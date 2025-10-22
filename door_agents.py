#!/usr/bin/env python3
# ABOUTME: Door agent avatar generation system
# ABOUTME: v2.0 with separate open/closed eye and mouth states for emote animations

"""
Door Agent Avatar Generation System v2.0

# Breaking Changes in v2.0

## What Changed
- Avatar generation now uses 4 separate indices for eyes/mouths instead of 2
  - v1.x: Used single eye_index and mouth_index
  - v2.0: Uses open_eye_index, closed_eye_index, open_mouth_index, closed_mouth_index
- Hash byte allocation changed to accommodate 4 indices:
  - Bytes [0-3]: Now allocated to 4 eye/mouth indices (was [0-1] in v1.x)
  - Bytes [4-10]: Hair and other attributes (shifted from [2-8] in v1.x)
- Emote system rewritten to control open/closed states instead of using special emote assets
- Idle animation changed from vertical breathing to horizontal sway + blink
- Asset structure changed: eyes/ and mouths/ now have open/ and closed/ subdirectories

## Impact on Existing Avatars
- All avatars generated from the same input string will look DIFFERENT in v2.0 vs v1.x
- This is due to hash byte reallocation - different bytes now control different features
- No automated migration path exists - v2.0 is a fresh start
- Avatar determinism IS preserved: same input = same avatar within v2.0

## Hash Byte Allocation (v2.0)
Byte [0]: open_eye_index - selects which open eye asset to use
Byte [1]: closed_eye_index - selects which closed eye asset to use
Byte [2]: open_mouth_index - selects which open mouth asset to use
Byte [3]: closed_mouth_index - selects which closed mouth asset to use
Byte [4]: hair_selection - presence and style of hair
Byte [5]: body_shape - width x height dimensions
Byte [6]: body_color - primary fill color
Byte [7]: node_color - side node fill color
Byte [8]: feet_match_body - boolean for feet color
Byte [9]: hair_color - used for deterministic hair color selection

## Why This Breaking Change?
The v2.0 emote system needed independent control over eye and mouth states
(open/closed) to support animations like blinking, talking, and expressive emotes.
The v1.x design used numbered assets where some were "rest" and some were "excited",
which didn't provide sufficient flexibility for animation control.

## Upgrade Path
There is no upgrade path to maintain visual consistency. If you need to preserve
existing avatar appearances, continue using v1.x. For new deployments, v2.0
provides significantly better animation capabilities.
"""

import os, random, re, xml.etree.ElementTree as ET, json, hashlib
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Union

AVATAR_SYSTEM_VERSION = "2.0"

