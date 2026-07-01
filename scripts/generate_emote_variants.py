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
        pupil_position: "center", "top" (top 5%), "bottom" (bottom 5%),
                       "upper_third" (1/3 down), "lower_third" (2/3 down)

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
    elif pupil_position == "upper_third":
        # 1/3 down from top (33%)
        target_y = whites_min_y + (whites_height * 0.33)
    elif pupil_position == "lower_third":
        # 2/3 down from top (67%)
        target_y = whites_min_y + (whites_height * 0.67)
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


def scale_path_around_center(path_data: str, scale: float, center_x: float, center_y: float) -> str:
    """
    Scale path coordinates around a center point.

    For each coordinate pair (x, y) in path:
    new_x = center_x + (x - center_x) * scale
    new_y = center_y + (y - center_y) * scale
    """
    tokens = re.findall(r'[MLCZ]|[-+]?[0-9]*\.?[0-9]+', path_data)
    result = []

    i = 0
    while i < len(tokens):
        token = tokens[i]

        if token in ['M', 'L']:
            result.append(token)
            if i + 2 < len(tokens):
                x = float(tokens[i + 1])
                y = float(tokens[i + 2])
                # Scale around center
                new_x = center_x + (x - center_x) * scale
                new_y = center_y + (y - center_y) * scale
                result.append(f"{new_x:.3f}")
                result.append(f"{new_y:.3f}")
                i += 3
            else:
                i += 1

        elif token == 'C':
            result.append(token)
            if i + 6 < len(tokens):
                for j in range(1, 7, 2):
                    x = float(tokens[i + j])
                    y = float(tokens[i + j + 1])
                    # Scale around center
                    new_x = center_x + (x - center_x) * scale
                    new_y = center_y + (y - center_y) * scale
                    result.append(f"{new_x:.3f}")
                    result.append(f"{new_y:.3f}")
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


def scale_pupils_only(root: ET.Element, scale_factor: float) -> ET.Element:
    """
    Scale only the pupils (dark fills) around their centers.
    Used for surprised emote to make pupils look wider.
    """
    whites, pupils = find_eye_elements(root)

    if not pupils:
        return root

    # Scale each pupil around its own center
    for pupil in pupils:
        path_data = pupil.get('d', '')
        if path_data:
            # Get pupil center
            center_x, center_y = get_path_center(path_data)
            # Scale path around its center
            new_path_data = scale_path_around_center(path_data, scale_factor, center_x, center_y)
            pupil.set('d', new_path_data)

    return root


def clip_top_half_of_eyes(root: ET.Element) -> ET.Element:
    """
    Clip the top half of eyes to create a half-lidded, bored look.
    Adds a clipPath that shows only the bottom half of the eye whites.
    """
    whites, pupils = find_eye_elements(root)

    if not whites:
        return root

    # Get bounding box of all whites to determine left vs right eyes
    bbox = get_combined_bbox(whites)
    min_x, min_y, max_x, max_y = bbox
    center_x = (min_x + max_x) / 2

    # Separate left and right eye elements
    left_whites = []
    left_pupils = []
    right_whites = []
    right_pupils = []

    for white in whites:
        path_data = white.get('d', '')
        if path_data:
            cx, cy = get_path_center(path_data)
            if cx < center_x:
                left_whites.append(white)
            else:
                right_whites.append(white)

    for pupil in pupils:
        path_data = pupil.get('d', '')
        if path_data:
            cx, cy = get_path_center(path_data)
            if cx < center_x:
                left_pupils.append(pupil)
            else:
                right_pupils.append(pupil)

    # Create clipPath for left eye
    if left_whites:
        left_bbox = get_combined_bbox(left_whites)
        l_min_x, l_min_y, l_max_x, l_max_y = left_bbox
        l_height = l_max_y - l_min_y
        l_mid_y = l_min_y + (l_height / 2)

        clip_id_left = "bored-clip-left"
        clipPath_left = ET.Element('clipPath', {'id': clip_id_left})
        rect_left = ET.Element('rect', {
            'x': str(l_min_x),
            'y': str(l_mid_y),
            'width': str(l_max_x - l_min_x),
            'height': str(l_height / 2)
        })
        clipPath_left.append(rect_left)
        root.insert(0, clipPath_left)

        # Wrap left eye elements in group with clip
        g_left = ET.Element('g', {'clip-path': f'url(#{clip_id_left})'})
        for elem in left_whites + left_pupils:
            root.remove(elem)
            g_left.append(elem)
        root.append(g_left)

        # Add horizontal line for left eye
        line_left = ET.Element('line', {
            'x1': str(l_min_x),
            'y1': str(l_mid_y),
            'x2': str(l_max_x),
            'y2': str(l_mid_y),
            'stroke': '#231F20',
            'stroke-width': '0.75'
        })
        root.append(line_left)

    # Create clipPath for right eye
    if right_whites:
        right_bbox = get_combined_bbox(right_whites)
        r_min_x, r_min_y, r_max_x, r_max_y = right_bbox
        r_height = r_max_y - r_min_y
        r_mid_y = r_min_y + (r_height / 2)

        clip_id_right = "bored-clip-right"
        clipPath_right = ET.Element('clipPath', {'id': clip_id_right})
        rect_right = ET.Element('rect', {
            'x': str(r_min_x),
            'y': str(r_mid_y),
            'width': str(r_max_x - r_min_x),
            'height': str(r_height / 2)
        })
        clipPath_right.append(rect_right)
        root.insert(0, clipPath_right)

        # Wrap right eye elements in group with clip
        g_right = ET.Element('g', {'clip-path': f'url(#{clip_id_right})'})
        for elem in right_whites + right_pupils:
            root.remove(elem)
            g_right.append(elem)
        root.append(g_right)

        # Add horizontal line for right eye
        line_right = ET.Element('line', {
            'x1': str(r_min_x),
            'y1': str(r_mid_y),
            'x2': str(r_max_x),
            'y2': str(r_mid_y),
            'stroke': '#231F20',
            'stroke-width': '0.75'
        })
        root.append(line_right)

    return root


