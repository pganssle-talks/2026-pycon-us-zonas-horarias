#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "shapely>=2.0",
#     "requests",
# ]
# ///
"""
Generate time zone maps as SVG files.

Modes:
  current   UTC offset at the given date (default)
  standard  UTC offset minus DST (standard/winter time)
  dst       UTC offset during DST/summer time (searches ±6 months if not currently in DST)
"""

import argparse
import datetime
import json
import math
import os
import sys
import zipfile
import io
import zoneinfo
from collections import defaultdict, deque
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

import requests
import shapely
from shapely.affinity import translate
from shapely.geometry import shape, MultiPolygon, box
from shapely.ops import unary_union

# ── Constants ─────────────────────────────────────────────────────────────────

GEOJSON_URL = (
    "https://github.com/evansiroky/timezone-boundary-builder"
    "/releases/download/{version}/timezones.geojson.zip"
)
DEFAULT_VERSION = "2026a"

# 4-color NOAA-inspired pastel palette cycling by integer UTC offset
PALETTE = [
    "#EDD898",  # light cream/tan
    "#F0B898",  # light peach/salmon
    "#A0C8DC",  # light steel blue
    "#A8CCA0",  # light sage green
]

SVG_WIDTH = 1800
LAT_MIN, LAT_MAX = -60.0, 84.0
# Display range: shifted 7.5° east so -11 is the leftmost label and +12 wraps on the right.
# The 7.5° strip at [-180°, -172.5°] reappears on the right via antimeridian wrapping.
LON_MIN, LON_MAX = -172.5, 187.5
SVG_HEIGHT = round(SVG_WIDTH * (LAT_MAX - LAT_MIN) / (LON_MAX - LON_MIN))
LABEL_MARGIN = 22  # px above and below map for offset label bars
TOTAL_HEIGHT = SVG_HEIGHT + 2 * LABEL_MARGIN

LAND_OVERLAY_OPACITY = "0.12"  # dark overlay on land to make it slightly darker than ocean
TZ_FILL_OPACITY = "0.92"
BORDER_WIDTH = "1.8"  # TZ zone border width

# Geometry clip uses the full ±180° geographic range; display wraps via lx().
MAP_CLIP = box(-180.0, LAT_MIN, 180.0, LAT_MAX)

# ── Color helpers ─────────────────────────────────────────────────────────────

def _cidx(h: float) -> int:
    return (int(math.floor(h)) + 24) % 4

def fill_color(h: float) -> str:
    return PALETTE[_cidx(h)]

def hatch_colors(h: float) -> tuple[str, str]:
    return PALETTE[_cidx(math.floor(h))], PALETTE[_cidx(math.ceil(h))]

def is_frac(h: float) -> bool:
    return h % 1.0 != 0.0

def pat_id(h: float) -> str:
    s = "p" if h >= 0 else "n"
    return f"hatch_{s}{abs(h):.2f}".replace(".", "_")

def desaturate(hex_color: str, factor: float = 0.85) -> str:
    """Mix hex_color toward its luminance grey by factor (1.0 = full grey)."""
    r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
    lum = round(0.299 * r + 0.587 * g + 0.114 * b)
    r2 = round(r + (lum - r) * factor)
    g2 = round(g + (lum - g) * factor)
    b2 = round(b + (lum - b) * factor)
    return f"#{r2:02x}{g2:02x}{b2:02x}"

# ── Coordinate transforms ─────────────────────────────────────────────────────

def lx(lon: float) -> float:
    return (lon - LON_MIN) / (LON_MAX - LON_MIN) * SVG_WIDTH

def ly(lat: float) -> float:
    return LABEL_MARGIN + (LAT_MAX - lat) / (LAT_MAX - LAT_MIN) * SVG_HEIGHT

# ── Geometry utils ────────────────────────────────────────────────────────────

def area_km2(geom) -> float:
    """Estimate area using Shapely's planar area scaled by a latitude correction."""
    b = geom.bounds
    cy = (b[1] + b[3]) / 2
    return geom.area * 111.0 * 111.0 * math.cos(math.radians(cy))

