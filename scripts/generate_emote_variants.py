#!/usr/bin/env python3
# ABOUTME: Generates emote-specific variants of eye and mouth SVGs through transformations
# ABOUTME: Applies translate, scale, and rotation transforms to create happy/sad/surprised/angry/bored variants

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


def find_pupil_elements(root: ET.Element) -> List[ET.Element]:
    """
    Find pupil elements in an eye SVG (dark fill elements).
    Looks for paths with dark fills like #2B2727.
    """
    pupils = []
    for elem in root.iter():
        if elem.tag.endswith('path'):
            fill = elem.get('fill', '')
            if fill.lower() in ['#2b2727', '#231f20'] or 'rgb(43, 39, 39)' in fill.lower():
                pupils.append(elem)
    return pupils


def apply_transform_to_element(elem: ET.Element, transform: str):
    """
    Applies a transform to an SVG element by prepending to existing transform.
    """
    existing = elem.get('transform', '')
    if existing:
        elem.set('transform', f"{transform} {existing}")
    else:
        elem.set('transform', transform)


def translate_pupils(root: ET.Element, dx: float, dy: float) -> ET.Element:
    """
    Translates pupil elements by (dx, dy) pixels.
    """
    pupils = find_pupil_elements(root)
    for pupil in pupils:
        apply_transform_to_element(pupil, f"translate({dx}, {dy})")
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

        # Apply scale transform to root or create a group
        for child in list(root):
            apply_transform_to_element(child, f"translate({cx}, {cy}) scale({scale_factor}) translate({-cx}, {-cy})")

    return root


def rotate_element(elem: ET.Element, angle: float, cx: float, cy: float):
    """
    Rotates an element around a center point.
    """
    apply_transform_to_element(elem, f"rotate({angle}, {cx}, {cy})")


def process_emote_variant(
    base_svg_path: Path,
    output_path: Path,
    transform_type: str,
    params: Dict
) -> bool:
    """
    Processes a single SVG file to create an emote variant.

    Args:
        base_svg_path: Path to base SVG file
        output_path: Path to write variant SVG
        transform_type: Type of transformation (pupil_translate, eye_scale, etc)
        params: Parameters for the transformation

    Returns:
        True if successful, False otherwise
    """
    try:
        tree = ET.parse(base_svg_path)
        root = tree.getroot()

        if transform_type == "pupil_translate":
            translate_pupils(root, params.get('dx', 0), params.get('dy', 0))
        elif transform_type == "eye_scale":
            scale_eyes(root, params.get('scale', 1.0))
        elif transform_type == "none":
            # Just copy as-is
            pass

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
        return False


# Emote transformation definitions
EMOTE_TRANSFORMS = {
    "happy": {
        "eyes_open": {
            "transform_type": "pupil_translate",
            "params": {"dx": 0, "dy": -0.5}  # Pupils up slightly
        },
        "eyes_closed": {
            "transform_type": "none",  # Use closed eyes as-is
            "params": {}
        },
        "mouths_open": {
            "transform_type": "none",  # Already smiling
            "params": {}
        },
        "mouths_closed": {
            "transform_type": "none",
            "params": {}
        }
    },
    "sad": {
        "eyes_open": {
            "transform_type": "pupil_translate",
            "params": {"dx": 0, "dy": 0.8}  # Pupils down
        },
        "eyes_closed": {
            "transform_type": "none",
            "params": {}
        },
        "mouths_open": {
            "transform_type": "none",
            "params": {}
        },
        "mouths_closed": {
            "transform_type": "none",
            "params": {}
        }
    },
    "surprised": {
        "eyes_open": {
            "transform_type": "eye_scale",
            "params": {"scale": 1.15}  # Wider eyes
        },
        "eyes_closed": {
            "transform_type": "none",
            "params": {}
        },
        "mouths_open": {
            "transform_type": "none",  # Already O-shaped
            "params": {}
        },
        "mouths_closed": {
            "transform_type": "none",
            "params": {}
        }
    },
    "angry": {
        "eyes_open": {
            "transform_type": "pupil_translate",
            "params": {"dx": 0, "dy": 0}  # Centered pupils
        },
        "eyes_closed": {
            "transform_type": "none",
            "params": {}
        },
        "mouths_open": {
            "transform_type": "none",
            "params": {}
        },
        "mouths_closed": {
            "transform_type": "none",  # Tight mouth
            "params": {}
        }
    },
    "bored": {
        "eyes_open": {
            "transform_type": "none",
            "params": {}
        },
        "eyes_closed": {
            "transform_type": "none",  # Use closed eyes
            "params": {}
        },
        "mouths_open": {
            "transform_type": "none",
            "params": {}
        },
        "mouths_closed": {
            "transform_type": "none",
            "params": {}
        }
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
                if process_emote_variant(
                    base_file,
                    output_file,
                    transform_config["transform_type"],
                    transform_config["params"]
                ):
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
                if process_emote_variant(
                    base_file,
                    output_file,
                    transform_config["transform_type"],
                    transform_config["params"]
                ):
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
                if process_emote_variant(
                    base_file,
                    output_file,
                    transform_config["transform_type"],
                    transform_config["params"]
                ):
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
                if process_emote_variant(
                    base_file,
                    output_file,
                    transform_config["transform_type"],
                    transform_config["params"]
                ):
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
