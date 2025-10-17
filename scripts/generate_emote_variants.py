#!/usr/bin/env python3
# ABOUTME: Generates emote-specific variants of eye and mouth SVGs through pupil repositioning
# ABOUTME: Positions pupils relative to eye whites bounding box for happy/sad/surprised/angry/bored emotes

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import re


# Base directories
ASSETS_DIR = Path(__file__).parent.parent / "assets"
EYES_OPEN_DIR = ASSETS_DIR / "eyes" / "open"
EYES_CLOSED_DIR = ASSETS_DIR / "eyes" / "closed"
MOUTHS_OPEN_DIR = ASSETS_DIR / "mouths" / "open"
MOUTHS_CLOSED_DIR = ASSETS_DIR / "mouths" / "closed"


def parse_path_bbox(path_data: str) -> Tuple[float, float, float, float]:
    """
    Extract bounding box (min_x, min_y, max_x, max_y) from SVG path data.

    Handles M (moveto), L (lineto), C (cubic bezier), Z (closepath) commands.
    Approximates bezier curves using control points for bbox estimation.
    """
    # Parse path commands and extract coordinates
    # Match command letter followed by numbers (including negative and decimal)
    tokens = re.findall(r'[MLCZ]|[-+]?[0-9]*\.?[0-9]+', path_data)

    min_x = float('inf')
    max_x = float('-inf')
    min_y = float('inf')
    max_y = float('-inf')

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token in ['M', 'L']:  # Moveto or Lineto - next 2 values are x, y
            if i + 2 < len(tokens):
                x = float(tokens[i + 1])
                y = float(tokens[i + 2])
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)
                i += 3
            else:
                i += 1

        elif token == 'C':  # Cubic bezier - next 6 values are control points and end point
            if i + 6 < len(tokens):
                # Include all control points in bbox estimation
                for j in range(1, 7, 2):
                    x = float(tokens[i + j])
                    y = float(tokens[i + j + 1])
                    min_x = min(min_x, x)
                    max_x = max(max_x, x)
                    min_y = min(min_y, y)
                    max_y = max(max_y, y)
                i += 7
            else:
                i += 1

        elif token == 'Z':  # Closepath - no coordinates
            i += 1
        else:
            # Numeric value without command - skip
            i += 1

    return (min_x, min_y, max_x, max_y)


def get_path_center(path_data: str) -> Tuple[float, float]:
    """Calculate center point of a path from its bounding box."""
    min_x, min_y, max_x, max_y = parse_path_bbox(path_data)
    cx = (min_x + max_x) / 2
    cy = (min_y + max_y) / 2
    return (cx, cy)


def translate_path(path_data: str, dx: float, dy: float) -> str:
    """
    Translate all coordinates in an SVG path by (dx, dy).

    Handles M (moveto), L (lineto), C (cubic bezier), Z (closepath) commands.
    """
    tokens = re.findall(r'[MLCZ]|[-+]?[0-9]*\.?[0-9]+', path_data)
    result = []

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token in ['M', 'L']:
            result.append(token)
            if i + 2 < len(tokens):
                x = float(tokens[i + 1]) + dx
                y = float(tokens[i + 2]) + dy
                result.append(f"{x:.3f}")
                result.append(f"{y:.3f}")
                i += 3
            else:
                i += 1

        elif token == 'C':
            result.append(token)
            if i + 6 < len(tokens):
                for j in range(1, 7, 2):
                    x = float(tokens[i + j]) + dx
                    y = float(tokens[i + j + 1]) + dy
                    result.append(f"{x:.3f}")
                    result.append(f"{y:.3f}")
                i += 7
            else:
                i += 1

        elif token == 'Z':
            result.append(token)
            i += 1
        else:
            result.append(token)
            i += 1

    return ' '.join(result)


def find_eye_elements(root: ET.Element) -> Tuple[List[ET.Element], List[ET.Element]]:
    """
    Find whites (light fills) and pupils (dark fills) in SVG.

    Returns:
        (whites_paths, pupils_paths) - Lists of path elements
    """
    whites = []
    pupils = []

    for elem in root.iter():
        if elem.tag.endswith('path'):
            fill = elem.get('fill', '').upper()
            # Whites are light colors like #F9F9F6
            if fill in ['#F9F9F6', '#FFFFFF', '#F9F9F5']:
                whites.append(elem)
            # Pupils are dark colors like #2B2727 or #231F20
            elif fill in ['#2B2727', '#231F20']:
                pupils.append(elem)

    return whites, pupils