def clip_eyes_angled(root: ET.Element) -> ET.Element:
    """
    Clip eyes with angled cuts pointing toward center for angry expression.
    Left eye: backslash angle (upper-left to lower-right)
    Right eye: forward slash angle (upper-right to lower-left)
    Creates classic angry eyebrow V-shape.
    """
    whites, pupils = find_eye_elements(root)

    if not whites:
        return root

    # Get bounding box of all whites to determine left vs right eyes
    bbox = get_combined_bbox(whites)
    min_x, min_y, max_x, max_y = bbox
    center_x = (min_x + max_x) / 2

    # Separate left and right eye elements
    left_whites = []
    left_pupils = []
    right_whites = []
    right_pupils = []

    for white in whites:
        path_data = white.get('d', '')
        if path_data:
            cx, cy = get_path_center(path_data)
            if cx < center_x:
                left_whites.append(white)
            else:
                right_whites.append(white)

    for pupil in pupils:
        path_data = pupil.get('d', '')
        if path_data:
            cx, cy = get_path_center(path_data)
            if cx < center_x:
                left_pupils.append(pupil)
            else:
                right_pupils.append(pupil)

    # Create clipPath for left eye (\ angle)
    if left_whites:
        left_bbox = get_combined_bbox(left_whites)
        l_min_x, l_min_y, l_max_x, l_max_y = left_bbox
        l_width = l_max_x - l_min_x
        l_height = l_max_y - l_min_y
        l_target_y = l_min_y + (l_height * 2 / 3)  # 2/3 down = 1/3 up from bottom

        # Angled clip: top outer corner (top-left) to bottom third of inner edge (right)
        clip_id_left = "angry-clip-left"
        clipPath_left = ET.Element('clipPath', {'id': clip_id_left})

        # Polygon: top-left corner → 2/3 down right edge (1/3 up from bottom) → bottom corners
        points = (
            f"{l_min_x - 1},{l_min_y - 1} "      # Top-left corner (outer)
            f"{l_max_x + 1},{l_target_y} "       # 2/3 down right edge (inner)
            f"{l_max_x + 1},{l_max_y + 1} "      # Bottom-right corner
            f"{l_min_x - 1},{l_max_y + 1}"       # Bottom-left corner
        )
        polygon_left = ET.Element('polygon', {'points': points})
        clipPath_left.append(polygon_left)
        root.insert(0, clipPath_left)

        # Wrap left eye elements in group with clip
        g_left = ET.Element('g', {'clip-path': f'url(#{clip_id_left})'})
        for elem in left_whites + left_pupils:
            root.remove(elem)
            g_left.append(elem)
        root.append(g_left)

    # Create clipPath for right eye (/ angle)
    if right_whites:
        right_bbox = get_combined_bbox(right_whites)
        r_min_x, r_min_y, r_max_x, r_max_y = right_bbox
        r_width = r_max_x - r_min_x
        r_height = r_max_y - r_min_y
        r_target_y = r_min_y + (r_height * 2 / 3)  # 2/3 down = 1/3 up from bottom

        # Angled clip: top outer corner (top-right) to bottom third of inner edge (left)
        clip_id_right = "angry-clip-right"
        clipPath_right = ET.Element('clipPath', {'id': clip_id_right})

        # Polygon: top-right corner → 2/3 down left edge (1/3 up from bottom) → bottom corners
        points = (
            f"{r_max_x + 1},{r_min_y - 1} "      # Top-right corner (outer)
            f"{r_min_x - 1},{r_target_y} "       # 2/3 down left edge (inner)
            f"{r_min_x - 1},{r_max_y + 1} "      # Bottom-left corner
            f"{r_max_x + 1},{r_max_y + 1}"       # Bottom-right corner
        )
        polygon_right = ET.Element('polygon', {'points': points})
        clipPath_right.append(polygon_right)
        root.insert(0, clipPath_right)

        # Wrap right eye elements in group with clip
        g_right = ET.Element('g', {'clip-path': f'url(#{clip_id_right})'})
        for elem in right_whites + right_pupils:
            root.remove(elem)
            g_right.append(elem)
        root.append(g_right)

        # Add angled line stroke for right eye (/ angle)
        line_right = ET.Element('line', {
            'x1': str(r_max_x),
            'y1': str(r_min_y),
            'x2': str(r_min_x),
            'y2': str(r_target_y),
            'stroke': '#231F20',
            'stroke-width': '0.75'
        })
        root.append(line_right)

    # Add angled line stroke for left eye (\ angle) - only if left eye was processed
    if left_whites:
        line_left = ET.Element('line', {
            'x1': str(l_min_x),
            'y1': str(l_min_y),
            'x2': str(l_max_x),
            'y2': str(l_target_y),
            'stroke': '#231F20',
            'stroke-width': '0.75'
        })
        root.append(line_left)

    return root


