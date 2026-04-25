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
import sys
import zipfile
import io
import zoneinfo
from collections import defaultdict, deque
from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path
from typing import Optional

import requests
import shapely
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
    "#F5E8B0",  # warm yellow
    "#F0B090",  # salmon
    "#90B8D0",  # steel blue
    "#A8C8A0",  # sage green
]

SVG_WIDTH = 1800
LAT_MIN, LAT_MAX = -60.0, 84.0
LON_MIN, LON_MAX = -180.0, 180.0
SVG_HEIGHT = round(SVG_WIDTH * (LAT_MAX - LAT_MIN) / (LON_MAX - LON_MIN))
LABEL_MARGIN = 22  # px above/below for offset labels
TOTAL_HEIGHT = SVG_HEIGHT + 2 * LABEL_MARGIN

LAND_COLOR = "#333333"   # 20% grey; shows slightly darker through the semi-opaque TZ layer
TZ_FILL_OPACITY = "0.5"  # TZ fill opacity; stroke stays full so borders are bold
BORDER_WIDTH = "1.5"

MAP_CLIP = box(LON_MIN, LAT_MIN, LON_MAX, LAT_MAX)

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
    """Estimate area via the circumscribed circle of the bounding box."""
    b = geom.bounds  # (minx, miny, maxx, maxy)
    cy = (b[1] + b[3]) / 2
    w_km = (b[2] - b[0]) * 111.0 * math.cos(math.radians(cy))
    h_km = (b[3] - b[1]) * 111.0
    r_km = math.sqrt((w_km / 2) ** 2 + (h_km / 2) ** 2)
    return math.pi * r_km ** 2

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