class DoorAgentConfig:
    """Handles loading and managing all door agent configuration and assets.

    Part of Avatar System v2.0 - uses separate open/closed eye and mouth assets
    for flexible animation control.
    """
    
    def __init__(self, assets_path: Path = Path("assets")):
        self.assets_path = assets_path
        self._load_configs()
        self._load_assets()
    
    def _load_configs(self):
        """Load all JSON configuration files."""
        with open(self.assets_path / "config.json") as f:
            config = json.load(f)
        with open(self.assets_path / "colors.json") as f:
            colors = json.load(f)
        with open(self.assets_path / "body_shapes.json") as f:
            body_shapes = json.load(f)
        with open(self.assets_path / "probabilities.json") as f:
            probabilities = json.load(f)

        # Extract configuration values
        self.CELL = config["grid"]["cell_size"]
        self.PAD = config["grid"]["padding"]
        self.BOX = self.CELL - 2 * self.PAD
        self.STROKE = config["styling"]["stroke_width"]
        self.OUTLINE = config["styling"]["outline_color"]

        self.BODY_SHAPES = [(shape["width"], shape["height"]) for shape in body_shapes["shapes"]]

        self.NODE_R_FRAC = config["sizing"]["node_radius_fraction"]
        self.FOOT_H_FRAC = config["sizing"]["foot_height_fraction"]

        self.EYE_Y_FRAC = config["positioning"]["eye_y_fraction"]
        self.MOUTH_Y_FRAC = config["positioning"]["mouth_y_fraction"]
        self.NODE_Y_FRAC = config["positioning"]["node_y_fraction"]

        self.EYES_W_FRAC = config["sizing"]["eyes_width_fraction"]
        self.MOUTH_W_REST = config["sizing"]["mouth_width_rest"]
        self.MOUTH_W_EXC = config["sizing"]["mouth_width_excited"]

        self.PALETTE = colors["palette"]

        self.ROWS = config["grid"]["rows"]
        self.COLS = config["grid"]["cols"]

        # Probability settings
        self.EXCITED_CHANCE = probabilities["excited_chance"]
        self.FEET_MATCH_BODY_CHANCE = probabilities["feet_match_body_chance"]
        self.REST_RANGE = probabilities["mouth_indices"]["rest_range"]
        self.EXC_RANGE = probabilities["mouth_indices"]["excited_range"]

        # Constraint settings
        self.EYE_MAX_HEIGHT_FRAC = config["positioning"]["eye_max_height_fraction"]
        self.MOUTH_MAX_HEIGHT_FRAC = config["positioning"]["mouth_max_height_fraction"]

    def _parse_defs(self, folder: Path) -> List[Tuple]:
        """Parse SVG definitions from a folder, returning sorted list of asset data.
        Only processes files with numeric names (e.g., 1.svg, 2.svg)."""
        defs = []
        # Filter for numeric filenames only
        numeric_files = [f for f in folder.glob("*.svg") if f.stem.isdigit()]
        for f in sorted(numeric_files, key=lambda p: int(p.stem)):
            root = ET.parse(f).getroot()
            x0, y0, w, h = map(float, root.get("viewBox").split())
            content = "".join(ET.tostring(c, encoding="unicode") for c in root)
            z_order = root.get("data-z-order", "behind")
            width_percent = float(root.get("data-width-percent", 100))
            position_x = root.get("data-position-x", "body-center")
            position_y = root.get("data-position-y", "above-body")
            anchor = root.get("data-anchor", "top")
            color_spec = root.get("data-color", "currentColor")
            defs.append((x0, y0, w, h, content, z_order, width_percent, position_x, position_y, anchor, color_spec))
        return defs

    def _parse_named_defs(self, folder: Path, pattern: str = "*.svg") -> Dict[str, Tuple]:
        """Parse SVG definitions from a folder, returning dict keyed by filename stem."""
        defs = {}
        for f in folder.glob(pattern):
            root = ET.parse(f).getroot()
            x0, y0, w, h = map(float, root.get("viewBox").split())
            content = "".join(ET.tostring(c, encoding="unicode") for c in root)
            # Use filename stem as key (e.g., "emote_happy" from "emote_happy.svg")
            defs[f.stem] = (x0, y0, w, h, content)
        return defs

    def _load_emote_variants(self, folder: Path) -> Dict[str, List[Tuple]]:
        """Load emote variant SVGs organized by emote name.

        Returns dict: {"happy": [variant1, variant2, ...], "sad": [...], ...}
        Each variant corresponds to a base asset index.
        """
        variants = {}
        for emote in ["happy", "sad", "surprised", "angry", "bored", "vowel_a", "vowel_e", "vowel_i", "vowel_o", "vowel_u"]:
            variants[emote] = []
            # Find all files matching emote_{emote}_*.svg pattern
            pattern = f"emote_{emote}_*.svg"
            files = sorted(folder.glob(pattern), key=lambda p: int(p.stem.split('_')[-1]))
            for f in files:
                root = ET.parse(f).getroot()
                x0, y0, w, h = map(float, root.get("viewBox").split())
                content = "".join(ET.tostring(c, encoding="unicode") for c in root)
                # Add minimal tuple (don't need positioning data for emote variants)
                variants[emote].append((x0, y0, w, h, content))
        return variants

    def _load_assets(self):
        """Load all SVG assets from open/closed subdirectories."""
        # Load numbered assets from open/closed subdirectories
        self.open_eyes = self._parse_defs(self.assets_path / "eyes" / "open")
        self.closed_eyes = self._parse_defs(self.assets_path / "eyes" / "closed")
        self.open_mouths = self._parse_defs(self.assets_path / "mouths" / "open")
        self.closed_mouths = self._parse_defs(self.assets_path / "mouths" / "closed")

        # Load emote variants for eyes and mouths
        self.open_eye_emotes = self._load_emote_variants(self.assets_path / "eyes" / "open")
        self.closed_eye_emotes = self._load_emote_variants(self.assets_path / "eyes" / "closed")
        self.open_mouth_emotes = self._load_emote_variants(self.assets_path / "mouths" / "open")
        self.closed_mouth_emotes = self._load_emote_variants(self.assets_path / "mouths" / "closed")

        # Keep legacy attributes for backward compatibility (combine open + closed)
        self.EYES = self.open_eyes + self.closed_eyes
        self.MOUTHS = self.open_mouths + self.closed_mouths

        self.HAIRS = self._parse_defs(self.assets_path / "hair")

        # Load emote/animation assets from parent directories
        eyes_path = self.assets_path / "eyes"
        mouths_path = self.assets_path / "mouths"
        eyebrows_path = self.assets_path / "eyebrows"

        self.EMOTE_EYES = self._parse_named_defs(eyes_path, "emote_*.svg")
        self.EMOTE_MOUTHS = self._parse_named_defs(mouths_path, "emote_*.svg")
        self.VOWEL_MOUTHS = self._parse_named_defs(mouths_path, "vowel_*.svg")

        # Load eyebrows (only angry for now)
        if eyebrows_path.exists():
            self.EYEBROWS = self._parse_named_defs(eyebrows_path)
        else:
            self.EYEBROWS = {}


