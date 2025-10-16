#!/usr/bin/env python3
# ABOUTME: Door agent sprite generation library with shared config, assets, and generation logic
# ABOUTME: Supports both random generation (for sheets) and deterministic generation (for gravatars)

import os, random, re, xml.etree.ElementTree as ET, json, hashlib
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Union

class DoorAgentConfig:
    """Handles loading and managing all door agent configuration and assets."""
    
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

    def _load_assets(self):
        """Load all SVG assets from open/closed subdirectories."""
        # Load numbered assets from open/closed subdirectories
        self.open_eyes = self._parse_defs(self.assets_path / "eyes" / "open")
        self.closed_eyes = self._parse_defs(self.assets_path / "eyes" / "closed")
        self.open_mouths = self._parse_defs(self.assets_path / "mouths" / "open")
        self.closed_mouths = self._parse_defs(self.assets_path / "mouths" / "closed")

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
                          body_transform: str = '') -> str:
        """Generate a single agent SVG with specified parameters.

        Animation parameters:
            eye_override: "open" or "closed" to override default eye state
            mouth_override: "open" or "closed" to override default mouth state
            body_transform: SVG transform string for body positioning (e.g., "translate(1.5, 0)")
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

        # Eyes - check for state override
        if eye_override == "closed":
            ex0, ey0, ew, eh, eyes_svg, _, _, _, _, _, _ = self.config.closed_eyes[closed_eye_index]
        elif eye_override == "open":
            ex0, ey0, ew, eh, eyes_svg, _, _, _, _, _, _ = self.config.open_eyes[open_eye_index]
        else:
            # Default to open eyes for neutral/base render
            ex0, ey0, ew, eh, eyes_svg, _, _, _, _, _, _ = self.config.open_eyes[open_eye_index]
        eyes_w = body_w * self.config.EYES_W_FRAC
        se = eyes_w / ew
        eyes_h = eh * se
        max_eyes_h = body_h * self.config.EYE_MAX_HEIGHT_FRAC
        if eyes_h > max_eyes_h:
            eyes_h = max_eyes_h
            se = eyes_h / eh
            eyes_w = ew * se
        eyes_x = cx - eyes_w / 2
        target_eye_center_y = by0 + body_h * self.config.EYE_Y_FRAC
        clamped_eye_center_y = max(by0 + eyes_h / 2, min(by1 - eyes_h / 2, target_eye_center_y))
        eyes_y = clamped_eye_center_y - eyes_h / 2

        # Mouth - check for state override
        if mouth_override == "closed":
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
        eyes_bottom = clamped_eye_center_y + eyes_h / 2
        target_mouth_center = (eyes_bottom + by1) / 2
        clamped_mouth_center_y = max(by0 + mouth_h / 2, min(by1 - mouth_h / 2, target_mouth_center))
        mouth_y = clamped_mouth_center_y - mouth_h / 2

        # Nodes
        node_r = int(body_w * self.config.NODE_R_FRAC)
        node_y = by0 + body_h * self.config.NODE_Y_FRAC
        left_node = bx0 - node_r
        right_node = bx1 + node_r

        # Feet
        foot_w = int(body_w * 0.26)
        left_foot = cx - body_w / 4 - foot_w / 2
        right_foot = cx + body_w / 4 - foot_w / 2
        fy = self.config.PAD + self.config.BOX - foot_h

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
        g.append(f'<rect x="{bx0}" y="{by0}" width="{body_w}" height="{body_h}" '
                 f'fill="{body_color}" stroke="{self.config.OUTLINE}" stroke-width="{self.config.STROKE}"/>')
        g.append(f'<line x1="{cx}" y1="{by0}" x2="{cx}" y2="{by1}" '
                 f'stroke="{self.config.OUTLINE}" stroke-width="{self.config.STROKE}"/>')

        # Nodes
        for nx in (left_node, right_node):
            g.append(f'<circle cx="{nx}" cy="{node_y}" r="{node_r}" '
                     f'fill="{node_color}" stroke="{self.config.OUTLINE}" stroke-width="{self.config.STROKE}"/>')

        # Feet
        for fx in (left_foot, right_foot):
            g.append(f'<rect x="{fx}" y="{fy}" width="{foot_w}" height="{foot_h}" '
                     f'fill="{feet_fill}" stroke="{self.config.OUTLINE}" stroke-width="{self.config.STROKE}"/>')

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

        return "".join(g)

    def _get_frame_modifications(self, frame: str, hash_bytes: bytes) -> Dict:
        """Get frame-specific modifications for animation.

        New system uses open/closed eye and mouth states with horizontal body sway.

        Args:
            frame: Frame identifier (e.g., "neutral", "idle_0", "happy", "vowel_A")
            hash_bytes: SHA-256 hash bytes for deterministic variations

        Returns:
            Dict with keys: eye_override, mouth_override, body_transform
        """
        modifications = {
            'eye_override': None,      # "open", "closed", or None (use agent default)
            'mouth_override': None,    # "open", "closed", or None (use agent default)
            'body_transform': ''       # SVG transform string for body positioning
        }

        # Neutral frame - no modifications
        if frame == "neutral":
            return modifications

        # Idle animation frames (4-frame blink + sway cycle)
        if frame.startswith("idle_"):
            frame_num = int(frame.split("_")[1])

            # Frame 0: open eyes, body left (-1.5px horizontal offset)
            if frame_num == 0:
                modifications['eye_override'] = 'open'
                modifications['body_transform'] = 'translate(-1.5, 0)'

            # Frame 1: open eyes, body center (no offset)
            elif frame_num == 1:
                modifications['eye_override'] = 'open'
                modifications['body_transform'] = ''

            # Frame 2: closed eyes (blink), body right (+1.5px horizontal offset)
            elif frame_num == 2:
                modifications['eye_override'] = 'closed'
                modifications['body_transform'] = 'translate(1.5, 0)'

            # Frame 3: open eyes, body center (no offset)
            elif frame_num == 3:
                modifications['eye_override'] = 'open'
                modifications['body_transform'] = ''

            return modifications

        # Emote frames (control eye/mouth open/closed states)
        if frame == 'happy':
            modifications['eye_override'] = 'open'
            modifications['mouth_override'] = 'open'  # smile

        elif frame == 'sad':
            modifications['eye_override'] = 'open'
            modifications['mouth_override'] = 'closed'  # frown

        elif frame == 'surprised':
            modifications['eye_override'] = 'open'
            modifications['mouth_override'] = 'open'  # O shape

        elif frame == 'angry':
            modifications['eye_override'] = 'open'
            modifications['mouth_override'] = 'closed'  # small/tight

        elif frame == 'bored':
            modifications['eye_override'] = 'closed'
            modifications['mouth_override'] = 'closed'  # normal

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
            body_transform=frame_mods['body_transform']
        )

        # Determine if mouth represents excited state (based on open mouth)
        excited = open_mouth_idx >= len(self.config.open_mouths) // 2

        config_info = {
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