def dist_km(a, b) -> float:
    """Approximate great-circle distance between representative points."""
    p1 = a.representative_point()
    p2 = b.representative_point()
    lat1, lon1 = math.radians(p1.y), math.radians(p1.x)
    lat2, lon2 = math.radians(p2.y), math.radians(p2.x)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    s = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(s))

def make_valid(geom):
    return shapely.make_valid(geom)

def safe_difference(a, b):
    """difference(a, b) with fallbacks for GEOS topology failures."""
    try:
        return a.difference(b)
    except Exception:
        pass
    try:
        return shapely.make_valid(a).difference(shapely.make_valid(b))
    except Exception:
        pass
    # Last resort: snap both to a coarse grid to resolve precision conflicts
    try:
        gs = 1e-7
        return shapely.set_precision(a, gs).difference(shapely.set_precision(b, gs))
    except Exception:
        return a

_DISPLAY_CLIP = box(LON_MIN, LAT_MIN, 180.0, LAT_MAX)
_OVERFLOW_CLIP = box(-180.0, LAT_MIN, LON_MIN, LAT_MAX)

def _wrap_for_display(geom):
    """Split geometry at LON_MIN; shift the [-180°, LON_MIN] strip by +360° to appear on the right."""
    if geom is None or geom.is_empty:
        return geom
    main = geom.intersection(_DISPLAY_CLIP)
    overflow = geom.intersection(_OVERFLOW_CLIP)
    if overflow.is_empty:
        return main
    overflow_shifted = translate(overflow, xoff=360.0)
    if main.is_empty:
        return overflow_shifted
    return shapely.make_valid(main.union(overflow_shifted))

def geom_to_svg_path(geom) -> str:
    if geom is None or geom.is_empty:
        return ""

    def ring(coords) -> str:
        parts = []
        for i, (lon, lat, *_) in enumerate(coords):
            parts.append(f"{'M' if i == 0 else 'L'}{lx(lon):.2f},{ly(lat):.2f}")
        parts.append("Z")
        return "".join(parts)

    if geom.geom_type == "Polygon":
        return ring(geom.exterior.coords) + "".join(ring(h.coords) for h in geom.interiors)
    if geom.geom_type in ("MultiPolygon", "GeometryCollection"):
        return "".join(geom_to_svg_path(g) for g in geom.geoms)
    return ""

# ── Small island handling ─────────────────────────────────────────────────────

def _bbox_for(poly, constraints: Sequence, margin_km: float, nearby_km: float):
    """Return a padded bounding box for a small polygon."""
    nearest = min((dist_km(poly, o) for o in constraints), default=float("inf"))
    m = min(margin_km, nearest / 2) if nearest < nearby_km else margin_km
    m_deg = m / 111.0
    b = poly.bounds
    return box(b[0] - m_deg, b[1] - m_deg, b[2] + m_deg, b[3] + m_deg)

def _replace_small_components(
    geom,
    other_zone_geoms: Sequence,
    threshold_km2: float,
    margin_km: float,
    nearby_km: float,
    simplify_tol: Optional[float],
):
    """Post-merge: simplify large components; replace small isolated ones with bboxes.

    Works on the already-merged geometry for one offset group so that adjacent
    same-timezone islands are treated as a unit before the area threshold is applied.
    """
    if geom is None or geom.is_empty:
        return geom

    if geom.geom_type == "Polygon":
        components = [geom]
    elif geom.geom_type in ("MultiPolygon", "GeometryCollection"):
        components = [g for g in geom.geoms if g.geom_type == "Polygon" and not g.is_empty]
    else:
        return geom

    large = [c for c in components if area_km2(c) >= threshold_km2]
    small = [c for c in components if area_km2(c) < threshold_km2]

    if not small:
        if simplify_tol:
            return geom.simplify(simplify_tol, preserve_topology=True)
        return geom

    # Distance constraints: large same-zone components + all other-zone geometries,
    # so boxes don't bleed into adjacent regions or the zone's own mainland.
    constraints = large + list(other_zone_geoms)

    result = []
    for c in large:
        result.append(c.simplify(simplify_tol, preserve_topology=True) if simplify_tol else c)
    # One collective bbox for all small components — avoids per-island boxes,
    # produces a single region (like NOAA's polygon treatment of island groups).
    # Guard: if components span the anti-meridian or a huge area, use individual bboxes.
    if small:
        collective = unary_union(small)
        cb = collective.bounds  # (minx, miny, maxx, maxy)
        if cb[2] - cb[0] > 25 or cb[3] - cb[1] > 20:
            for c in small:
                result.append(_bbox_for(c, constraints, margin_km, nearby_km))
        else:
            result.append(_bbox_for(collective, constraints, margin_km, nearby_km))

    return make_valid(unary_union(result))