def rotate_mouth(root: ET.Element, rotation_degrees: float) -> ET.Element:
    """
    Rotate mouth around its center point.

    Args:
        root: SVG root element
        rotation_degrees: Positive = clockwise, Negative = counter-clockwise

    Returns:
        Modified root element
    """
    # Parse viewBox to find center
    viewbox = root.get('viewBox', '0 0 100 100')
    parts = viewbox.split()
    if len(parts) == 4:
        x, y, w, h = map(float, parts)
        cx = x + w / 2
        cy = y + h / 2

        # Apply rotation transform to all path elements
        for elem in root.iter():
            if elem.tag.endswith('path'):
                existing = elem.get('transform', '')
                transform = f"rotate({rotation_degrees} {cx} {cy})"
                if existing:
                    elem.set('transform', f"{transform} {existing}")
                else:
                    elem.set('transform', transform)

    return root


def scale_mouth(root: ET.Element, scale_x: float = 1.0, scale_y: float = 1.0) -> ET.Element:
    """
    Scale mouth around its center point and adjust viewBox to accommodate.

    Args:
        root: SVG root element
        scale_x: Horizontal scale factor (>1 = wider, <1 = narrower)
        scale_y: Vertical scale factor (>1 = taller, <1 = shorter)

    Returns:
        Modified root element
    """
    # Parse viewBox to find center
    viewbox = root.get('viewBox', '0 0 100 100')
    parts = viewbox.split()
    if len(parts) == 4:
        x, y, w, h = map(float, parts)
        cx = x + w / 2
        cy = y + h / 2

        # Apply scale transform to all path elements
        for elem in root.iter():
            if elem.tag.endswith('path'):
                existing = elem.get('transform', '')
                transform = f"translate({cx}, {cy}) scale({scale_x}, {scale_y}) translate({-cx}, {-cy})"
                if existing:
                    elem.set('transform', f"{transform} {existing}")
                else:
                    elem.set('transform', transform)

        # Expand viewBox to accommodate scaled content
        # Calculate how much larger the content will be
        max_scale = max(scale_x, scale_y)
        if max_scale > 1.0:
            # Expand viewBox from center
            new_w = w * max_scale
            new_h = h * max_scale
            new_x = cx - (new_w / 2)
            new_y = cy - (new_h / 2)
            root.set('viewBox', f"{new_x} {new_y} {new_w} {new_h}")

    return root


def flip_mouth_vertically(root: ET.Element) -> ET.Element:
    """
    Flip mouth vertically (upside down) for sad expression.

    Args:
        root: SVG root element

    Returns:
        Modified root element
    """
    # Parse viewBox to find center
    viewbox = root.get('viewBox', '0 0 100 100')
    parts = viewbox.split()
    if len(parts) == 4:
        x, y, w, h = map(float, parts)
        cy = y + h / 2

        # Apply vertical flip transform to all path elements
        for elem in root.iter():
            if elem.tag.endswith('path'):
                existing = elem.get('transform', '')
                # Flip around horizontal center line
                transform = f"translate(0, {cy}) scale(1, -1) translate(0, {-cy})"
                if existing:
                    elem.set('transform', f"{transform} {existing}")
                else:
                    elem.set('transform', transform)

    return root


def flatten_mouth(root: ET.Element, flatten_amount: float = 0.5) -> ET.Element:
    """
    Flatten a mouth path by averaging Y coordinates toward a horizontal line.

    Args:
        root: SVG root element
        flatten_amount: 0.0 = no change, 1.0 = completely flat (default 0.5 = halfway)

    Returns:
        Modified root element
    """
    # Find all path elements
    for elem in root.iter():
        if elem.tag.endswith('path'):
            path_data = elem.get('d', '')
            if not path_data:
                continue

            # Parse the path to find the average Y coordinate
            tokens = re.findall(r'[MLCZ]|[-+]?[0-9]*\.?[0-9]+', path_data)

            # Collect all Y coordinates
            y_coords = []
            i = 0
            while i < len(tokens):
                token = tokens[i]
                if token in ['M', 'L']:
                    if i + 2 < len(tokens):
                        y_coords.append(float(tokens[i + 2]))
                        i += 3
                    else:
                        i += 1
                elif token == 'C':
                    if i + 6 < len(tokens):
                        # Bezier control points
                        y_coords.append(float(tokens[i + 2]))
                        y_coords.append(float(tokens[i + 4]))
                        y_coords.append(float(tokens[i + 6]))
                        i += 7
                    else:
                        i += 1
                else:
                    i += 1

            if not y_coords:
                continue

            # Calculate average Y (the horizontal line we're flattening toward)
            avg_y = sum(y_coords) / len(y_coords)

            # Rebuild path with flattened Y coordinates
            result = []
            i = 0
            while i < len(tokens):
                token = tokens[i]

                if token in ['M', 'L']:
                    result.append(token)
                    if i + 2 < len(tokens):
                        x = tokens[i + 1]
                        y = float(tokens[i + 2])
                        # Flatten: move Y toward average
                        new_y = y + (avg_y - y) * flatten_amount
                        result.append(x)
                        result.append(f"{new_y:.5f}")
                        i += 3
                    else:
                        i += 1

                elif token == 'C':
                    result.append(token)
                    if i + 6 < len(tokens):
                        for j in range(1, 7, 2):
                            x = tokens[i + j]
                            y = float(tokens[i + j + 1])
                            # Flatten: move Y toward average
                            new_y = y + (avg_y - y) * flatten_amount
                            result.append(x)
                            result.append(f"{new_y:.5f}")
                        i += 7
                    else:
                        i += 1

                elif token == 'Z':
                    result.append(token)
                    i += 1
                else:
                    result.append(token)
                    i += 1

            elem.set('d', ' '.join(result))

    return root


