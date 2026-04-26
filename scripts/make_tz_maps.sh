#!/bin/bash
# Generate timezone maps using the requested configurations.
# This script is intended to be run from the project root or its own directory.

set -e

# Change to the directory where the generator script resides
cd "$(dirname "$0")"

OUTPUT_DIR="../images/figures"
MODE="standard"  # Use standard time offsets no matter the date
DATE="2026-05-15T14:00-07:00" # Date of the talk
DATE_LINE_TEXT="Línea internacional de cambio de fecha"
TYPE="png"
HEIGHT=700

echo "Generating idealized map..."
uv run --python=3.14t ./generate_tz_maps.py "$OUTPUT_DIR" \
    -t "$TYPE" \
    --height "$HEIGHT" \
    --date-line-text="$DATE_LINE_TEXT" \
    --ideal

echo "Generating standard map..."
uv run --python=3.14t ./generate_tz_maps.py "$OUTPUT_DIR" \
    -t "$TYPE" \
    --height "$HEIGHT" \
    --mode "$MODE" \
    --date-line-text="$DATE_LINE_TEXT" \
    --date "$DATE"

echo "Generating highlighted map..."
uv run --python=3.14t ./generate_tz_maps.py "$OUTPUT_DIR" \
    -t "$TYPE" \
    --height "$HEIGHT" \
    --mode "$MODE" \
    --date-line-text="$DATE_LINE_TEXT" \
    --date "$DATE" \
    --highlight-non-integer

echo "Done."