def _process_group(
    h: float,
    geoms: Sequence,
    all_geoms: Sequence,
    threshold_km2: float,
    margin_km: float,
    nearby_km: float,
    simplify_tol: Optional[float],
) -> tuple[float, object, object]:
    """Union one offset group and return (offset, raw_merged, display_merged).

    raw_merged   – full-resolution union, used for the land layer
    display_merged – simplified timezone boundaries + bbox for small islands
    """
    geom_ids = {id(g) for g in geoms}
    others = [g for g in all_geoms if id(g) not in geom_ids]

    raw_merged = make_valid(unary_union(geoms)).intersection(MAP_CLIP)
    display = _replace_small_components(raw_merged, others, threshold_km2, margin_km, nearby_km, simplify_tol)
    return h, raw_merged, display

def _compute_ocean_band(i: int, land_union) -> tuple[float, object]:
    """Return the ocean portion of the idealized band for integer offset i."""
    band = MAP_CLIP.intersection(box(i * 15 - 7.5, LAT_MIN, i * 15 + 7.5, LAT_MAX))
    return float(i), safe_difference(band, land_union)

# ── Offset calculations ───────────────────────────────────────────────────────

def _utc(dt: datetime.datetime) -> datetime.datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=datetime.timezone.utc)
    return dt.astimezone(datetime.timezone.utc)

def current_offset(name: str, dt: datetime.datetime) -> Optional[float]:
    try:
        zi = zoneinfo.ZoneInfo(name)
        return _utc(dt).astimezone(zi).utcoffset().total_seconds() / 3600
    except Exception:
        return None

def standard_offset(name: str, dt: datetime.datetime) -> Optional[float]:
    try:
        zi = zoneinfo.ZoneInfo(name)
        local = _utc(dt).astimezone(zi)
        dst = local.dst() or datetime.timedelta(0)
        return (local.utcoffset() - dst).total_seconds() / 3600
    except Exception:
        return None

def _dst_day_offsets(max_days: float = 183.0, min_days: float = 7.0):
    """Yield day deltas in binary-subdivision order: +max, -max, +mid, -mid, ..."""
    yield max_days
    yield -max_days
    queue: deque[tuple[float, float]] = deque([(0.0, max_days)])
    while queue:
        lo, hi = queue.popleft()
        mid = (lo + hi) / 2
        if hi - lo < min_days:
            continue
        yield mid
        yield -mid
        queue.append((lo, mid))
        queue.append((mid, hi))

def dst_offset(name: str, dt: datetime.datetime) -> Optional[float]:
    """Return the DST (summer) UTC offset, searching ±6 months if not currently in DST."""
    try:
        zi = zoneinfo.ZoneInfo(name)
        utc_aware = _utc(dt)
        local = utc_aware.astimezone(zi)
        if (local.dst() or datetime.timedelta(0)).total_seconds() != 0:
            return local.utcoffset().total_seconds() / 3600
        for delta in _dst_day_offsets():
            check = (utc_aware + datetime.timedelta(days=delta)).astimezone(zi)
            if (check.dst() or datetime.timedelta(0)).total_seconds() != 0:
                return check.utcoffset().total_seconds() / 3600
        dst_now = local.dst() or datetime.timedelta(0)
        return (local.utcoffset() - dst_now).total_seconds() / 3600
    except Exception:
        return None

