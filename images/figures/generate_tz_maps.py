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
import colorsys
import datetime
import gzip
import json
import math
import os
import subprocess
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

# ── Styling ───────────────────────────────────────────────────────────────────

STYLE = {
    "land": {
        "fill": "#ccc",
        "fill-opacity": "1",
        "stroke": "#333",
        "stroke-width": "0.5",
        "stroke-dasharray": "none",
    },
    "zone_band": {
        "fill-opacity": "0.62",
        "stroke": "#334",
        "stroke-width": "1.8",
        "stroke-linejoin": "round",
    },
    "map_border": {
        "stroke": "#334",
        "stroke-width": "1.5",
    },
    "label": {
        "font-family": "Futura,sans-serif",
        "font-weight": "bold",
        "fill": "#222",
        "opacity": "0.8",
        "size_top_bot": 10,
        "size_frac_min": 7,
        "size_frac_max": 13,
    },
    "idl": {
        "font-family": "sans-serif",
        "font-size": "9",
        "fill": "#445",
        "opacity": "0.6",
    },
}

# 4-color NOAA-inspired pastel palette cycling by integer UTC offset
PALETTE = [
    "#A8CCA0",  # light sage green
    "#EDD898",  # light cream/tan
    "#F0B898",  # light peach/salmon
    "#A0C8DC",  # light steel blue
]

LAT_MIN, LAT_MAX = -60.0, 84.0
# Display range: shifted 7.5° east so -11 is the leftmost label and +12 wraps on the right.
# The 7.5° strip at [-180°, -172.5°] reappears on the right via antimeridian wrapping.
LON_MIN, LON_MAX = -172.5, 187.5

# Geometry clip uses the full ±180° geographic range; display wraps via lx().
MAP_CLIP = box(-180.0, LAT_MIN, 180.0, LAT_MAX)

_HOUR: datetime.timedelta = datetime.timedelta(hours=1)
_ZERO_TD: datetime.timedelta = datetime.timedelta(0)

_DISPLAY_CLIP = box(LON_MIN, -90.0, 180.0, 90.0)
_OVERFLOW_CLIP = box(-180.0, -90.0, LON_MIN, 90.0)

# ── Color helpers ─────────────────────────────────────────────────────────────

def _cidx(h: float) -> int:
    return (int(math.floor(h)) + 24) % 4

def adjust_color(hex_color: str, sat_factor: float = 1.0, lum_factor: float = 1.0) -> str:
    """Adjust saturation and luminance of a hex color."""
    r, g, b = int(hex_color[1:3], 16) / 255.0, int(hex_color[3:5], 16) / 255.0, int(hex_color[5:7], 16) / 255.0
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    s = min(1.0, s * sat_factor)
    l = min(1.0, l * lum_factor)
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return f"#{round(r*255):02x}{round(g*255):02x}{round(b*255):02x}"

def fill_color(h: float) -> str:
    return PALETTE[_cidx(h)]

def hatch_colors(h: float, vivid: bool = False) -> tuple[str, str]:
    c1, c2 = PALETTE[_cidx(math.floor(h))], PALETTE[_cidx(math.ceil(h))]
    if vivid:
        return adjust_color(c1, 3.0, 0.9), adjust_color(c2, 3.0, 0.9)
    return c1, c2

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

def lx(lon: float, width: float) -> float:
    return (lon - LON_MIN) / (LON_MAX - LON_MIN) * width

def ly(lat: float, map_height: float, margin: float = 0.0) -> float:
    return margin + (LAT_MAX - lat) / (LAT_MAX - LAT_MIN) * map_height

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

_DISPLAY_CLIP = box(LON_MIN, -90.0, 180.0, 90.0)
_OVERFLOW_CLIP = box(-180.0, -90.0, LON_MIN, 90.0)

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

def geom_to_svg_path(geom, width: float, map_height: float, margin: float) -> str:
    if geom is None or geom.is_empty:
        return ""

    def ring(coords) -> str:
        parts = []
        for i, (lon, lat, *_) in enumerate(coords):
            parts.append(f"{'M' if i == 0 else 'L'}{lx(lon, width):.2f},{ly(lat, map_height, margin):.2f}")
        parts.append("Z")
        return "".join(parts)

    if geom.geom_type == "Polygon":
        return ring(geom.exterior.coords) + "".join(ring(h.coords) for h in geom.interiors)
    if geom.geom_type in ("MultiPolygon", "GeometryCollection"):
        return "".join(geom_to_svg_path(g, width, map_height, margin) for g in geom.geoms)
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

def _compute_ocean_band(i: int, land_union, clip_box) -> tuple[float, object]:
    """Return the ocean portion of the idealized band for integer offset i."""
    band = clip_box.intersection(box(i * 15 - 7.5, -90, i * 15 + 7.5, 90))
    return float(i), safe_difference(band, land_union)

