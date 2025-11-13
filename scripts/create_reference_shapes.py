#!/usr/bin/env python3
# ABOUTME: Creates U-smile and O-shape reference paths matching base mouth structures
# ABOUTME: Generates structure-matched reference shapes for path blending

import re
from pathlib import Path

MOUTHS_OPEN_DIR = Path(__file__).parent.parent / "assets" / "mouths" / "open"


def parse_path_tokens(path_data: str) -> list:
    """Parse path into tokens (commands and numbers)."""
    return re.findall(r"[MLCVHZ]|[-+]?[0-9]*\.?[0-9]+", path_data)


def create_u_smile_from_structure(base_path: str, bbox: tuple[float, float, float, float]) -> str:
    """
    Create a U-shaped smile path that matches the structure of the base path.

    Strategy: Parse the base path structure, then create a U-shape by:
    - Keeping the same commands (M, C, V, Z, etc.)
    - Replacing coordinates to form a U-shape within the bounding box
    """
    min_x, min_y, max_x, max_y = bbox
    width = max_x - min_x
    height = max_y - min_y
    cx = min_x + width / 2

    # Create a U-shape that curves down (smile)
    # Top corners should be at min_y, bottom of U at about min_y + height * 0.7
    depth = height * 0.7
    bottom_y = min_y + depth

    tokens = parse_path_tokens(base_path)
    result = []

    # Simple strategy: Map all Y coordinates to create U-shape
    # Points near left edge (min_x) -> stay at top (min_y)
    # Points near center (cx) -> move to bottom (bottom_y)
    # Points near right edge (max_x) -> stay at top (min_y)

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token in ["M", "L", "C", "V", "H", "Z"]:
            result.append(token)
            i += 1
        else:
            # It's a number - check if it's X or Y based on context
            # This is a simplified approach
            try:
                val = float(token)
                result.append(token)  # Keep original for now
                i += 1
            except ValueError:
                result.append(token)
                i += 1

    return " ".join(result)


def create_o_shape_from_structure(base_path: str, bbox: tuple[float, float, float, float]) -> str:
    """
    Create an O-shaped path that matches the structure of the base path.
    """
    # For now, return base path - this is complex
    return base_path


def get_path_bbox(path_data: str) -> tuple[float, float, float, float]:
    """Get bounding box from path data."""
    tokens = parse_path_tokens(path_data)

    min_x = float("inf")
    max_x = float("-inf")
    min_y = float("inf")
    max_y = float("-inf")

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token in ["M", "L"]:
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
        elif token == "C":
            if i + 6 < len(tokens):
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
        elif token == "V":
            if i + 1 < len(tokens):
                y = float(tokens[i + 1])
                min_y = min(min_y, y)
                max_y = max(max_y, y)
                i += 2
            else:
                i += 1
        elif token == "H":
            if i + 1 < len(tokens):
                x = float(tokens[i + 1])
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                i += 2
            else:
                i += 1
        elif token == "Z":
            i += 1
        else:
            i += 1

    return (min_x, min_y, max_x, max_y)


if __name__ == "__main__":
    # Read base mouth files and analyze their structures
    for mouth_file in sorted(MOUTHS_OPEN_DIR.glob("[0-9].svg")):
        print(f"\n=== {mouth_file.name} ===")

        content = mouth_file.read_text()
        # Extract path data
        match = re.search(r'd="([^"]+)"', content)
        if match:
            path_data = match.group(1)
            tokens = parse_path_tokens(path_data)
            bbox = get_path_bbox(path_data)

            print(f"Tokens: {len(tokens)}")
            print(f"BBox: {bbox}")
            print(
                f"Path structure: {' '.join(t for t in tokens if t in ['M', 'L', 'C', 'V', 'H', 'Z'])}"
            )
            print(f"Path: {path_data[:100]}...")