# ── GeoJSON ───────────────────────────────────────────────────────────────────

def load_features(cache_dir: Path, version: str) -> Sequence:
    combined = cache_dir / "combined.json"
    if not combined.exists():
        url = GEOJSON_URL.format(version=version)
        print(f"Downloading {url}...", file=sys.stderr)
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        cache_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            z.extractall(cache_dir)
    print("Loading GeoJSON...", file=sys.stderr)
    with open(combined, encoding="utf-8") as f:
        return json.load(f)["features"]

# ── SVG rendering ─────────────────────────────────────────────────────────────

def offset_label(h: float) -> str:
    whole = int(h)
    mins = round(abs(h - whole) * 60)
    sign = "+" if whole > 0 else ("-" if whole < 0 else "")
    if mins:
        return f"{sign}{abs(whole)}:{mins:02d}"
    return f"{sign}{abs(whole)}" if whole else "0"

def frac_label(h: float) -> str:
    """Format fractional UTC offset with Unicode fraction symbols: +3½, -9½, +5¾"""
    sign = "+" if h > 0 else ("-" if h < 0 else "")
    whole = abs(int(h))  # truncation toward zero
    frac = round(abs(h) % 1.0, 10)
    sym = {0.5: "½", 0.75: "¾", 0.25: "¼"}.get(frac, f":{round(frac * 60):02d}")
    return f"{sign}{whole}{sym}"