def mirror_mouth_to_round(root: ET.Element) -> ET.Element:
    """
    Create a round O-shaped mouth by duplicating and flipping the mouth path.
    Takes the existing path, mirrors it vertically around the top edge, creating an oval.

    Args:
        root: SVG root element

    Returns:
        Modified root element with mirrored mouth
    """
    # Find all path elements
    paths = [elem for elem in root.iter() if elem.tag.endswith('path')]

    if not paths:
        return root

    # For each path, create a mirrored copy
    for path in paths:
        path_data = path.get('d', '')
        if not path_data:
            continue

        # Get the bounding box of the path to find the top edge
        bbox = parse_path_bbox(path_data)
        min_x, min_y, max_x, max_y = bbox

        # We want to flip around the top edge (min_y) to create an oval
        # The bottom of the mouth becomes the top when flipped
        flip_y = min_y

        # Create a mirrored group containing both original and flipped path
        g = ET.Element('g')

        # Original path (bottom half of the O)
        original = ET.Element('path')
        original.set('d', path_data)
        for attr in ['fill', 'stroke', 'stroke-width', 'stroke-miterlimit']:
            if path.get(attr):
                original.set(attr, path.get(attr))
        g.append(original)

        # Mirrored path (top half of the O) - flip vertically around the top edge
        mirrored = ET.Element('path')
        mirrored.set('d', path_data)
        for attr in ['fill', 'stroke', 'stroke-width', 'stroke-miterlimit']:
            if path.get(attr):
                mirrored.set(attr, path.get(attr))
        # Flip around the top edge: translate to origin, scale -1 in Y, translate back
        mirrored.set('transform', f'translate(0, {flip_y}) scale(1, -1) translate(0, {-flip_y})')
        g.append(mirrored)

        # Replace the original path with the group
        parent = root
        parent.remove(path)
        parent.append(g)

    return root


def blend_paths(path1_data: str, path2_data: str, blend_factor: float = 0.5) -> str:
    """
    Blend two SVG paths by averaging their coordinates.

    Args:
        path1_data: First path data string
        path2_data: Second path data string
        blend_factor: Blending factor (0.0 = path1, 1.0 = path2, 0.5 = average)

    Returns:
        Blended path data string

    Note: Paths must have the same structure (same commands in same order)
    """
    tokens1 = re.findall(r'[MLCZ]|[-+]?[0-9]*\.?[0-9]+', path1_data)
    tokens2 = re.findall(r'[MLCZ]|[-+]?[0-9]*\.?[0-9]+', path2_data)

    if len(tokens1) != len(tokens2):
        print(f"Warning: Paths have different lengths ({len(tokens1)} vs {len(tokens2)}), using first path")
        return path1_data

    result = []
    i = 0
    while i < len(tokens1):
        token1 = tokens1[i]
        token2 = tokens2[i]

        # Commands should match
        if token1 in ['M', 'L', 'C', 'Z']:
            if token1 != token2:
                print(f"Warning: Command mismatch at position {i} ({token1} vs {token2}), using first path")
                return path1_data
            result.append(token1)
            i += 1
        else:
            # Numeric value - blend it
            try:
                val1 = float(token1)
                val2 = float(token2)
                blended = val1 * (1 - blend_factor) + val2 * blend_factor
                result.append(f"{blended:.3f}")
                i += 1
            except ValueError:
                result.append(token1)
                i += 1

    return ' '.join(result)


def create_u_smile_path(bbox: Tuple[float, float, float, float]) -> str:
    """
    Create a U-shaped smile path within given bounding box.

    Args:
        bbox: (min_x, min_y, max_x, max_y)

    Returns:
        SVG path data for U-shaped smile
    """
    min_x, min_y, max_x, max_y = bbox
    width = max_x - min_x
    height = max_y - min_y

    # Create a U-shape using cubic bezier curves
    # Start at left, curve down, then curve up to right
    cx = min_x + width / 2

    # Control the depth of the U-shape
    depth = height * 0.7

    path = (
        f"M {min_x} {min_y} "
        f"C {min_x} {min_y + depth * 0.5}, "
        f"{cx - width * 0.25} {min_y + depth}, "
        f"{cx} {min_y + depth} "
        f"C {cx + width * 0.25} {min_y + depth}, "
        f"{max_x} {min_y + depth * 0.5}, "
        f"{max_x} {min_y}"
    )

    return path


def create_o_shape_path(bbox: Tuple[float, float, float, float]) -> str:
    """
    Create an O-shaped (ellipse) path within given bounding box.

    Args:
        bbox: (min_x, min_y, max_x, max_y)

    Returns:
        SVG path data for O-shape
    """
    min_x, min_y, max_x, max_y = bbox
    width = max_x - min_x
    height = max_y - min_y

    cx = min_x + width / 2
    cy = min_y + height / 2
    rx = width / 2
    ry = height / 2

    # Create ellipse using cubic bezier approximation
    # Magic number for bezier circle approximation: 0.5522847498
    k = 0.5522847498

    path = (
        f"M {cx - rx} {cy} "
        f"C {cx - rx} {cy - ry * k}, {cx - rx * k} {cy - ry}, {cx} {cy - ry} "
        f"C {cx + rx * k} {cy - ry}, {cx + rx} {cy - ry * k}, {cx + rx} {cy} "
        f"C {cx + rx} {cy + ry * k}, {cx + rx * k} {cy + ry}, {cx} {cy + ry} "
        f"C {cx - rx * k} {cy + ry}, {cx - rx} {cy + ry * k}, {cx - rx} {cy} "
        f"Z"
    )

    return path


