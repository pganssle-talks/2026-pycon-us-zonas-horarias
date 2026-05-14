# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

import re
from collections.abc import Sequence
from pathlib import Path


def get_slide_notes(content: str) -> Sequence[str]:
    """Splits slide content and extracts notes from each section."""
    # Split slides by '--' on its own line
    sections = re.split(r"\r?\n--\s*\r?\n", content)
    notes: list[str] = []

    for section in sections:
        # Find "Notes:" section (case-insensitive)
        # We look for "Notes:" and take everything until the end of the slide part
        if match := re.search(r"Notes:\s*(.*)", section, re.DOTALL | re.IGNORECASE):
            notes_text = match.group(1).strip()
            if notes_text:
                notes.append(notes_text)

    return notes


def extract_all_notes(posts_dir: Path, output_file: Path) -> None:
    """Extracts notes from all markdown files in posts_dir and writes to output_file."""
    if not posts_dir.is_dir():
        print(f"Error: {posts_dir} directory not found.")
        return

    # Sort files to ensure sequential order
    files = sorted(posts_dir.glob("*.md"))
    all_formatted_notes: list[str] = []

    for file_idx, file_path in enumerate(files, start=1):
        content = file_path.read_text(encoding="utf-8")
        notes = get_slide_notes(content)

        for slide_idx, notes_text in enumerate(notes, start=1):
            slide_num = f"{file_idx:02d}-{slide_idx:02d}"
            header = f"Slide {slide_num}: {file_path.name}"
            all_formatted_notes.append(f"{header}\n\n{notes_text}")

    if all_formatted_notes:
        output_file.write_text(
            "\n\n---\n\n".join(all_formatted_notes), encoding="utf-8"
        )
        print(f"Successfully extracted notes from {len(files)} files to {output_file}")
    else:
        print("No notes found in the slide files.")


if __name__ == "__main__":
    # Assume we are running from the project root
    root = Path.cwd()
    extract_all_notes(posts_dir=root / "_posts", output_file=root / "script.md")