def render(
    offset_map: Mapping,
    land_geom,
    out: Path,
    highlight_non_integer: bool = False,
) -> None:
    offsets = sorted(offset_map)

    lines: MutableSequence[str] = [
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"',
        f'  width="{SVG_WIDTH}" height="{TOTAL_HEIGHT}" viewBox="0 0 {SVG_WIDTH} {TOTAL_HEIGHT}">',
        "<defs>",
    ]
    for h in offsets:
        if is_frac(h):
            pid = pat_id(h)
            c1, c2 = hatch_colors(h)
            sw = 6
            lines.append(
                f'<pattern id="{pid}" patternUnits="userSpaceOnUse"'
                f' width="{sw*2}" height="{sw*2}" patternTransform="rotate(45)">'
                f'<rect x="0" y="0" width="{sw}" height="{sw*2}" fill="{c1}"/>'
                f'<rect x="{sw}" y="0" width="{sw}" height="{sw*2}" fill="{c2}"/>'
                f'</pattern>'
            )

    map_top = LABEL_MARGIN
    map_bot = LABEL_MARGIN + SVG_HEIGHT
    idl_x = lx(180.0)

    # Clip path so zone fill strokes don't bleed into the label bars
    lines.append(
        f'<clipPath id="mapclip">'
        f'<rect x="0" y="{map_top}" width="{SVG_WIDTH}" height="{SVG_HEIGHT}"/>'
        f'</clipPath>'
    )
    lines.append("</defs>")

    # White background
    lines.append(f'<rect width="{SVG_WIDTH}" height="{TOTAL_HEIGHT}" fill="white"/>')

    # All map content is clipped to the map viewport
    lines.append('<g clip-path="url(#mapclip)">')

    # TZ zone fills — solid zone colors for land AND ocean alike.
    for h in offsets:
        geom = _wrap_for_display(offset_map[h])
        d = geom_to_svg_path(geom)
        if not d:
            continue
        if is_frac(h):
            f = f"url(#{pat_id(h)})"
        elif highlight_non_integer:
            f = desaturate(fill_color(h))
        else:
            f = fill_color(h)
        lines.append(
            f'<path d="{d}" fill="{f}" fill-opacity="{TZ_FILL_OPACITY}"'
            f' stroke="#334" stroke-width="{BORDER_WIDTH}" stroke-linejoin="round"/>'
        )

    # Dark land overlay — makes land slightly darker than ocean in the same zone.
    if land_geom and not land_geom.is_empty:
        d = geom_to_svg_path(_wrap_for_display(land_geom))
        if d:
            lines.append(f'<path d="{d}" fill="#000" fill-opacity="{LAND_OVERLAY_OPACITY}" stroke="none"/>')

    # Labels for fractional zones placed at their representative point inside the map
    for h in offsets:
        if not is_frac(h):
            continue
        geom = _wrap_for_display(offset_map[h])
        if geom is None or geom.is_empty:
            continue
        pt = geom.representative_point()
        px, py = lx(pt.x), ly(pt.y)
        if not (0 <= px <= SVG_WIDTH and map_top <= py <= map_bot):
            continue
        bbox = geom.bounds
        bbox_px_width = lx(min(bbox[2], LON_MAX)) - lx(max(bbox[0], LON_MIN))
        font_size = max(7, min(13, int(bbox_px_width / 5)))
        lbl = frac_label(h)
        lines.append(
            f'<text x="{px:.1f}" y="{py:.1f}"'
            f' font-family="sans-serif" font-size="{font_size}"'
            f' font-weight="bold" fill="#222" text-anchor="middle"'
            f' dominant-baseline="middle" opacity="0.8">{lbl}</text>'
        )

    lines.append("</g>")

    # Colored label bars drawn outside the clip so they are always fully visible.
    # +12 bar is capped at the IDL; a separate -12 bar fills the right sliver.
    for i in range(-11, 13):
        x1 = max(0.0, lx(i * 15 - 7.5))
        x2 = idl_x if i == 12 else min(float(SVG_WIDTH), lx(i * 15 + 7.5))
        if x2 <= x1:
            continue
        col = fill_color(float(i)) if not highlight_non_integer else desaturate(fill_color(float(i)))
        lines.append(f'<rect x="{x1:.1f}" y="0" width="{x2 - x1:.1f}" height="{LABEL_MARGIN}" fill="{col}"/>')
        lines.append(f'<rect x="{x1:.1f}" y="{map_bot}" width="{x2 - x1:.1f}" height="{LABEL_MARGIN}" fill="{col}"/>')

    m12_x1, m12_x2 = idl_x, float(SVG_WIDTH)
    if m12_x2 > m12_x1:
        col_m12 = fill_color(-12.0) if not highlight_non_integer else desaturate(fill_color(-12.0))
        lines.append(f'<rect x="{m12_x1:.1f}" y="0" width="{m12_x2 - m12_x1:.1f}" height="{LABEL_MARGIN}" fill="{col_m12}"/>')
        lines.append(f'<rect x="{m12_x1:.1f}" y="{map_bot}" width="{m12_x2 - m12_x1:.1f}" height="{LABEL_MARGIN}" fill="{col_m12}"/>')

    # Outer map border drawn over label bars for a clean edge
    lines.append(
        f'<rect x="0" y="{map_top}" width="{SVG_WIDTH}" height="{SVG_HEIGHT}"'
        f' fill="none" stroke="#334" stroke-width="1.5"/>'
    )

    # Offset labels centered in label bars
    ty_top = LABEL_MARGIN // 2 + 5
    ty_bot = map_bot + LABEL_MARGIN // 2 + 5
    for i in range(-11, 13):
        x1 = max(0.0, lx(i * 15 - 7.5))
        x2 = idl_x if i == 12 else min(float(SVG_WIDTH), lx(i * 15 + 7.5))
        if x2 <= x1:
            continue
        cx = (x1 + x2) / 2
        lbl = offset_label(float(i))
        lines.append(
            f'<text x="{cx:.1f}" y="{ty_top}"'
            f' font-family="sans-serif" font-size="10" font-weight="bold" fill="#222"'
            f' text-anchor="middle">{lbl}</text>'
        )
        lines.append(
            f'<text x="{cx:.1f}" y="{ty_bot}"'
            f' font-family="sans-serif" font-size="10" font-weight="bold" fill="#222"'
            f' text-anchor="middle">{lbl}</text>'
        )

    if m12_x2 > m12_x1:
        cx_m12 = (m12_x1 + m12_x2) / 2
        lines.append(
            f'<text x="{cx_m12:.1f}" y="{ty_top}"'
            f' font-family="sans-serif" font-size="10" font-weight="bold" fill="#222"'
            f' text-anchor="middle">-12</text>'
        )
        lines.append(
            f'<text x="{cx_m12:.1f}" y="{ty_bot}"'
            f' font-family="sans-serif" font-size="10" font-weight="bold" fill="#222"'
            f' text-anchor="middle">-12</text>'
        )

    # International Date Line label (vertical, just left of IDL)
    idl_label_x = idl_x - 4
    idl_label_y = (ly(LAT_MIN) + ly(LAT_MAX)) / 2
    lines.append(
        f'<text x="{idl_label_x:.1f}" y="{idl_label_y:.1f}"'
        f' transform="rotate(-90,{idl_label_x:.1f},{idl_label_y:.1f})"'
        f' font-family="sans-serif" font-size="9" fill="#445" opacity="0.6"'
        f' text-anchor="middle">International Date Line</text>'
    )

    lines.append("</svg>")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Written: {out}", file=sys.stderr)

# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "output_dir", nargs="?", default=None,
        help="Output directory (default: directory of this script)",
    )
    p.add_argument(
        "--date", default=None, metavar="YYYY-MM-DD",
        help="Reference date in UTC (default: today)",
    )
    p.add_argument(
        "--mode", choices=["current", "standard", "dst"], default="current",
        help="Offset mode (default: current)",
    )
    p.add_argument(
        "--version", default=DEFAULT_VERSION, dest="tz_version", metavar="VER",
        help=f"timezone-boundary-builder release version (default: {DEFAULT_VERSION})",
    )
    p.add_argument(
        "--cache-dir", default=None, metavar="DIR",
        help="Directory holding cached combined.json "
             "(default: ../../tmp_geojson relative to this script)",
    )
    p.add_argument(
        "--small-threshold-km2", type=float, default=5000.0, metavar="KM2",
        help="Disconnected components smaller than this area get a bounding box (default: 5000)",
    )
    p.add_argument(
        "--island-margin-km", type=float, default=100.0, metavar="KM",
        help="Bounding box margin for small islands in km (default: 100)",
    )
    p.add_argument(
        "--nearby-km", type=float, default=200.0, metavar="KM",
        help="If nearest other region is closer than this, use half that as margin (default: 200)",
    )
    p.add_argument(
        "--simplify", type=float, default=0.05, metavar="DEG",
        help="Geometry simplification tolerance in degrees (default: 0.05 ≈ 5 km)",
    )
    p.add_argument(
        "--no-simplify", action="store_true",
        help="Disable geometry simplification",
    )
    p.add_argument(
        "--ideal", action="store_true",
        help="Use only idealized longitude bands (ignore geojson zone data)",
    )
    p.add_argument(
        "--highlight-non-integer", action="store_true", dest="highlight_non_integer",
        help="Desaturate integer-offset zones so fractional offsets stand out",
    )
    args = p.parse_args()

    script_dir = Path(__file__).resolve().parent
    out_dir = Path(args.output_dir) if args.output_dir else script_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    dt: datetime.datetime
    if args.date:
        dt = datetime.datetime.fromisoformat(args.date)
    else:
        dt = datetime.datetime.now(datetime.timezone.utc)

    cache_dir = (
        Path(args.cache_dir) if args.cache_dir
        else script_dir.parent.parent / "tmp_geojson"
    )

    date_sfx = (dt if dt.tzinfo is None else dt.astimezone(datetime.timezone.utc)).strftime(
        "%Y%m%d"
    )
    highlight_sfx = "_highlight" if args.highlight_non_integer else ""

    if args.ideal:
        features = load_features(cache_dir, args.tz_version)
        print("Building idealized longitude bands and land silhouette...", file=sys.stderr)
        workers = os.cpu_count() or 1
        with ThreadPoolExecutor(max_workers=workers) as pool:
            all_geoms = list(pool.map(
                lambda feat: make_valid(shape(feat["geometry"])), features
            ))
        land_union = shapely.make_valid(
            unary_union(all_geoms).intersection(MAP_CLIP)
        )
        offset_map: MutableMapping[float, object] = {}
        for i in range(-12, 15):
            band = MAP_CLIP.intersection(box(i * 15 - 7.5, LAT_MIN, i * 15 + 7.5, LAT_MAX))
            if not band.is_empty:
                offset_map[float(i)] = band
        out_path = out_dir / f"tz_map_ideal_{date_sfx}{highlight_sfx}.svg"
        print("Rendering SVG...", file=sys.stderr)
        render(offset_map, land_union, out_path, highlight_non_integer=args.highlight_non_integer)
        return

    features = load_features(cache_dir, args.tz_version)

    get_off = {"current": current_offset, "standard": standard_offset, "dst": dst_offset}[
        args.mode
    ]
    simplify_tol = None if args.no_simplify else args.simplify
    workers = os.cpu_count() or 1

    # Phase 1 — compute offset + load/validate geometry for every feature in parallel.
    # DST mode can do 100+ zoneinfo lookups per zone; this is the dominant cost there.
    def _process_feature(feat: Mapping) -> Optional[tuple[float, object]]:
        name = feat["properties"]["tzid"]
        h = get_off(name, dt)
        if h is None:
            return None
        return h, make_valid(shape(feat["geometry"]))

    print("Computing offsets and loading geometries...", file=sys.stderr)
    groups: MutableMapping[float, MutableSequence] = defaultdict(list)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for result in pool.map(_process_feature, features):
            if result is not None:
                h, g = result
                groups[h].append(g)

    # Phase 2 — expand small islands, union, clip, simplify — one task per offset group.
    # Each group is independent; GEOS ops release the GIL so threads run truly in parallel.
    all_geoms_flat = [g for gs in groups.values() for g in gs]

    # Phase 2 — per-offset group: returns (h, raw_full_res, display_simplified+boxed).
    # Raw geometries feed the land layer; display geometries feed the TZ color overlay.
    print("Expanding small islands and merging by offset...", file=sys.stderr)
    actual_offset_map: MutableMapping[float, object] = {}
    raw_offset_map: MutableMapping[float, object] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(
                _process_group,
                h, geoms, all_geoms_flat,
                args.small_threshold_km2, args.island_margin_km,
                args.nearby_km, simplify_tol,
            ): h
            for h, geoms in groups.items()
        }
        for fut in as_completed(futures):
            h, raw_merged, display_merged = fut.result()
            raw_offset_map[h] = raw_merged
            actual_offset_map[h] = display_merged

    # Raw land union (from unsimplified geometries) is used only for the dark land overlay.
    # Display land union (from simplified+boxed geometries) is used for ocean band subtraction
    # so that the ocean fill matches the displayed TZ fill without seams at coastlines.
    print("Computing land/defined-area union...", file=sys.stderr)
    land_union = shapely.make_valid(
        unary_union(list(raw_offset_map.values())).intersection(MAP_CLIP)
    )
    display_land_union = shapely.make_valid(
        unary_union(list(actual_offset_map.values())).intersection(MAP_CLIP)
    )

    # Phase 3 — compute ocean fills for all 27 integer bands in parallel, then merge.
    print("Merging idealized ocean bands...", file=sys.stderr)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        band_results = list(pool.map(
            lambda i: _compute_ocean_band(i, display_land_union),
            range(-12, 15),
        ))
    offset_map = dict(actual_offset_map)
    for h, ocean_fill in band_results:
        if ocean_fill.is_empty:
            continue
        if h in offset_map:
            offset_map[h] = offset_map[h].union(ocean_fill)
        else:
            offset_map[h] = ocean_fill

    mode_sfx = {"current": "", "standard": "_standard", "dst": "_dst"}[args.mode]
    out_path = out_dir / f"tz_map{mode_sfx}_{date_sfx}{highlight_sfx}.svg"

    print("Rendering SVG...", file=sys.stderr)
    render(offset_map, land_union, out_path, highlight_non_integer=args.highlight_non_integer)


if __name__ == "__main__":
    main()