def morph_to_u_smile(root: ET.Element, blend_factor: float = 0.5) -> ET.Element:
    """
    Morph mouth path into a U-shaped smile by transforming Y coordinates.
    Preserves original path structure.

    Args:
        root: SVG root element
        blend_factor: How much to morph (0.0 = original, 1.0 = full U, 0.5 = halfway)

    Returns:
        Modified root element
    """
    paths = [elem for elem in root.iter() if elem.tag.endswith('path')]

    for path in paths:
        path_data = path.get('d', '')
        if not path_data:
            continue

        bbox = parse_path_bbox(path_data)
        min_x, min_y, max_x, max_y = bbox
        width = max_x - min_x
        height = max_y - min_y
        cx = min_x + width / 2

        # Parse path tokens
        tokens = re.findall(r'[MLCVHZ]|[-+]?[0-9]*\.?[0-9]+', path_data)
        result = []

        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token in ['M', 'L']:
                result.append(token)
                if i + 2 < len(tokens):
                    x = float(tokens[i + 1])
                    y = float(tokens[i + 2])

                    # Calculate target Y for U-shape
                    # Distance from center: 0 at center, 1 at edges
                    dist_from_center = abs(x - cx) / (width / 2) if width > 0 else 0
                    # U-shape: low in center, high at edges (gentler curve with 0.5 multiplier)
                    u_offset = (1 - dist_from_center) * height * 0.5
                    target_y = min_y + u_offset

                    # Blend original and target
                    new_y = y * (1 - blend_factor) + target_y * blend_factor

                    result.append(tokens[i + 1])
                    result.append(f"{new_y:.3f}")
                    i += 3
                else:
                    i += 1

            elif token == 'C':
                result.append(token)
                if i + 6 < len(tokens):
                    # Process all 3 coordinate pairs in bezier
                    for j in range(1, 7, 2):
                        x = float(tokens[i + j])
                        y = float(tokens[i + j + 1])

                        dist_from_center = abs(x - cx) / (width / 2) if width > 0 else 0
                        u_offset = (1 - dist_from_center) * height * 0.5
                        target_y = min_y + u_offset
                        new_y = y * (1 - blend_factor) + target_y * blend_factor

                        result.append(tokens[i + j])
                        result.append(f"{new_y:.3f}")
                    i += 7
                else:
                    i += 1

            elif token in ['V', 'H', 'Z']:
                result.append(token)
                if token == 'V' and i + 1 < len(tokens):
                    # Vertical line - just pass through for now
                    result.append(tokens[i + 1])
                    i += 2
                elif token == 'H' and i + 1 < len(tokens):
                    result.append(tokens[i + 1])
                    i += 2
                else:
                    i += 1
            else:
                result.append(token)
                i += 1

        path.set('d', ' '.join(result))

    return root


def morph_to_o_shape(root: ET.Element, blend_factor: float = 0.5) -> ET.Element:
    """
    Morph mouth path into an O-shape by transforming coordinates.
    Preserves original path structure.

    Args:
        root: SVG root element
        blend_factor: How much to morph (0.0 = original, 1.0 = full O, 0.5 = halfway)

    Returns:
        Modified root element
    """
    paths = [elem for elem in root.iter() if elem.tag.endswith('path')]

    for path in paths:
        path_data = path.get('d', '')
        if not path_data:
            continue

        bbox = parse_path_bbox(path_data)
        min_x, min_y, max_x, max_y = bbox
        width = max_x - min_x
        height = max_y - min_y
        cx = min_x + width / 2
        cy = min_y + height / 2

        # Parse path tokens
        tokens = re.findall(r'[MLCVHZ]|[-+]?[0-9]*\.?[0-9]+', path_data)
        result = []

        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token in ['M', 'L']:
                result.append(token)
                if i + 2 < len(tokens):
                    x = float(tokens[i + 1])
                    y = float(tokens[i + 2])

                    # Map to ellipse: calculate angle and radius
                    dx = x - cx
                    dy = y - cy
                    angle = 0 if width == 0 else dx / (width / 2)  # Normalized -1 to 1
                    # Target position on ellipse
                    import math
                    theta = math.acos(max(-1, min(1, angle)))  # Clamp to [-1, 1]
                    if dy < 0:
                        theta = -theta

                    rx = width / 2
                    ry = height / 2
                    target_x = cx + rx * math.cos(theta)
                    target_y = cy + ry * math.sin(theta)

                    # Blend original and target
                    new_x = x * (1 - blend_factor) + target_x * blend_factor
                    new_y = y * (1 - blend_factor) + target_y * blend_factor

                    result.append(f"{new_x:.3f}")
                    result.append(f"{new_y:.3f}")
                    i += 3
                else:
                    i += 1

            elif token == 'C':
                result.append(token)
                if i + 6 < len(tokens):
                    # Process all 3 coordinate pairs in bezier
                    for j in range(1, 7, 2):
                        x = float(tokens[i + j])
                        y = float(tokens[i + j + 1])

                        dx = x - cx
                        dy = y - cy
                        angle = 0 if width == 0 else dx / (width / 2)
                        import math
                        theta = math.acos(max(-1, min(1, angle)))
                        if dy < 0:
                            theta = -theta

                        rx = width / 2
                        ry = height / 2
                        target_x = cx + rx * math.cos(theta)
                        target_y = cy + ry * math.sin(theta)

                        new_x = x * (1 - blend_factor) + target_x * blend_factor
                        new_y = y * (1 - blend_factor) + target_y * blend_factor

                        result.append(f"{new_x:.3f}")
                        result.append(f"{new_y:.3f}")
                    i += 7
                else:
                    i += 1

            elif token in ['V', 'H', 'Z']:
                result.append(token)
                if token == 'V' and i + 1 < len(tokens):
                    result.append(tokens[i + 1])
                    i += 2
                elif token == 'H' and i + 1 < len(tokens):
                    result.append(tokens[i + 1])
                    i += 2
                else:
                    i += 1
            else:
                result.append(token)
                i += 1

        path.set('d', ' '.join(result))

    return root