def expand_small_polys(
    geom,
    others: Sequence,
    threshold_km2: float,
    margin_km: float,
    nearby_km: float,
):
    """Replace sub-threshold individual polygons with buffered bounding boxes."""
    if geom is None or geom.is_empty:
        return geom
    if geom.geom_type == "Polygon":
        polys = [geom]
    elif geom.geom_type == "MultiPolygon":
        polys = list(geom.geoms)
    else:
        return geom

    result = []
    for poly in polys:
        if area_km2(poly) < threshold_km2:
            nearest = min((dist_km(poly, o) for o in others), default=float("inf"))
            m = min(margin_km, nearest / 2) if nearest < nearby_km else margin_km
            m_deg = m / 111.0  # approximate: 1° ≈ 111 km
            b = poly.bounds
            result.append(box(b[0] - m_deg, b[1] - m_deg, b[2] + m_deg, b[3] + m_deg))
        else:
            result.append(poly)

    return result[0] if len(result) == 1 else MultiPolygon(result)

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
    lines.append("</defs>")

    # White background (represents open ocean with no idealized fill — shouldn't be visible)
    lines.append(f'<rect width="{SVG_WIDTH}" height="{TOTAL_HEIGHT}" fill="white"/>')

    # Land masses in 20% grey — blends with TZ color at fill-opacity above
    if land_geom and not land_geom.is_empty:
        d = geom_to_svg_path(land_geom)
        if d:
            lines.append(f'<path d="{d}" fill="{LAND_COLOR}" stroke="none"/>')

    # TZ zones — each covers its actual geojson polygon(s) PLUS the idealized band ocean fill.
    # fill-opacity leaves the stroke at 100% so offset borders are clearly visible.
    # In highlight_non_integer mode, integer zones are desaturated so fractional ones pop.
    for h in offsets:
        geom = offset_map[h]
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
            f' stroke="#556" stroke-width="{BORDER_WIDTH}" stroke-linejoin="round"/>'
        )

    # Map border
    lines.append(
        f'<rect x="0" y="{LABEL_MARGIN}" width="{SVG_WIDTH}" height="{SVG_HEIGHT}"'
        f' fill="none" stroke="#445" stroke-width="1"/>'
    )

    # International Date Line label (vertical, near right edge)
    idl_x = lx(180.0) - 4
    idl_y = (ly(LAT_MIN) + ly(LAT_MAX)) / 2
    lines.append(
        f'<text x="{idl_x:.1f}" y="{idl_y:.1f}"'
        f' transform="rotate(-90,{idl_x:.1f},{idl_y:.1f})"'
        f' font-family="sans-serif" font-size="9" fill="#445" opacity="0.6"'
        f' text-anchor="middle">International Date Line</text>'
    )

    # Offset labels top and bottom
    for h in offsets:
        lon_c = h * 15
        if not (LON_MIN <= lon_c <= LON_MAX):
            continue
        x = lx(lon_c)
        lbl = offset_label(h)
        fs = 8 if is_frac(h) else 10
        lines.append(
            f'<text x="{x:.1f}" y="{LABEL_MARGIN - 5}"'
            f' font-family="sans-serif" font-size="{fs}" fill="#333"'
            f' text-anchor="middle">{lbl}</text>'
        )
        lines.append(
            f'<text x="{x:.1f}" y="{TOTAL_HEIGHT - 4}"'
            f' font-family="sans-serif" font-size="{fs}" fill="#333"'
            f' text-anchor="middle">{lbl}</text>'
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
        "--small-threshold-km2", type=float, default=100.0, metavar="KM2",
        help="Islands smaller than this area get a bounding box (default: 100)",
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
        print("Building idealized longitude bands...", file=sys.stderr)
        offset_map: MutableMapping[float, object] = {}
        for i in range(-12, 15):
            band = MAP_CLIP.intersection(box(i * 15 - 7.5, LAT_MIN, i * 15 + 7.5, LAT_MAX))
            if not band.is_empty:
                offset_map[float(i)] = band
        out_path = out_dir / f"tz_map_ideal_{date_sfx}{highlight_sfx}.svg"
        print("Rendering SVG...", file=sys.stderr)
        render(offset_map, None, out_path, highlight_non_integer=args.highlight_non_integer)
        return

    features = load_features(cache_dir, args.tz_version)

    get_off = {"current": current_offset, "standard": standard_offset, "dst": dst_offset}[
        args.mode
    ]

    print("Computing offsets...", file=sys.stderr)
    zone_offset: MutableMapping[str, float] = {}
    for feat in features:
        name = feat["properties"]["tzid"]
        h = get_off(name, dt)
        if h is not None:
            zone_offset[name] = h

    # Group raw geometries by offset
    print("Grouping geometries...", file=sys.stderr)
    groups: MutableMapping[float, MutableSequence] = defaultdict(list)
    for feat in features:
        name = feat["properties"]["tzid"]
        if name not in zone_offset:
            continue
        g = make_valid(shape(feat["geometry"]))
        groups[zone_offset[name]].append(g)

    simplify_tol = None if args.no_simplify else args.simplify

    print("Expanding small islands and merging by offset...", file=sys.stderr)
    actual_offset_map: MutableMapping[float, object] = {}
    for h, geoms in groups.items():
        others = [g for oh, gs in groups.items() for g in gs if oh != h]
        processed = [
            expand_small_polys(
                g, others,
                args.small_threshold_km2,
                args.island_margin_km,
                args.nearby_km,
            )
            for g in geoms
        ]
        merged = unary_union(processed)
        merged = merged.intersection(MAP_CLIP)
        if simplify_tol:
            merged = merged.simplify(simplify_tol, preserve_topology=True)
        actual_offset_map[h] = merged

    # Union of all defined zones — used as the land layer and as the mask for idealized fills
    print("Computing land/defined-area union...", file=sys.stderr)
    land_union = shapely.make_valid(
        unary_union(list(actual_offset_map.values())).intersection(MAP_CLIP)
    )

    # For each integer offset, fill the undefined ocean within its idealized band and merge
    # into the corresponding actual zone (creating it if no real zone has that offset).
    print("Merging idealized ocean bands...", file=sys.stderr)
    offset_map = dict(actual_offset_map)
    for i in range(-12, 15):
        band = MAP_CLIP.intersection(box(i * 15 - 7.5, LAT_MIN, i * 15 + 7.5, LAT_MAX))
        ocean_fill = safe_difference(band, land_union)
        if ocean_fill.is_empty:
            continue
        h = float(i)
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