def get_combined_bbox(paths: List[ET.Element]) -> Tuple[float, float, float, float]:
    """Get bounding box that encompasses all provided path elements."""
    if not paths:
        return (0, 0, 0, 0)

    min_x = float('inf')
    max_x = float('-inf')
    min_y = float('inf')
    max_y = float('-inf')

    for path in paths:
        path_data = path.get('d', '')
        if path_data:
            bbox = parse_path_bbox(path_data)
            min_x = min(min_x, bbox[0])
            min_y = min(min_y, bbox[1])
            max_x = max(max_x, bbox[2])
            max_y = max(max_y, bbox[3])

    return (min_x, min_y, max_x, max_y)


def reposition_pupils(
    root: ET.Element,
    pupil_position: str
) -> ET.Element:
    """
    Reposition pupils within eye whites bounding box.

    Args:
        root: SVG root element
        pupil_position: "center", "top" (top 5%), or "bottom" (bottom 5%)

    Returns:
        Modified root element
    """
    whites, pupils = find_eye_elements(root)

    if not pupils or not whites:
        # No pupils or whites found - return unchanged
        return root

    # Get bounding box of all whites
    whites_bbox = get_combined_bbox(whites)
    whites_min_y = whites_bbox[1]
    whites_max_y = whites_bbox[3]
    whites_height = whites_max_y - whites_min_y

    # Calculate target Y position based on position type
    if pupil_position == "top":
        # Top 5% of whites
        target_y = whites_min_y + (whites_height * 0.05)
    elif pupil_position == "bottom":
        # Bottom 5% of whites (95% down)
        target_y = whites_min_y + (whites_height * 0.95)
    else:  # "center"
        # Vertical center of whites
        target_y = whites_min_y + (whites_height * 0.5)

    # Reposition each pupil
    for pupil in pupils:
        path_data = pupil.get('d', '')
        if path_data:
            # Get current pupil center
            current_cx, current_cy = get_path_center(path_data)

            # Calculate translation needed
            dy = target_y - current_cy

            # Translate pupil path
            new_path_data = translate_path(path_data, 0, dy)
            pupil.set('d', new_path_data)

    return root


def scale_eyes(root: ET.Element, scale_factor: float) -> ET.Element:
    """
    Scales entire eye SVG from its center point.
    """
    # Parse viewBox to find center
    viewbox = root.get('viewBox', '0 0 100 100')
    parts = viewbox.split()
    if len(parts) == 4:
        x, y, w, h = map(float, parts)
        cx = x + w / 2
        cy = y + h / 2

        # Apply scale transform to all direct children
        for child in list(root):
            existing = child.get('transform', '')
            transform = f"translate({cx}, {cy}) scale({scale_factor}) translate({-cx}, {-cy})"
            if existing:
                child.set('transform', f"{transform} {existing}")
            else:
                child.set('transform', transform)

    return root


def process_emote_variant(
    base_svg_path: Path,
    output_path: Path,
    transform_config: Dict
) -> bool:
    """
    Processes a single SVG file to create an emote variant.

    Args:
        base_svg_path: Path to base SVG file
        output_path: Path to write variant SVG
        transform_config: Configuration for transformations
            - pupil_position: "center", "top", or "bottom"
            - scale: scale factor for eye_scale

    Returns:
        True if successful, False otherwise
    """
    try:
        tree = ET.parse(base_svg_path)
        root = tree.getroot()

        # Apply transformations based on config
        if 'pupil_position' in transform_config:
            reposition_pupils(root, transform_config['pupil_position'])

        if 'scale' in transform_config:
            scale_eyes(root, transform_config['scale'])

        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        tree.write(output_path, encoding='unicode', xml_declaration=False)

        # Clean up the output (ElementTree adds namespace)
        content = output_path.read_text()
        content = content.replace('ns0:', '').replace(':ns0', '').replace('xmlns:ns0=', 'xmlns=')
        output_path.write_text(content)

        return True
    except Exception as e:
        print(f"Error processing {base_svg_path}: {e}")
        import traceback
        traceback.print_exc()
        return False