# ── Offset calculations ───────────────────────────────────────────────────────

def current_offset(zi: zoneinfo.ZoneInfo, dt: datetime.datetime) -> float | None:
    return zi.utcoffset(dt) / _HOUR

def standard_offset(zi: zoneinfo.ZoneInfo, dt: datetime.datetime) -> Optional[float]:
    local = dt.astimezone(zi)
    dst = local.dst() or _ZERO_TD
    return (local.utcoffset() - dst) / _HOUR

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

def dst_offset(zi: zoneinfo.ZoneInfo, dt: datetime.datetime) -> Optional[float]:
    """Return the DST (summer) UTC offset, searching ±6 months if not currently in DST."""
    local = dt.astimezone(zi)
    if (local.dst() or datetime.timedelta(0)) != _ZERO_TD:
        return local.utcoffset() / _HOUR
    for delta in _dst_day_offsets():
        check = dt + datetime.timedelta(days=delta)
        if (check.dst() or datetime.timedelta(0)) != _ZERO_TD:
            return check.utcoffset() / _HOUR
    dst_now = local.dst() or datetime.timedelta(0)
    return (local.utcoffset() - dst_now) / _HOUR

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

def _get_tzdata_version() -> str:
    """Attempt to detect the version of tzdata being used by zoneinfo."""
    try:
        import tzdata
        return tzdata.__version__
    except ImportError:
        pass
    for p in ["/usr/share/zoneinfo/tzdata.zi", "/var/db/zoneinfo/tzdata.zi"]:
        path = Path(p)
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    first_line = f.readline()
                    if first_line.startswith("# version "):
                        return first_line.split()[-1]
            except Exception:
                pass
    return "unknown"