def morph_to_vowel_a(root: ET.Element, blend_factor: float = 0.5) -> ET.Element:
    """
    Morph mouth into vowel 'A' shape - wide vertical oval.
    Stretches Y coordinates vertically while keeping horizontal spread.
    """
    paths = [elem for elem in root.iter() if elem.tag.endswith('path')]

    for path in paths:
        path_data = path.get('d', '')
        if not path_data:
            continue

        bbox = parse_path_bbox(path_data)
        min_x, min_y, max_x, max_y = bbox
        width = max_x - min_x
        height = max_y - min_y
        cy = min_y + height / 2

        tokens = re.findall(r'[MLCVHZ]|[-+]?[0-9]*\.?[0-9]+', path_data)
        result = []

        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token in ['M', 'L']:
                result.append(token)
                if i + 2 < len(tokens):
                    x = float(tokens[i + 1])
                    y = float(tokens[i + 2])

                    # Stretch Y away from center
                    dy = y - cy
                    target_y = cy + dy * 2.0  # 2x vertical stretch
                    new_y = y * (1 - blend_factor) + target_y * blend_factor

                    result.append(tokens[i + 1])
                    result.append(f"{new_y:.3f}")
                    i += 3
                else:
                    i += 1

            elif token == 'C':
                result.append(token)
                if i + 6 < len(tokens):
                    for j in range(1, 7, 2):
                        x = float(tokens[i + j])
                        y = float(tokens[i + j + 1])

                        dy = y - cy
                        target_y = cy + dy * 2.0
                        new_y = y * (1 - blend_factor) + target_y * blend_factor

                        result.append(tokens[i + j])
                        result.append(f"{new_y:.3f}")
                    i += 7
                else:
                    i += 1

            elif token in ['V', 'H', 'Z']:
                result.append(token)
                if token == 'V' and i + 1 < len(tokens):
                    result.append(tokens[i + 1])
                    i += 2
                elif token == 'H' and i + 1 < len(tokens):
                    result.append(tokens[i + 1])
                    i += 2
                else:
                    i += 1
            else:
                result.append(token)
                i += 1

        path.set('d', ' '.join(result))

    return root


def morph_to_vowel_e(root: ET.Element, blend_factor: float = 0.5) -> ET.Element:
    """
    Morph mouth into vowel 'E' shape - wide horizontal shape.
    Flattens Y coordinates toward center while keeping horizontal spread.
    """
    paths = [elem for elem in root.iter() if elem.tag.endswith('path')]

    for path in paths:
        path_data = path.get('d', '')
        if not path_data:
            continue

        bbox = parse_path_bbox(path_data)
        min_x, min_y, max_x, max_y = bbox
        height = max_y - min_y
        cy = min_y + height / 2

        tokens = re.findall(r'[MLCVHZ]|[-+]?[0-9]*\.?[0-9]+', path_data)
        result = []

        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token in ['M', 'L']:
                result.append(token)
                if i + 2 < len(tokens):
                    x = float(tokens[i + 1])
                    y = float(tokens[i + 2])

                    # Flatten toward center (reduce Y variation)
                    target_y = cy + (y - cy) * 0.3
                    new_y = y * (1 - blend_factor) + target_y * blend_factor

                    result.append(tokens[i + 1])
                    result.append(f"{new_y:.3f}")
                    i += 3
                else:
                    i += 1

            elif token == 'C':
                result.append(token)
                if i + 6 < len(tokens):
                    for j in range(1, 7, 2):
                        x = float(tokens[i + j])
                        y = float(tokens[i + j + 1])

                        target_y = cy + (y - cy) * 0.3
                        new_y = y * (1 - blend_factor) + target_y * blend_factor

                        result.append(tokens[i + j])
                        result.append(f"{new_y:.3f}")
                    i += 7
                else:
                    i += 1

            elif token in ['V', 'H', 'Z']:
                result.append(token)
                if token == 'V' and i + 1 < len(tokens):
                    result.append(tokens[i + 1])
                    i += 2
                elif token == 'H' and i + 1 < len(tokens):
                    result.append(tokens[i + 1])
                    i += 2
                else:
                    i += 1
            else:
                result.append(token)
                i += 1

        path.set('d', ' '.join(result))

    return root