class DoorAgentGenerator:
    """Generates door agent SVGs with both random and deterministic modes."""

    def __init__(self, config: DoorAgentConfig):
        self.config = config

    def _generate_avatar_id(self, input_string: str) -> str:
        """Generate unique avatar ID from input string.

        Args:
            input_string: Seed string (e.g., email)

        Returns:
            Avatar ID like 'avatar-973dfe463ec8' (12-char hash)
        """
        hash_hex = hashlib.sha256(input_string.encode('utf-8')).hexdigest()
        return f"avatar-{hash_hex[:12]}"

    def _generate_body(self, shape: Tuple[int, int], body_color: str, cell_size: float, pad: float) -> str:
        """Generate body rectangle and vertical line.

        Args:
            shape: (width, height) tuple in grid units
            body_color: Hex color string
            cell_size: Size of grid cell
            pad: Padding amount

        Returns:
            SVG string for body elements
        """
        w_tiles, h_tiles = shape
        box = cell_size - 2 * pad
        foot_h_frac = self.config.FOOT_H_FRAC

        # Calculate body dimensions
        scale = (box - box * foot_h_frac) / 7
        body_w = int(w_tiles * scale)
        body_h = int(h_tiles * scale)
        foot_h = int(box * foot_h_frac)

        # Calculate body position
        bx0 = pad + (box - body_w) // 2
        by0 = pad + box - foot_h - body_h
        bx1 = bx0 + body_w
        by1 = by0 + body_h
        cx = (bx0 + bx1) / 2

        # Body rectangle
        body_rect = f'<rect x="{bx0}" y="{by0}" width="{body_w}" height="{body_h}" fill="{body_color}" stroke="{self.config.OUTLINE}" stroke-width="{self.config.STROKE}"/>'

        # Vertical line
        vert_line = f'<line x1="{cx}" y1="{by0}" x2="{cx}" y2="{by1}" stroke="{self.config.OUTLINE}" stroke-width="{self.config.STROKE}"/>'

        return body_rect + vert_line

    def _generate_nodes(self, shape: Tuple[int, int], node_color: str, cell_size: float, pad: float) -> str:
        """Generate side node circles.

        Args:
            shape: (width, height) tuple in grid units
            node_color: Hex color string
            cell_size: Size of grid cell
            pad: Padding amount

        Returns:
            SVG string for node circles
        """
        w_tiles, h_tiles = shape
        box = cell_size - 2 * pad
        foot_h_frac = self.config.FOOT_H_FRAC

        # Calculate body dimensions (same as in _generate_body)
        scale = (box - box * foot_h_frac) / 7
        body_w = int(w_tiles * scale)
        body_h = int(h_tiles * scale)
        foot_h = int(box * foot_h_frac)

        # Calculate body position
        bx0 = pad + (box - body_w) // 2
        by0 = pad + box - foot_h - body_h
        bx1 = bx0 + body_w

        # Calculate node properties
        node_r = int(body_w * self.config.NODE_R_FRAC)
        node_y = by0 + body_h * self.config.NODE_Y_FRAC
        left_node = bx0 - node_r
        right_node = bx1 + node_r

        # Generate node circles
        left_circle = f'<circle cx="{left_node}" cy="{node_y}" r="{node_r}" fill="{node_color}" stroke="{self.config.OUTLINE}" stroke-width="{self.config.STROKE}"/>'
        right_circle = f'<circle cx="{right_node}" cy="{node_y}" r="{node_r}" fill="{node_color}" stroke="{self.config.OUTLINE}" stroke-width="{self.config.STROKE}"/>'

        return left_circle + right_circle

    def _generate_feet(self, shape: Tuple[int, int], body_color: str, node_color: str,
                      feet_match_body: bool, cell_size: float, pad: float) -> str:
        """Generate foot rectangles.

        Args:
            shape: (width, height) tuple in grid units
            body_color: Hex color string
            node_color: Hex color string
            feet_match_body: If True, feet use body color; else node color
            cell_size: Size of grid cell
            pad: Padding amount

        Returns:
            SVG string for feet rectangles
        """
        w_tiles, h_tiles = shape
        box = cell_size - 2 * pad
        foot_h_frac = self.config.FOOT_H_FRAC

        # Calculate body dimensions (same as in _generate_body)
        scale = (box - box * foot_h_frac) / 7
        body_w = int(w_tiles * scale)
        body_h = int(h_tiles * scale)
        foot_h = int(box * foot_h_frac)

        # Calculate body position
        bx0 = pad + (box - body_w) // 2
        by0 = pad + box - foot_h - body_h
        bx1 = bx0 + body_w
        cx = (bx0 + bx1) / 2

        # Determine foot color
        foot_color = body_color if feet_match_body else node_color

        # Calculate foot dimensions and positions
        foot_w = int(body_w * 0.26)
        left_foot_x = cx - body_w / 4 - foot_w / 2
        right_foot_x = cx + body_w / 4 - foot_w / 2
        foot_y = pad + box - foot_h

        # Generate foot rectangles
        left_foot = f'<rect x="{left_foot_x}" y="{foot_y}" width="{foot_w}" height="{foot_h}" fill="{foot_color}" stroke="{self.config.OUTLINE}" stroke-width="{self.config.STROKE}"/>'
        right_foot = f'<rect x="{right_foot_x}" y="{foot_y}" width="{foot_w}" height="{foot_h}" fill="{foot_color}" stroke="{self.config.OUTLINE}" stroke-width="{self.config.STROKE}"/>'

        return left_foot + right_foot

    def _resolve_hair_color(self, hair_color_spec: str, body_fill: str) -> str:
        """Resolve hair color based on data-color specification."""
        if hair_color_spec == "currentColor":
            return body_fill
        elif hair_color_spec == "contrast":
            return random.choice([c for c in self.config.PALETTE if c != body_fill])
        elif hair_color_spec.startswith('[') and hair_color_spec.endswith(']'):
            try:
                color_array = json.loads(hair_color_spec)
                return random.choice(color_array)
            except (json.JSONDecodeError, ValueError):
                return body_fill
        else:
            return hair_color_spec
    
    def _resolve_hair_color_deterministic(self, hair_color_spec: str, body_fill: str, hash_byte: int) -> str:
        """Resolve hair color deterministically based on data-color specification."""
        if hair_color_spec == "currentColor":
            return body_fill
        elif hair_color_spec == "contrast":
            contrast_colors = [c for c in self.config.PALETTE if c != body_fill]
            return contrast_colors[hash_byte % len(contrast_colors)]
        elif hair_color_spec.startswith('[') and hair_color_spec.endswith(']'):
            try:
                color_array = json.loads(hair_color_spec)
                return color_array[hash_byte % len(color_array)]
            except (json.JSONDecodeError, ValueError):
                return body_fill
        else:
            return hair_color_spec

    def generate_agent_svg(self,
                          shape: Tuple[int, int],
                          open_eye_index: int,
                          closed_eye_index: int,
                          open_mouth_index: int,
                          closed_mouth_index: int,
                          hair_index: Optional[int],
                          body_color: str,
                          node_color: str,
                          feet_match_body: bool,
                          hair_color_hash_byte: int = 0,
                          eye_override: Optional[str] = None,
                          mouth_override: Optional[str] = None,
                          body_transform: str = '',
                          emote_name: Optional[str] = None,
                          eye_emote: Optional[str] = None,
                          mouth_emote: Optional[str] = None,
                          email: Optional[str] = None,
                          frame: str = "neutral") -> str:
        """Generate a single agent SVG with specified parameters.

        Animation parameters:
            eye_override: "open" or "closed" to override default eye state
            mouth_override: "open" or "closed" to override default mouth state
            body_transform: SVG transform string for body positioning (e.g., "translate(1.5, 0)")
            emote_name: Emote name for using variant assets (e.g., "happy", "sad")
            email: Email or input string for generating avatar ID (optional)
            frame: Animation frame identifier for CSS class (default: "neutral")
        """

        w_tiles, h_tiles = shape
        scale = (self.config.BOX - self.config.BOX * self.config.FOOT_H_FRAC) / 7
        body_w = int(w_tiles * scale)
        body_h = int(h_tiles * scale)
        foot_h = int(self.config.BOX * self.config.FOOT_H_FRAC)

        bx0 = self.config.PAD + (self.config.BOX - body_w) // 2
        by0 = self.config.PAD + self.config.BOX - foot_h - body_h
        bx1 = bx0 + body_w
        by1 = by0 + body_h
        cx = (bx0 + bx1) / 2

        feet_fill = body_color if feet_match_body else node_color

        # Determine which emote to use for eyes (prefer eye_emote over emote_name)
        effective_eye_emote = eye_emote if eye_emote is not None else emote_name

        # Eyes - check for emote variant first, then state override
        if effective_eye_emote and eye_override == "open" and effective_eye_emote in self.config.open_eye_emotes:
            # Use emote variant if available
            emote_variants = self.config.open_eye_emotes[effective_eye_emote]
            if open_eye_index < len(emote_variants):
                ex0, ey0, ew, eh, eyes_svg = emote_variants[open_eye_index]
            else:
                # Fallback to base if variant doesn't exist
                ex0, ey0, ew, eh, eyes_svg, _, _, _, _, _, _ = self.config.open_eyes[open_eye_index]
        elif effective_eye_emote and eye_override == "closed" and effective_eye_emote in self.config.closed_eye_emotes:
            emote_variants = self.config.closed_eye_emotes[effective_eye_emote]
            if closed_eye_index < len(emote_variants):
                ex0, ey0, ew, eh, eyes_svg = emote_variants[closed_eye_index]
            else:
                ex0, ey0, ew, eh, eyes_svg, _, _, _, _, _, _ = self.config.closed_eyes[closed_eye_index]
        elif eye_override == "closed":
            ex0, ey0, ew, eh, eyes_svg, _, _, _, _, _, _ = self.config.closed_eyes[closed_eye_index]
        elif eye_override == "open":
            ex0, ey0, ew, eh, eyes_svg, _, _, _, _, _, _ = self.config.open_eyes[open_eye_index]
        else:
            # Default to open eyes for neutral/base render
            ex0, ey0, ew, eh, eyes_svg, _, _, _, _, _, _ = self.config.open_eyes[open_eye_index]

        # Apply emote-specific size scaling
        eye_scale_multiplier = 1.0
        if emote_name == "surprised":
            eye_scale_multiplier = 1.15  # 15% bigger for surprised

        eyes_w = body_w * self.config.EYES_W_FRAC * eye_scale_multiplier
        se = eyes_w / ew
        eyes_h = eh * se
        max_eyes_h = body_h * self.config.EYE_MAX_HEIGHT_FRAC * eye_scale_multiplier  # Scale max constraint too
        if eyes_h > max_eyes_h:
            eyes_h = max_eyes_h
            se = eyes_h / eh
            eyes_w = ew * se
        eyes_x = cx - eyes_w / 2
        target_eye_center_y = by0 + body_h * self.config.EYE_Y_FRAC
        clamped_eye_center_y = max(by0 + eyes_h / 2, min(by1 - eyes_h / 2, target_eye_center_y))
        eyes_y = clamped_eye_center_y - eyes_h / 2

        # Determine which emote to use for mouth (prefer mouth_emote over emote_name)
        effective_mouth_emote = mouth_emote if mouth_emote is not None else emote_name

        # Mouth - check for emote variant first, then state override
        if effective_mouth_emote and mouth_override == "open" and effective_mouth_emote in self.config.open_mouth_emotes:
            # Use emote variant if available
            emote_variants = self.config.open_mouth_emotes[effective_mouth_emote]
            if open_mouth_index < len(emote_variants):
                mx0, my0, mw, mh, mouth_svg = emote_variants[open_mouth_index]
            else:
                # Fallback to base if variant doesn't exist
                mx0, my0, mw, mh, mouth_svg, _, _, _, _, _, _ = self.config.open_mouths[open_mouth_index]
        elif effective_mouth_emote and mouth_override == "closed" and effective_mouth_emote in self.config.closed_mouth_emotes:
            emote_variants = self.config.closed_mouth_emotes[effective_mouth_emote]
            if closed_mouth_index < len(emote_variants):
                mx0, my0, mw, mh, mouth_svg = emote_variants[closed_mouth_index]
            else:
                mx0, my0, mw, mh, mouth_svg, _, _, _, _, _, _ = self.config.closed_mouths[closed_mouth_index]
        elif mouth_override == "closed":
            mx0, my0, mw, mh, mouth_svg, _, _, _, _, _, _ = self.config.closed_mouths[closed_mouth_index]
        elif mouth_override == "open":
            mx0, my0, mw, mh, mouth_svg, _, _, _, _, _, _ = self.config.open_mouths[open_mouth_index]
        else:
            # Default to open mouths for neutral/base render
            mx0, my0, mw, mh, mouth_svg, _, _, _, _, _, _ = self.config.open_mouths[open_mouth_index]
        # Determine if this is an excited mouth (index in upper half)
        excited = open_mouth_index >= len(self.config.open_mouths) // 2
        mw_ratio = self.config.MOUTH_W_EXC if excited else self.config.MOUTH_W_REST
        mouth_w = body_w * mw_ratio
        sm = mouth_w / mw
        mouth_h = mh * sm
        max_mouth_h = body_h * self.config.MOUTH_MAX_HEIGHT_FRAC
        if mouth_h > max_mouth_h:
            mouth_h = max_mouth_h
            sm = mouth_h / mh
            mouth_w = mw * sm
        mouth_x = cx - mouth_w / 2
        # Position mouth at fixed fraction below eye center (not dependent on eye height)
        target_mouth_center_y = by0 + body_h * self.config.MOUTH_Y_FRAC
        clamped_mouth_center_y = max(by0 + mouth_h / 2, min(by1 - mouth_h / 2, target_mouth_center_y))
        mouth_y = clamped_mouth_center_y - mouth_h / 2

        g = []

        # Hair rendering
        hair_element = None
        if hair_index is not None:
            hx0, hy0, hw, hh, hair_svg, hair_z_order, hair_width_percent, hair_position_x, hair_position_y, hair_anchor, hair_color_spec = self.config.HAIRS[hair_index]

            # Calculate hair dimensions and position (same logic as original)
            hair_w = body_w * (hair_width_percent / 100)
            sh = hair_w / hw
            hair_h = hh * sh

            # Calculate hair X position
            if hair_position_x == "cell-center":
                hair_x = self.config.PAD + self.config.BOX / 2 - hair_w / 2
            elif hair_position_x.endswith("%"):
                percent = float(hair_position_x[:-1]) / 100
                hair_x = cx + (hair_w * percent) - hair_w / 2
            else:
                hair_x = cx - hair_w / 2

            # Calculate hair Y position
            if hair_position_y == "between-body-eyes":
                base_y = (by0 + eyes_y) / 2
            elif hair_position_y == "eyes":
                base_y = clamped_eye_center_y
            elif hair_position_y.endswith("%"):
                percent = float(hair_position_y[:-1]) / 100
                base_y = by0 + (hair_h * percent)
            else:
                base_y = by0

            # Apply anchor offset
            if hair_anchor == "bottom":
                hair_y = base_y - hair_h
            elif hair_anchor == "center":
                hair_y = base_y - hair_h / 2
            else:
                hair_y = base_y

            # Resolve hair color (deterministic or random based on context)
            if hair_color_hash_byte > 0:
                hair_color = self._resolve_hair_color_deterministic(hair_color_spec, body_color, hair_color_hash_byte)
            else:
                hair_color = self._resolve_hair_color(hair_color_spec, body_color)

            hair_element = f'<g color="{hair_color}" transform="translate({hair_x},{hair_y}) scale({sh}) translate({-hx0}, {-hy0})">{hair_svg}</g>'

            if hair_z_order == "behind":
                g.append(hair_element)

        # Wrap body, nodes, feet, eyes, and mouth in a transform group if body_transform is specified
        if body_transform:
            g.append(f'<g transform="{body_transform}">')

        # Body and core elements
        body_svg = self._generate_body(shape, body_color, self.config.CELL, self.config.PAD)
        g.append(body_svg)

        # Nodes
        nodes_svg = self._generate_nodes(shape, node_color, self.config.CELL, self.config.PAD)
        g.append(nodes_svg)

        # Feet
        feet_svg = self._generate_feet(shape, body_color, node_color, feet_match_body, self.config.CELL, self.config.PAD)
        g.append(feet_svg)

        # Eyes
        g.append(f'<g transform="translate({eyes_x},{eyes_y}) scale({se}) '
                 f'translate({-ex0}, {-ey0})">{eyes_svg}</g>')

        # Mouth
        g.append(f'<g transform="translate({mouth_x},{mouth_y}) scale({sm}) '
                 f'translate({-mx0}, {-my0})">{mouth_svg}</g>')

        # Close body transform group if needed
        if body_transform:
            g.append('</g>')

        # Hair in front
        if hair_element and hair_index is not None:
            _, _, _, _, _, hair_z_order, _, _, _, _, _ = self.config.HAIRS[hair_index]
            if hair_z_order == "front":
                g.append(hair_element)

        # Generate avatar ID and wrap in SVG tag
        avatar_id = self._generate_avatar_id(email) if email else "avatar-default"
        svg_content = "".join(g)

        return (f'<svg id="{avatar_id}" class="agent {frame}" '
                f'width="{self.config.CELL}" height="{self.config.CELL}" '
                f'viewBox="0 0 {self.config.CELL} {self.config.CELL}" '
                f'xmlns="http://www.w3.org/2000/svg">'
                f'{svg_content}</svg>')

    def _get_frame_modifications(self, frame: str, hash_bytes: bytes) -> Dict:
        """Get frame-specific modifications for animation.

        New system uses open/closed eye and mouth states with horizontal body sway.

        Args:
            frame: Frame identifier (e.g., "neutral", "idle_0", "happy", "vowel_A")
            hash_bytes: SHA-256 hash bytes for deterministic variations

        Returns:
            Dict with keys: eye_override, mouth_override, body_transform, emote_name
        """
        modifications = {
            'eye_override': None,      # "open", "closed", or None (use agent default)
            'mouth_override': None,    # "open", "closed", or None (use agent default)
            'body_transform': '',      # SVG transform string for body positioning
            'emote_name': None,        # Emote name for variant selection (e.g., "happy", "sad")
            'eye_emote': None,         # Separate emote for eyes only
            'mouth_emote': None        # Separate emote for mouth only
        }

        # Neutral frame - no modifications
        if frame == "neutral":
            return modifications

        # Idle animation frames (10-frame extended cycle with emote variations)
        if frame.startswith("idle_"):
            frame_num = int(frame.split("_")[1])

            # Frame 0: open eyes, closed mouth
            if frame_num == 0:
                modifications['eye_override'] = 'open'
                modifications['mouth_override'] = 'closed'

            # Frame 1: open eyes, open mouth (breathing/talking)
            elif frame_num == 1:
                modifications['eye_override'] = 'open'
                modifications['mouth_override'] = 'open'

            # Frame 2: closed eyes (blink), closed mouth
            elif frame_num == 2:
                modifications['eye_override'] = 'closed'
                modifications['mouth_override'] = 'closed'

            # Frame 3: happy eyes, base closed mouth
            elif frame_num == 3:
                modifications['eye_override'] = 'open'
                modifications['mouth_override'] = 'closed'
                modifications['eye_emote'] = 'happy'

            # Frame 4: base eyes, closed mouth
            elif frame_num == 4:
                modifications['eye_override'] = 'open'
                modifications['mouth_override'] = 'closed'

            # Frame 5: sad eyes, base closed mouth
            elif frame_num == 5:
                modifications['eye_override'] = 'open'
                modifications['mouth_override'] = 'closed'
                modifications['eye_emote'] = 'sad'

            # Frame 6: base eyes, bored mouth
            elif frame_num == 6:
                modifications['eye_override'] = 'open'
                modifications['mouth_override'] = 'closed'
                modifications['mouth_emote'] = 'bored'

            # Frame 7: bored eyes, bored mouth
            elif frame_num == 7:
                modifications['eye_override'] = 'open'
                modifications['mouth_override'] = 'closed'
                modifications['eye_emote'] = 'bored'
                modifications['mouth_emote'] = 'bored'

            # Frame 8: base eyes, base mouth (open)
            elif frame_num == 8:
                modifications['eye_override'] = 'open'
                modifications['mouth_override'] = 'open'

            # Frame 9: open eyes, closed mouth
            elif frame_num == 9:
                modifications['eye_override'] = 'open'
                modifications['mouth_override'] = 'closed'

            return modifications

        # Emote frames (control eye/mouth open/closed states)
        if frame == 'happy':
            modifications['eye_override'] = 'open'
            modifications['mouth_override'] = 'open'  # smile
            modifications['emote_name'] = 'happy'

        elif frame == 'sad':
            modifications['eye_override'] = 'open'
            modifications['mouth_override'] = 'closed'  # frown
            modifications['emote_name'] = 'sad'

        elif frame == 'surprised':
            modifications['eye_override'] = 'open'
            modifications['mouth_override'] = 'open'  # O shape
            modifications['emote_name'] = 'surprised'

        elif frame == 'angry':
            modifications['eye_override'] = 'open'
            modifications['mouth_override'] = 'closed'  # small/tight
            modifications['emote_name'] = 'angry'

        elif frame == 'bored':
            modifications['eye_override'] = 'open'  # half-lidded (clipped open eyes)
            modifications['mouth_override'] = 'closed'  # normal
            modifications['emote_name'] = 'bored'

        # Vowel frames for lip-sync animation
        elif frame == 'vowel_a':
            modifications['eye_override'] = 'open'
            modifications['mouth_override'] = 'open'
            modifications['emote_name'] = 'vowel_a'

        elif frame == 'vowel_e':
            modifications['eye_override'] = 'open'
            modifications['mouth_override'] = 'open'
            modifications['emote_name'] = 'vowel_e'

        elif frame == 'vowel_i':
            modifications['eye_override'] = 'open'
            modifications['mouth_override'] = 'open'
            modifications['emote_name'] = 'vowel_i'

        elif frame == 'vowel_o':
            modifications['eye_override'] = 'open'
            modifications['mouth_override'] = 'open'
            modifications['emote_name'] = 'vowel_o'

        elif frame == 'vowel_u':
            modifications['eye_override'] = 'open'
            modifications['mouth_override'] = 'open'
            modifications['emote_name'] = 'vowel_u'

        # Unknown frame - return neutral
        return modifications

    def generate_random(self) -> Tuple[str, Dict]:
        """Generate a random agent with configuration info."""
        shape = random.choice(self.config.BODY_SHAPES)

        # Generate separate indices for open/closed eyes and mouths
        open_eye_idx = random.randrange(len(self.config.open_eyes))
        closed_eye_idx = random.randrange(len(self.config.closed_eyes))

        excited = random.random() < self.config.EXCITED_CHANCE
        hi = random.randrange(len(self.config.HAIRS)) if random.random() < 0.5 else None

        # Select mouth indices from open/closed mouths
        if excited:
            # For excited, choose from upper half of open mouths
            open_mouth_idx = random.randint(len(self.config.open_mouths) // 2, len(self.config.open_mouths) - 1)
            closed_mouth_idx = random.randint(len(self.config.closed_mouths) // 2, len(self.config.closed_mouths) - 1)
        else:
            # For rest, choose from lower half of open mouths
            open_mouth_idx = random.randint(0, len(self.config.open_mouths) // 2 - 1)
            closed_mouth_idx = random.randint(0, len(self.config.closed_mouths) // 2 - 1)

        body_fill = random.choice(self.config.PALETTE)
        node_fill = random.choice([c for c in self.config.PALETTE if c != body_fill])
        feet_match_body = random.random() < self.config.FEET_MATCH_BODY_CHANCE

        svg_content = self.generate_agent_svg(
            shape, open_eye_idx, closed_eye_idx, open_mouth_idx, closed_mouth_idx,
            hi, body_fill, node_fill, feet_match_body
        )

        config_info = {
            'avatar_system_version': AVATAR_SYSTEM_VERSION,
            'body_shape': f"{shape[0]}x{shape[1]}",
            'open_eye_index': open_eye_idx + 1,
            'closed_eye_index': closed_eye_idx + 1,
            'open_mouth_index': open_mouth_idx + 1,
            'closed_mouth_index': closed_mouth_idx + 1,
            'hair_index': hi + 1 if hi is not None else None,
            'excited': excited,
            'body_color': body_fill,
            'node_color': node_fill,
            'feet_color': body_fill if feet_match_body else node_fill,
            'feet_match_body': feet_match_body
        }

        return svg_content, config_info

    def generate_deterministic(self, input_string: str, frame: str = "neutral") -> Tuple[str, Dict]:
        """Generate a deterministic agent from input string (e.g., email).

        Args:
            input_string: Seed string for deterministic generation
            frame: Animation frame identifier (default: "neutral")
                   Options: "neutral", "idle_0" through "idle_3",
                           "happy", "sad", "surprised", "angry", "bored",
                           "vowel_A", "vowel_E", "vowel_I", "vowel_O", "vowel_U"
        """
        # Generate SHA-256 hash
        hash_bytes = hashlib.sha256(input_string.encode('utf-8')).digest()

        # Map hash bytes to asset selections (using different bytes for each choice)
        # Allocate 4 indices for open/closed eye and mouth states
        open_eye_idx = hash_bytes[0] % len(self.config.open_eyes)
        closed_eye_idx = hash_bytes[1] % len(self.config.closed_eyes)
        open_mouth_idx = hash_bytes[2] % len(self.config.open_mouths)
        closed_mouth_idx = hash_bytes[3] % len(self.config.closed_mouths)
        
        # Hair selection (use None if hash indicates no hair)
        hair_selection = hash_bytes[4]
        if hair_selection < 128:  # ~50% chance of having hair
            hair_index = hair_selection % len(self.config.HAIRS)
        else:
            hair_index = None

        shape_index = hash_bytes[5] % len(self.config.BODY_SHAPES)
        shape = self.config.BODY_SHAPES[shape_index]

        body_color_index = hash_bytes[6] % len(self.config.PALETTE)
        body_color = self.config.PALETTE[body_color_index]

        node_color_index = hash_bytes[7] % len(self.config.PALETTE)
        node_color = self.config.PALETTE[node_color_index]

        # Handle constraint: body_color != node_color
        if body_color == node_color:
            node_color_index = (node_color_index + 1) % len(self.config.PALETTE)
            node_color = self.config.PALETTE[node_color_index]

        feet_match_body = (hash_bytes[8] & 0x01) == 0  # Use bit for boolean decision

        # Use additional hash byte for hair color selection if needed
        hair_color_hash_byte = hash_bytes[9] if hair_index is not None else 0

        # Get frame-specific modifications
        frame_mods = self._get_frame_modifications(frame, hash_bytes)

        # Generate agent SVG with all 4 indices
        svg_content = self.generate_agent_svg(
            shape, open_eye_idx, closed_eye_idx, open_mouth_idx, closed_mouth_idx,
            hair_index, body_color, node_color, feet_match_body, hair_color_hash_byte,
            eye_override=frame_mods['eye_override'],
            mouth_override=frame_mods['mouth_override'],
            body_transform=frame_mods['body_transform'],
            emote_name=frame_mods.get('emote_name'),
            eye_emote=frame_mods.get('eye_emote'),
            mouth_emote=frame_mods.get('mouth_emote'),
            email=input_string,
            frame=frame
        )

        # Determine if mouth represents excited state (based on open mouth)
        excited = open_mouth_idx >= len(self.config.open_mouths) // 2

        config_info = {
            'avatar_system_version': AVATAR_SYSTEM_VERSION,
            'input_string': input_string,
            'frame': frame,
            'body_shape': f"{shape[0]}x{shape[1]}",
            'open_eye_index': open_eye_idx + 1,
            'closed_eye_index': closed_eye_idx + 1,
            'open_mouth_index': open_mouth_idx + 1,
            'closed_mouth_index': closed_mouth_idx + 1,
            'hair_index': hair_index + 1 if hair_index is not None else None,
            'excited': excited,
            'body_color': body_color,
            'node_color': node_color,
            'feet_color': body_color if feet_match_body else node_color,
            'feet_match_body': feet_match_body,
            'eye_override': frame_mods['eye_override'],
            'mouth_override': frame_mods['mouth_override'],
            'body_transform': frame_mods['body_transform']
        }

        return svg_content, config_info