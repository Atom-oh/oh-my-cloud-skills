#!/usr/bin/env python3
"""Extract AWS Architecture Icons for use in reactive presentations.

Extracts SVG icons from the official AWS Asset Package zip into a
presentation repo's common/aws-icons/ directory, organized by category.

Usage:
    python3 extract_aws_icons.py [--output DIR] [--categories CAT1,CAT2,...] [--size SIZE]

Examples:
    # Extract all 48px SVGs (default)
    python3 extract_aws_icons.py -o ~/reactive_presentation/common/aws-icons/

    # Extract only Containers and Management categories
    python3 extract_aws_icons.py -o ./common/aws-icons/ -c Containers,Management-Governance

    # Extract 64px icons
    python3 extract_aws_icons.py -o ./common/aws-icons/ -s 64

    # List available categories
    python3 extract_aws_icons.py --list-categories
"""

import argparse
import os
import re
import shutil
import zipfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
ZIP_PATH = SKILL_DIR / "assets" / "aws-icons.zip"

# Icon type prefixes mapped to output subdirectories
ICON_TYPES = {
    "Architecture-Service-Icons": "services",
    "Architecture-Group-Icons": "groups",
    "Category-Icons": "categories",
    "Resource-Icons": "resources",
}


def list_categories(zip_path):
    """List available service categories in the zip."""
    cats = set()
    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in zf.namelist():
            if "__MACOSX" in name:
                continue
            # Match Arch_{Category}/ pattern
            m = re.match(r"Architecture-Service-Icons_\d+/Arch_([^/]+)/", name)
            if m:
                cats.add(m.group(1))
            # Match Res_{Category}/ pattern
            m = re.match(r"Resource-Icons_\d+/Res_([^/]+)/", name)
            if m:
                cats.add(m.group(1))
    return sorted(cats)


def extract_icons(zip_path, output_dir, categories=None, size=48, svg_only=True):
    """Extract icons from zip to output directory."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    extracted = 0
    skipped = 0

    with zipfile.ZipFile(zip_path, "r") as zf:
        for entry in zf.namelist():
            # Skip macOS metadata
            if "__MACOSX" in entry or entry.endswith("/") or ".DS_Store" in entry:
                continue

            # Filter by file type
            if svg_only and not entry.endswith(".svg"):
                continue

            # Filter by size
            parts = entry.split("/")
            filename = parts[-1]

            # Check size in directory path (service/resource icons use size subdirs)
            size_parts = [p for p in parts[:-1] if p.isdigit()]
            if size_parts and str(size) not in size_parts:
                skipped += 1
                continue

            # Check size in filename (category/group icons embed size: _48.svg)
            size_in_name = re.search(r"_(\d+)\.svg$", filename)
            if size_in_name and int(size_in_name.group(1)) != size:
                skipped += 1
                continue

            # Filter by category if specified
            if categories:
                match_cat = False
                for cat in categories:
                    cat_lower = cat.lower().replace(" ", "-")
                    if cat_lower in entry.lower():
                        match_cat = True
                        break
                if not match_cat:
                    skipped += 1
                    continue

            # Determine output subdirectory
            out_subdir = ""
            for prefix, dirname in ICON_TYPES.items():
                if entry.startswith(prefix):
                    out_subdir = dirname
                    break

            # Extract filename (last part)
            filename = parts[-1]

            # Create output path
            dest_dir = output / out_subdir if out_subdir else output
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / filename

            # Extract
            with zf.open(entry) as src, open(dest_path, "wb") as dst:
                dst.write(src.read())
            extracted += 1

    # Also create an index file
    _write_index(output)

    return extracted, skipped


def _write_index(output_dir):
    """Write a simple index of extracted icons."""
    output = Path(output_dir)
    icons = {}
    for svg in sorted(output.rglob("*.svg")):
        rel = svg.relative_to(output)
        # Extract a clean name
        name = svg.stem
        # Remove size suffix like _48
        name = re.sub(r"_\d+$", "", name)
        # Remove prefixes
        name = re.sub(r"^(Arch_|Res_|Arch-Category_)", "", name)
        icons[name] = str(rel)

    index_path = output / "icon-index.txt"
    with open(index_path, "w") as f:
        f.write("# AWS Architecture Icons Index\n")
        f.write(f"# {len(icons)} icons extracted\n")
        f.write("# Format: clean-name → relative-path\n\n")
        for name, path in sorted(icons.items()):
            f.write(f"{name} → {path}\n")


def main():
    parser = argparse.ArgumentParser(description="Extract AWS Architecture Icons")
    parser.add_argument("-o", "--output", default="./common/aws-icons",
                        help="Output directory (default: ./common/aws-icons)")
    parser.add_argument("-c", "--categories", default=None,
                        help="Comma-separated categories to extract (default: all)")
    parser.add_argument("-s", "--size", type=int, default=48,
                        help="Icon size to extract: 16, 32, 48, 64 (default: 48)")
    parser.add_argument("--list-categories", action="store_true",
                        help="List available categories and exit")
    parser.add_argument("--zip", default=str(ZIP_PATH),
                        help=f"Path to AWS icons zip (default: {ZIP_PATH})")
    parser.add_argument("--include-png", action="store_true",
                        help="Include PNG files (default: SVG only)")

    args = parser.parse_args()

    zip_path = Path(args.zip)
    if not zip_path.exists():
        print(f"Error: ZIP file not found: {zip_path}")
        print(f"Expected at: {ZIP_PATH}")
        return 1

    if args.list_categories:
        cats = list_categories(zip_path)
        print("Available categories:")
        for c in cats:
            print(f"  {c}")
        return 0

    categories = [c.strip() for c in args.categories.split(",")] if args.categories else None
    extracted, skipped = extract_icons(
        zip_path, args.output,
        categories=categories,
        size=args.size,
        svg_only=not args.include_png,
    )
    print(f"Extracted {extracted} icons to {args.output}")
    if categories:
        print(f"  Categories: {', '.join(categories)}")
    print(f"  Size: {args.size}px, Format: {'SVG+PNG' if args.include_png else 'SVG only'}")
    print(f"  Skipped: {skipped} (filtered out)")
    print(f"  Index: {args.output}/icon-index.txt")
    return 0


if __name__ == "__main__":
    exit(main())