def morph_to_vowel_i(root: ET.Element, blend_factor: float = 0.5) -> ET.Element:
    """
    Morph mouth into vowel 'I' shape - narrow horizontal slit.
    Strongly flattens Y coordinates and narrows X.
    """
    paths = [elem for elem in root.iter() if elem.tag.endswith('path')]

    for path in paths:
        path_data = path.get('d', '')
        if not path_data:
            continue

        bbox = parse_path_bbox(path_data)
        min_x, min_y, max_x, max_y = bbox
        width = max_x - min_x
        height = max_y - min_y
        cx = min_x + width / 2
        cy = min_y + height / 2

        tokens = re.findall(r'[MLCVHZ]|[-+]?[0-9]*\.?[0-9]+', path_data)
        result = []

        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token in ['M', 'L']:
                result.append(token)
                if i + 2 < len(tokens):
                    x = float(tokens[i + 1])
                    y = float(tokens[i + 2])

                    # Narrow horizontally and flatten vertically
                    target_x = cx + (x - cx) * 0.8
                    target_y = cy + (y - cy) * 0.15
                    new_x = x * (1 - blend_factor) + target_x * blend_factor
                    new_y = y * (1 - blend_factor) + target_y * blend_factor

                    result.append(f"{new_x:.3f}")
                    result.append(f"{new_y:.3f}")
                    i += 3
                else:
                    i += 1

            elif token == 'C':
                result.append(token)
                if i + 6 < len(tokens):
                    for j in range(1, 7, 2):
                        x = float(tokens[i + j])
                        y = float(tokens[i + j + 1])

                        target_x = cx + (x - cx) * 0.8
                        target_y = cy + (y - cy) * 0.15
                        new_x = x * (1 - blend_factor) + target_x * blend_factor
                        new_y = y * (1 - blend_factor) + target_y * blend_factor

                        result.append(f"{new_x:.3f}")
                        result.append(f"{new_y:.3f}")
                    i += 7
                else:
                    i += 1

            elif token in ['V', 'H', 'Z']:
                result.append(token)
                if token == 'V' and i + 1 < len(tokens):
                    result.append(tokens[i + 1])
                    i += 2
                elif token == 'H' and i + 1 < len(tokens):
                    result.append(tokens[i + 1])
                    i += 2
                else:
                    i += 1
            else:
                result.append(token)
                i += 1

        path.set('d', ' '.join(result))

    return root


def morph_to_vowel_u(root: ET.Element, blend_factor: float = 0.5) -> ET.Element:
    """
    Morph mouth into vowel 'U' shape - small round pout.
    Similar to O but smaller and more centered.
    """
    paths = [elem for elem in root.iter() if elem.tag.endswith('path')]

    for path in paths:
        path_data = path.get('d', '')
        if not path_data:
            continue

        bbox = parse_path_bbox(path_data)
        min_x, min_y, max_x, max_y = bbox
        width = max_x - min_x
        height = max_y - min_y
        cx = min_x + width / 2
        cy = min_y + height / 2

        tokens = re.findall(r'[MLCVHZ]|[-+]?[0-9]*\.?[0-9]+', path_data)
        result = []

        i = 0
        while i < len(tokens):
            token = tokens[i]

            if token in ['M', 'L']:
                result.append(token)
                if i + 2 < len(tokens):
                    x = float(tokens[i + 1])
                    y = float(tokens[i + 2])

                    # Map to smaller ellipse
                    dx = x - cx
                    dy = y - cy
                    angle = 0 if width == 0 else dx / (width / 2)
                    import math
                    theta = math.acos(max(-1, min(1, angle)))
                    if dy < 0:
                        theta = -theta

                    # Smaller radius for U (small pout)
                    rx = width / 2 * 0.35
                    ry = height / 2 * 0.35
                    target_x = cx + rx * math.cos(theta)
                    target_y = cy + ry * math.sin(theta)

                    new_x = x * (1 - blend_factor) + target_x * blend_factor
                    new_y = y * (1 - blend_factor) + target_y * blend_factor

                    result.append(f"{new_x:.3f}")
                    result.append(f"{new_y:.3f}")
                    i += 3
                else:
                    i += 1

            elif token == 'C':
                result.append(token)
                if i + 6 < len(tokens):
                    for j in range(1, 7, 2):
                        x = float(tokens[i + j])
                        y = float(tokens[i + j + 1])

                        dx = x - cx
                        dy = y - cy
                        angle = 0 if width == 0 else dx / (width / 2)
                        import math
                        theta = math.acos(max(-1, min(1, angle)))
                        if dy < 0:
                            theta = -theta

                        rx = width / 2 * 0.35
                        ry = height / 2 * 0.35
                        target_x = cx + rx * math.cos(theta)
                        target_y = cy + ry * math.sin(theta)

                        new_x = x * (1 - blend_factor) + target_x * blend_factor
                        new_y = y * (1 - blend_factor) + target_y * blend_factor

                        result.append(f"{new_x:.3f}")
                        result.append(f"{new_y:.3f}")
                    i += 7
                else:
                    i += 1

            elif token in ['V', 'H', 'Z']:
                result.append(token)
                if token == 'V' and i + 1 < len(tokens):
                    result.append(tokens[i + 1])
                    i += 2
                elif token == 'H' and i + 1 < len(tokens):
                    result.append(tokens[i + 1])
                    i += 2
                else:
                    i += 1
            else:
                result.append(token)
                i += 1

        path.set('d', ' '.join(result))

    return root