def render(
    offset_map: Mapping,
    land_geom,
    out: Path,
    width: float,
    total_height: float,
    map_height: float,
    margin: float,
    metadata: Optional[Mapping] = None,
    highlight_non_integer: bool = False,
) -> None:
    offsets = sorted(offset_map)
    z_sty = STYLE["zone_band"]
    l_sty = STYLE["land"]
    b_sty = STYLE["map_border"]
    txt_sty = STYLE["label"]
    idl_sty = STYLE["idl"]

    lines: MutableSequence[str] = [
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"',
        f'  width="{width}" height="{total_height}" viewBox="0 0 {width} {total_height}">',
    ]

    if metadata:
        lines.append("  <desc>")
        for k, v in metadata.items():
            lines.append(f"    {k}: {v}")
        lines.append("  </desc>")

    lines.append("<defs>")
    for h in offsets:
        if is_frac(h):
            pid = pat_id(h)
            c1, c2 = hatch_colors(h, vivid=highlight_non_integer)
            sw = 6
            lines.append(
                f'<pattern id="{pid}" patternUnits="userSpaceOnUse"'
                f' width="{sw*2}" height="{sw*2}" patternTransform="rotate(45)">'
                f'<rect x="0" y="0" width="{sw}" height="{sw*2}" fill="{c1}"/>'
                f'<rect x="{sw}" y="0" width="{sw}" height="{sw*2}" fill="{c2}"/>'
                f'</pattern>'
            )

    map_top = margin
    map_bot = margin + map_height
    idl_x = lx(180.0, width)

    # Clip path so zone fill strokes don't bleed into the label bars
    lines.append(
        f'<clipPath id="mapclip">'
        f'<rect x="0" y="{map_top}" width="{width}" height="{map_height}"/>'
        f'</clipPath>'
    )
    lines.append("</defs>")

    # White background
    lines.append(f'<rect width="{width}" height="{total_height}" fill="white"/>')

    # Dark land overlay — moved here to be below other layers.
    # It makes land slightly darker than ocean by darkening the background before colors are applied.
    if land_geom and not land_geom.is_empty:
        d = geom_to_svg_path(_wrap_for_display(land_geom), width, map_height, margin)
        if d:
            lines.append('<g clip-path="url(#mapclip)">')
            lines.append(
                f'<path d="{d}" fill="{l_sty["fill"]}" fill-opacity="{l_sty["fill-opacity"]}"'
                f' stroke="{l_sty["stroke"]}" stroke-width="{l_sty["stroke-width"]}"'
                f' stroke-dasharray="{l_sty["stroke-dasharray"]}"/>'
            )
            lines.append('</g>')

    # Background TZ zone fills (including ocean bands) — these extend from edge to edge
    for h in offsets:
        geom = _wrap_for_display(offset_map[h])
        d = geom_to_svg_path(geom, width, map_height, margin)
        if not d:
            continue
        if is_frac(h):
            f = f"url(#{pat_id(h)})"
        elif highlight_non_integer:
            f = desaturate(fill_color(h), factor=0.92)
        else:
            f = fill_color(h)
        lines.append(
            f'<path d="{d}" fill="{f}" fill-opacity="{z_sty["fill-opacity"]}"'
            f' stroke="{z_sty["stroke"]}" stroke-width="{z_sty["stroke-width"]}"'
            f' stroke-linejoin="{z_sty["stroke-linejoin"]}"/>'
        )

    # All map-specific overlays (fractional labels) are clipped to the map viewport
    lines.append('<g clip-path="url(#mapclip)">')

    # Labels for fractional zones placed at their representative point inside the map
    for h in offsets:
        if not is_frac(h):
            continue
        geom = _wrap_for_display(offset_map[h])
        if geom is None or geom.is_empty:
            continue
        pt = geom.representative_point()
        px, py = lx(pt.x, width), ly(pt.y, map_height, margin)
        if not (0 <= px <= width and margin <= py <= map_bot):
            continue
        bbox = geom.bounds
        bbox_px_width = lx(min(bbox[2], LON_MAX), width) - lx(max(bbox[0], LON_MIN), width)
        font_size = max(txt_sty["size_frac_min"], min(txt_sty["size_frac_max"], int(bbox_px_width / 5)))
        lbl = frac_label(h)
        lines.append(
            f'<text x="{px:.1f}" y="{py:.1f}"'
            f' font-family="{txt_sty["font-family"]}" font-size="{font_size}"'
            f' font-weight="{txt_sty["font-weight"]}" fill="{txt_sty["fill"]}" text-anchor="middle"'
            f' dominant-baseline="middle" opacity="{txt_sty["opacity"]}">{lbl}</text>'
        )

    lines.append("</g>")

    # Outer map border (Sides ONLY - top and bottom are open for bands to flow through)
    lines.append(
        f'<path d="M0,{margin} L0,{map_bot} M{width},{map_bot} L{width},{margin}"'
        f' fill="none" stroke="{b_sty["stroke"]}" stroke-width="{b_sty["stroke-width"]}"/>'
    )

    # Offset labels centered in the padding areas (directly on background bands)
    ty_top = margin / 2 + 5
    ty_bot = map_bot + margin / 2 + 5
    m12_x1, m12_x2 = idl_x, float(width)

    for i in range(-11, 13):
        x1 = max(0.0, lx(i * 15 - 7.5, width))
        x2 = idl_x if i == 12 else min(float(width), lx(i * 15 + 7.5, width))
        if x2 <= x1:
            continue
        cx = (x1 + x2) / 2
        lbl = offset_label(float(i))
        lines.append(
            f'<text x="{cx:.1f}" y="{ty_top}"'
            f' font-family="{txt_sty["font-family"]}" font-size="{txt_sty["size_top_bot"]}"'
            f' font-weight="{txt_sty["font-weight"]}" fill="{txt_sty["fill"]}"'
            f' opacity="{txt_sty["opacity"]}" text-anchor="middle">{lbl}</text>'
        )
        lines.append(
            f'<text x="{cx:.1f}" y="{ty_bot}"'
            f' font-family="{txt_sty["font-family"]}" font-size="{txt_sty["size_top_bot"]}"'
            f' font-weight="{txt_sty["font-weight"]}" fill="{txt_sty["fill"]}"'
            f' opacity="{txt_sty["opacity"]}" text-anchor="middle">{lbl}</text>'
        )

    if m12_x2 > m12_x1:
        cx_m12 = (m12_x1 + m12_x2) / 2
        lines.append(
            f'<text x="{cx_m12:.1f}" y="{ty_top}"'
            f' font-family="{txt_sty["font-family"]}" font-size="{txt_sty["size_top_bot"]}"'
            f' font-weight="{txt_sty["font-weight"]}" fill="{txt_sty["fill"]}"'
            f' opacity="{txt_sty["opacity"]}" text-anchor="middle">-12</text>'
        )
        lines.append(
            f'<text x="{cx_m12:.1f}" y="{ty_bot}"'
            f' font-family="{txt_sty["font-family"]}" font-size="{txt_sty["size_top_bot"]}"'
            f' font-weight="{txt_sty["font-weight"]}" fill="{txt_sty["fill"]}"'
            f' opacity="{txt_sty["opacity"]}" text-anchor="middle">-12</text>'
        )

    # International Date Line label (vertical)
    idl_label_x = idl_x - 4
    idl_label_y = margin + map_height / 2
    lines.append(
        f'<text x="{idl_label_x:.1f}" y="{idl_label_y:.1f}"'
        f' transform="rotate(-90,{idl_label_x:.1f},{idl_label_y:.1f})"'
        f' font-family="{idl_sty["font-family"]}" font-size="{idl_sty["font-size"]}"'
        f' fill="{idl_sty["fill"]}" opacity="{idl_sty["opacity"]}"'
        f' text-anchor="middle">International Date Line</text>'
    )

    lines.append("</svg>")
    svg_content = "\n".join(lines).encode("utf-8")

    if out.suffix == ".svgz":
        with gzip.open(out, "wb") as f:
            f.write(svg_content)
    elif out.suffix == ".png":
        # Render to temporary SVG first, then convert
        temp_svg = out.with_suffix(".temp.svg")
        temp_svg.write_bytes(svg_content)
        try:
            subprocess.run(["rsvg-convert", "-o", str(out), str(temp_svg)], check=True)
        finally:
            if temp_svg.exists():
                temp_svg.unlink()
    else:
        out.write_bytes(svg_content)
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
        "-o", "--output", default=None,
        help="Manual output filename (overrides automatic naming)",
    )
    p.add_argument(
        "-t", "--type", choices=["svg", "svgz", "png"], default="png",
        help="Output format (default: svgz)",
    )
    p.add_argument(
        "--width", type=int, default=None,
        help="Output width in pixels",
    )
    p.add_argument(
        "--height", type=int, default=None,
        help="Output total height in pixels",
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
             "(default: ../../misc_local/tmp_geojson relative to this script)",
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
        dt = datetime.datetime.fromisoformat(args.date).astimezone()
    else:
        dt = datetime.datetime.now().astimezone()

    cache_dir = (
        Path(args.cache_dir) if args.cache_dir
        else script_dir.parent.parent / "misc_local/tmp_geojson"
    )

    # ── Dimension Logic ───────────────────────────────────────────────────────
    # Default constants
    base_width = 1800.0
    base_map_height = round(base_width * (LAT_MAX - LAT_MIN) / (LON_MAX - LON_MIN))
    base_margin = 22.0
    base_total_height = base_map_height + 2 * base_margin

    if args.width and args.height:
        width = float(args.width)
        total_height = float(args.height)
        # Proportionally scale margin if we are changing size significantly
        margin = base_margin * (width / base_width)
        map_height = total_height - 2 * margin
    elif args.width:
        width = float(args.width)
        scale = width / base_width
        margin = base_margin * scale
        map_height = base_map_height * scale
        total_height = map_height + 2 * margin
    elif args.height:
        total_height = float(args.height)
        scale = total_height / base_total_height
        width = base_width * scale
        margin = base_margin * scale
        map_height = base_map_height * scale
    else:
        width = base_width
        total_height = base_total_height
        margin = base_margin
        map_height = base_map_height

    # Calculate latitude delta for margin to extend background bands to the edges
    lat_margin_delta = (LAT_MAX - LAT_MIN) * margin / map_height
    BANDS_CLIP = box(-180, LAT_MIN - lat_margin_delta, 180, LAT_MAX + lat_margin_delta)

    highlight_sfx = "_highlight" if args.highlight_non_integer else ""
    ext = f".{args.type}"

    metadata = {
        "Simulated Date": dt.isoformat(),
        "Tzdata Version": _get_tzdata_version(),
        "Boundary Builder Version": args.tz_version,
        "Options": json.dumps(vars(args)),
    }

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
            band = BANDS_CLIP.intersection(box(i * 15 - 7.5, -90, i * 15 + 7.5, 90))
            if not band.is_empty:
                offset_map[float(i)] = band

        if args.output:
            out_path = out_dir / args.output
        else:
            out_path = out_dir / f"tz_map_ideal{highlight_sfx}{ext}"

        print("Rendering SVG...", file=sys.stderr)
        render(
            offset_map, land_union, out_path,
            width=width, total_height=total_height, map_height=map_height, margin=margin,
            metadata=metadata, highlight_non_integer=args.highlight_non_integer
        )
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
        zi = zoneinfo.ZoneInfo(name)
        h = get_off(zi, dt)
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
            lambda i: _compute_ocean_band(i, display_land_union, BANDS_CLIP),
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

    if args.output:
        out_path = out_dir / args.output
    else:
        mode_sfx = {"current": "", "standard": "_standard", "dst": "_dst"}[args.mode]
        out_path = out_dir / f"tz_map{mode_sfx}{highlight_sfx}{ext}"

    print("Rendering SVG...", file=sys.stderr)
    render(
        offset_map, land_union, out_path,
        width=width, total_height=total_height, map_height=map_height, margin=margin,
        metadata=metadata, highlight_non_integer=args.highlight_non_integer
    )


if __name__ == "__main__":
    main()