# Emote transformation definitions
EMOTE_TRANSFORMS = {
    "happy": {
        "eyes_open": {"pupil_position": "top"},  # Looking up (joyful)
        "eyes_closed": {},  # Use closed eyes as-is
        "mouths_open": {},  # Already smiling
        "mouths_closed": {}
    },
    "sad": {
        "eyes_open": {"pupil_position": "bottom"},  # Looking down (sad)
        "eyes_closed": {},
        "mouths_open": {},
        "mouths_closed": {}
    },
    "surprised": {
        "eyes_open": {"scale": 1.15},  # Wider eyes
        "eyes_closed": {},
        "mouths_open": {},  # Already O-shaped
        "mouths_closed": {}
    },
    "angry": {
        "eyes_open": {"pupil_position": "center"},  # Focused/intense
        "eyes_closed": {},
        "mouths_open": {},
        "mouths_closed": {}
    },
    "bored": {
        "eyes_open": {},  # Use open eyes as-is
        "eyes_closed": {},  # Use closed eyes for half-lidded look
        "mouths_open": {},
        "mouths_closed": {}
    }
}


def generate_all_emote_variants(emotes: Optional[List[str]] = None):
    """
    Generates all emote variants for eyes and mouths.

    Args:
        emotes: List of emote names to generate. If None, generates all.
    """
    if emotes is None:
        emotes = list(EMOTE_TRANSFORMS.keys())

    stats = {
        "total": 0,
        "success": 0,
        "failed": 0
    }

    for emote_name in emotes:
        if emote_name not in EMOTE_TRANSFORMS:
            print(f"Warning: Unknown emote '{emote_name}', skipping")
            continue

        print(f"\nGenerating {emote_name} emote variants...")
        transforms = EMOTE_TRANSFORMS[emote_name]

        # Process open eyes
        if EYES_OPEN_DIR.exists():
            for base_file in sorted(EYES_OPEN_DIR.glob("*.svg")):
                # Skip if already an emote variant
                if base_file.stem.startswith("emote_"):
                    continue

                output_file = EYES_OPEN_DIR / f"emote_{emote_name}_{base_file.name}"
                transform_config = transforms["eyes_open"]

                stats["total"] += 1
                if process_emote_variant(base_file, output_file, transform_config):
                    stats["success"] += 1
                    print(f"  Created: {output_file.relative_to(ASSETS_DIR)}")
                else:
                    stats["failed"] += 1

        # Process closed eyes
        if EYES_CLOSED_DIR.exists():
            for base_file in sorted(EYES_CLOSED_DIR.glob("*.svg")):
                if base_file.stem.startswith("emote_"):
                    continue

                output_file = EYES_CLOSED_DIR / f"emote_{emote_name}_{base_file.name}"
                transform_config = transforms["eyes_closed"]

                stats["total"] += 1
                if process_emote_variant(base_file, output_file, transform_config):
                    stats["success"] += 1
                    print(f"  Created: {output_file.relative_to(ASSETS_DIR)}")
                else:
                    stats["failed"] += 1

        # Process open mouths
        if MOUTHS_OPEN_DIR.exists():
            for base_file in sorted(MOUTHS_OPEN_DIR.glob("*.svg")):
                if base_file.stem.startswith("emote_"):
                    continue

                output_file = MOUTHS_OPEN_DIR / f"emote_{emote_name}_{base_file.name}"
                transform_config = transforms["mouths_open"]

                stats["total"] += 1
                if process_emote_variant(base_file, output_file, transform_config):
                    stats["success"] += 1
                    print(f"  Created: {output_file.relative_to(ASSETS_DIR)}")
                else:
                    stats["failed"] += 1

        # Process closed mouths
        if MOUTHS_CLOSED_DIR.exists():
            for base_file in sorted(MOUTHS_CLOSED_DIR.glob("*.svg")):
                if base_file.stem.startswith("emote_"):
                    continue

                output_file = MOUTHS_CLOSED_DIR / f"emote_{emote_name}_{base_file.name}"
                transform_config = transforms["mouths_closed"]

                stats["total"] += 1
                if process_emote_variant(base_file, output_file, transform_config):
                    stats["success"] += 1
                    print(f"  Created: {output_file.relative_to(ASSETS_DIR)}")
                else:
                    stats["failed"] += 1

    print(f"\n{'='*60}")
    print(f"Emote variant generation complete!")
    print(f"Total variants: {stats['total']}")
    print(f"Successful: {stats['success']}")
    print(f"Failed: {stats['failed']}")
    print(f"{'='*60}")


if __name__ == "__main__":
    import sys

    # Parse command line arguments
    if len(sys.argv) > 1:
        emotes = sys.argv[1:]
        print(f"Generating variants for emotes: {', '.join(emotes)}")
        generate_all_emote_variants(emotes)
    else:
        print("Generating all emote variants...")
        generate_all_emote_variants()