def blend_mouth_with_shape(root: ET.Element, shape_type: str, blend_factor: float = 0.5) -> ET.Element:
    """
    Morph mouth path into a reference shape.
    Uses path morphing to preserve original structure.

    Args:
        root: SVG root element
        shape_type: "u_smile", "o_shape", "vowel_a", "vowel_e", "vowel_i", "vowel_o", "vowel_u"
        blend_factor: How much to morph (0.0 = original, 1.0 = shape, 0.5 = halfway)

    Returns:
        Modified root element
    """
    if shape_type == "u_smile":
        return morph_to_u_smile(root, blend_factor)
    elif shape_type == "o_shape":
        return morph_to_o_shape(root, blend_factor)
    elif shape_type == "vowel_a":
        return morph_to_vowel_a(root, blend_factor)
    elif shape_type == "vowel_e":
        return morph_to_vowel_e(root, blend_factor)
    elif shape_type == "vowel_i":
        return morph_to_vowel_i(root, blend_factor)
    elif shape_type == "vowel_o":
        return morph_to_o_shape(root, blend_factor)  # O-shape is same as vowel O
    elif shape_type == "vowel_u":
        return morph_to_vowel_u(root, blend_factor)
    else:
        print(f"Warning: Unknown shape type '{shape_type}'")
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
            - scale_pupils: scale factor for pupils only
            - clip_top_half: if True, clip top half of eyes
            - clip_angled: if True, clip eyes with angled cuts for angry look
            - flip_mouth: if True, flip mouth vertically (upside down)
            - flatten_mouth: float 0.0-1.0, flatten mouth toward horizontal line
            - mirror_mouth: if True, duplicate and flip mouth to create round O-shape
            - rotate_mouth: rotation in degrees (for sad/happy mouths)
            - scale_mouth: tuple (scale_x, scale_y) for mouth scaling

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

        if 'scale_pupils' in transform_config:
            scale_pupils_only(root, transform_config['scale_pupils'])

        if 'clip_top_half' in transform_config and transform_config['clip_top_half']:
            clip_top_half_of_eyes(root)

        if 'clip_angled' in transform_config and transform_config['clip_angled']:
            clip_eyes_angled(root)

        # Apply mouth transformations
        if 'blend_mouth' in transform_config:
            shape_type, blend_factor = transform_config['blend_mouth']
            blend_mouth_with_shape(root, shape_type, blend_factor)

        if 'flip_mouth' in transform_config and transform_config['flip_mouth']:
            flip_mouth_vertically(root)

        if 'flatten_mouth' in transform_config:
            flatten_mouth(root, transform_config['flatten_mouth'])

        if 'mirror_mouth' in transform_config and transform_config['mirror_mouth']:
            mirror_mouth_to_round(root)

        if 'rotate_mouth' in transform_config:
            rotate_mouth(root, transform_config['rotate_mouth'])

        if 'scale_mouth' in transform_config:
            scale_x, scale_y = transform_config['scale_mouth']
            scale_mouth(root, scale_x, scale_y)

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
        "eyes_open": {"pupil_position": "upper_third"},  # 1/3 down = 33% (pupils at top, looking up, joyful)
        "mouths_open": {"blend_mouth": ("u_smile", 0.3)},  # Blend base mouth with U-shaped smile (30% morph)
    },
    "sad": {
        "eyes_open": {"pupil_position": "lower_third"},  # 2/3 down = 67% (pupils at bottom, looking down, sad)
        "mouths_closed": {"flip_mouth": True}  # Flip vertically for frown
    },
    "surprised": {
        "eyes_open": {"scale_pupils": 1.5},  # Bigger pupils (size scaling happens at render time in door_agents.py)
        "mouths_open": {"blend_mouth": ("o_shape", 0.7), "scale_mouth": (1.3, 1.3)},  # Blend with O-shape (70%) + 30% bigger
    },
    "angry": {
        "eyes_open": {"clip_angled": True, "pupil_position": "center", "scale_pupils": 1.3},  # V-shape + centered + 30% bigger pupils
        "mouths_closed": {"flip_mouth": True, "scale_mouth": (0.75, 0.75)}  # Flipped vertically + smaller (25% smaller)
    },
    "bored": {
        "eyes_open": {"clip_top_half": True},  # Clip top half for half-lidded look
        "mouths_closed": {"flatten_mouth": 0.5}  # Flatten halfway toward horizontal line
    },
    "vowel_a": {
        "mouths_open": {"blend_mouth": ("vowel_a", 0.6)}  # Wide vertical oval
    },
    "vowel_e": {
        "mouths_open": {"blend_mouth": ("vowel_e", 0.7)}  # Wide horizontal
    },
    "vowel_i": {
        "mouths_open": {"blend_mouth": ("vowel_i", 0.8)}  # Narrow slit
    },
    "vowel_o": {
        "mouths_open": {"blend_mouth": ("vowel_o", 0.7)}  # Round O
    },
    "vowel_u": {
        "mouths_open": {"blend_mouth": ("vowel_u", 0.7)}  # Small pout
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

        # Process open eyes (if this emote has open eye transforms)
        if "eyes_open" in transforms and EYES_OPEN_DIR.exists():
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

        # Process closed eyes (if this emote has closed eye transforms)
        if "eyes_closed" in transforms and EYES_CLOSED_DIR.exists():
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

        # Process open mouths (if this emote has open mouth transforms)
        if "mouths_open" in transforms and MOUTHS_OPEN_DIR.exists():
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

        # Process closed mouths (if this emote has closed mouth transforms)
        if "mouths_closed" in transforms and MOUTHS_CLOSED_DIR.exists():
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
    print("Emote variant generation complete!")
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
