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
        """Load all SVG assets."""
        # Load numbered assets (existing)
        self.EYES = self._parse_defs(self.assets_path / "eyes")
        self.MOUTHS = self._parse_defs(self.assets_path / "mouths")
        self.HAIRS = self._parse_defs(self.assets_path / "hair")

        # Load emote/animation assets (new)
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
                          eye_index: int,
                          mouth_index: int,
                          hair_index: Optional[int],
                          body_color: str,
                          node_color: str,
                          feet_match_body: bool,
                          hair_color_hash_byte: int = 0,
                          body_scale_y: float = 1.0,
                          eye_override: Optional[str] = None,
                          mouth_override: Optional[str] = None,
                          show_eyebrows: bool = False) -> str:
        """Generate a single agent SVG with specified parameters.

        Animation parameters:
            body_scale_y: Vertical scale factor for body (for breathing)
            eye_override: Asset name for emote eyes (e.g., "emote_happy")
            mouth_override: Asset name for emote/vowel mouths (e.g., "vowel_A")
            show_eyebrows: Whether to render eyebrows (for angry emote)
        """

        w_tiles, h_tiles = shape
        scale = (self.config.BOX - self.config.BOX * self.config.FOOT_H_FRAC) / 7
        body_w = int(w_tiles * scale)
        body_h = int(h_tiles * scale * body_scale_y)  # Apply vertical scale
        foot_h = int(self.config.BOX * self.config.FOOT_H_FRAC)

        bx0 = self.config.PAD + (self.config.BOX - body_w) // 2
        by0 = self.config.PAD + self.config.BOX - foot_h - body_h
        bx1 = bx0 + body_w
        by1 = by0 + body_h
        cx = (bx0 + bx1) / 2

        feet_fill = body_color if feet_match_body else node_color

        # Eyes - check for override
        if eye_override and eye_override in self.config.EMOTE_EYES:
            ex0, ey0, ew, eh, eyes_svg = self.config.EMOTE_EYES[eye_override]
        else:
            ex0, ey0, ew, eh, eyes_svg, _, _, _, _, _, _ = self.config.EYES[eye_index]
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

        # Mouth - check for override
        if mouth_override:
            if mouth_override in self.config.EMOTE_MOUTHS:
                mx0, my0, mw, mh, mouth_svg = self.config.EMOTE_MOUTHS[mouth_override]
            elif mouth_override in self.config.VOWEL_MOUTHS:
                mx0, my0, mw, mh, mouth_svg = self.config.VOWEL_MOUTHS[mouth_override]
            else:
                # Fallback to normal mouth if override not found
                mx0, my0, mw, mh, mouth_svg, _, _, _, _, _, _ = self.config.MOUTHS[mouth_index]
        else:
            mx0, my0, mw, mh, mouth_svg, _, _, _, _, _, _ = self.config.MOUTHS[mouth_index]
        # Determine if this is an excited mouth (index 6+ in our system)
        excited = mouth_index >= 6
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

        # Eyebrows (if enabled for angry emote)
        if show_eyebrows and "angry" in self.config.EYEBROWS:
            brow_x0, brow_y0, brow_w, brow_h, brow_svg = self.config.EYEBROWS["angry"]
            # Position eyebrows above eyes, same width as eyes
            s_brow = eyes_w / brow_w
            brow_height = brow_h * s_brow
            brow_x = eyes_x
            brow_y = eyes_y - brow_height - 1  # 1px gap above eyes
            g.append(f'<g transform="translate({brow_x},{brow_y}) scale({s_brow}) '
                     f'translate({-brow_x0}, {-brow_y0})">{brow_svg}</g>')

        # Mouth
        g.append(f'<g transform="translate({mouth_x},{mouth_y}) scale({sm}) '
                 f'translate({-mx0}, {-my0})">{mouth_svg}</g>')

        # Hair in front
        if hair_element and hair_index is not None:
            _, _, _, _, _, hair_z_order, _, _, _, _, _ = self.config.HAIRS[hair_index]
            if hair_z_order == "front":
                g.append(hair_element)

        return "".join(g)

    def _get_frame_modifications(self, frame: str, hash_bytes: bytes) -> Dict:
        """Get frame-specific modifications for animation.

        Args:
            frame: Frame identifier (e.g., "neutral", "idle_0", "happy", "vowel_A")
            hash_bytes: SHA-256 hash bytes for deterministic variations

        Returns:
            Dict with keys: body_scale_y, eye_override, mouth_override, show_eyebrows
        """
        modifications = {
            'body_scale_y': 1.0,
            'eye_override': None,
            'mouth_override': None,
            'show_eyebrows': False
        }

        # Neutral frame - no modifications
        if frame == "neutral":
            return modifications

        # Idle animation frames (4-frame breathing cycle)
        if frame.startswith("idle_"):
            frame_num = int(frame.split("_")[1])
            # Use hash bytes 8-10 for subtle per-agent variations
            variation = (hash_bytes[8] % 10) / 100.0  # 0.00 to 0.09

            # Breathing cycle: expand -> hold -> contract -> hold
            scales = [1.0, 1.02 + variation, 1.02 + variation, 1.0]
            modifications['body_scale_y'] = scales[frame_num % 4]
            return modifications

        # Emote frames
        emote_map = {
            'happy': ('emote_happy', 'emote_smile', False),
            'sad': ('emote_sad', 'emote_frown', False),
            'surprised': ('emote_surprised', 'emote_O', False),
            'angry': ('emote_angry', 'emote_line', True),
            'bored': ('emote_bored', 'emote_line', False)
        }

        if frame in emote_map:
            eye_asset, mouth_asset, eyebrows = emote_map[frame]
            modifications['eye_override'] = eye_asset
            modifications['mouth_override'] = mouth_asset
            modifications['show_eyebrows'] = eyebrows
            return modifications

        # Vowel mouth frames
        vowel_map = {
            'vowel_A': 'vowel_A',
            'vowel_E': 'vowel_E',
            'vowel_I': 'vowel_I',
            'vowel_O': 'vowel_O',
            'vowel_U': 'vowel_U'
        }

        if frame in vowel_map:
            modifications['mouth_override'] = vowel_map[frame]
            return modifications

        # Unknown frame - return neutral
        return modifications

    def generate_random(self) -> Tuple[str, Dict]:
        """Generate a random agent with configuration info."""
        shape = random.choice(self.config.BODY_SHAPES)
        ei = random.randrange(len(self.config.EYES))
        excited = random.random() < self.config.EXCITED_CHANCE
        hi = random.randrange(len(self.config.HAIRS)) if random.random() < 0.5 else None

        if excited:
            mi = random.randint(self.config.EXC_RANGE[0], self.config.EXC_RANGE[1])
        else:
            mi = random.randint(self.config.REST_RANGE[0], self.config.REST_RANGE[1])

        body_fill = random.choice(self.config.PALETTE)
        node_fill = random.choice([c for c in self.config.PALETTE if c != body_fill])
        feet_match_body = random.random() < self.config.FEET_MATCH_BODY_CHANCE

        svg_content = self.generate_agent_svg(shape, ei, mi, hi, body_fill, node_fill, feet_match_body)

        config_info = {
            'body_shape': f"{shape[0]}x{shape[1]}",
            'eye_index': ei + 1,
            'mouth_index': mi + 1,
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
        eye_index = hash_bytes[0] % len(self.config.EYES)
        mouth_index = hash_bytes[1] % len(self.config.MOUTHS)
        
        # Hair selection (use None if hash indicates no hair)
        hair_selection = hash_bytes[2]
        if hair_selection < 128:  # ~50% chance of having hair
            hair_index = hair_selection % len(self.config.HAIRS)
        else:
            hair_index = None
            
        shape_index = hash_bytes[3] % len(self.config.BODY_SHAPES)
        shape = self.config.BODY_SHAPES[shape_index]
        
        body_color_index = hash_bytes[4] % len(self.config.PALETTE)
        body_color = self.config.PALETTE[body_color_index]
        
        node_color_index = hash_bytes[5] % len(self.config.PALETTE)
        node_color = self.config.PALETTE[node_color_index]
        
        # Handle constraint: body_color != node_color
        if body_color == node_color:
            node_color_index = (node_color_index + 1) % len(self.config.PALETTE)
            node_color = self.config.PALETTE[node_color_index]
            
        feet_match_body = (hash_bytes[6] & 0x01) == 0  # Use bit for boolean decision
        
        # Use additional hash byte for hair color selection if needed
        hair_color_hash_byte = hash_bytes[7] if hair_index is not None else 0

        # Get frame-specific modifications
        frame_mods = self._get_frame_modifications(frame, hash_bytes)

        svg_content = self.generate_agent_svg(
            shape, eye_index, mouth_index, hair_index,
            body_color, node_color, feet_match_body, hair_color_hash_byte,
            body_scale_y=frame_mods['body_scale_y'],
            eye_override=frame_mods['eye_override'],
            mouth_override=frame_mods['mouth_override'],
            show_eyebrows=frame_mods['show_eyebrows']
        )

        # Determine if mouth represents excited state
        excited = mouth_index >= 6

        config_info = {
            'input_string': input_string,
            'frame': frame,
            'body_shape': f"{shape[0]}x{shape[1]}",
            'eye_index': eye_index + 1,
            'mouth_index': mouth_index + 1,
            'hair_index': hair_index + 1 if hair_index is not None else None,
            'excited': excited,
            'body_color': body_color,
            'node_color': node_color,
            'feet_color': body_color if feet_match_body else node_color,
            'feet_match_body': feet_match_body,
            'body_scale_y': frame_mods['body_scale_y'],
            'eye_override': frame_mods['eye_override'],
            'mouth_override': frame_mods['mouth_override'],
            'show_eyebrows': frame_mods['show_eyebrows']
        }

        return svg_content, config_info

    def generate_transition(self, input_string: str, emote: str, weight: int) -> Tuple[str, Dict]:
        """
        Generate a transition frame between neutral and an emotional expression.

        Uses opacity-based crossfading to smoothly interpolate between:
        - Base state (open eyes, closed mouth)
        - Target expression (emote eyes + emote mouth)

        Args:
            input_string: Seed string for deterministic generation
            emote: Expression name (joy, sorrow, surprised, angry, bored, fun, A, O, U)
            weight: Animation progress as percentage (0-100)
                   0 = neutral, 100 = full expression

        Returns:
            Tuple of (svg_string, metadata_dict)
        """
        # Validate inputs
        valid_emotes = ['joy', 'sorrow', 'surprised', 'angry', 'bored', 'fun']
        valid_vowels = ['A', 'E', 'I', 'O', 'U']

        if emote not in valid_emotes and emote not in valid_vowels:
            raise ValueError(f"Invalid emote '{emote}'. Must be one of {valid_emotes + valid_vowels}")

        if not 0 <= weight <= 100:
            raise ValueError(f"Weight must be 0-100, got {weight}")

        # Generate base avatar deterministically
        hash_bytes = hashlib.sha256(input_string.encode('utf-8')).digest()

        # Map hash bytes to asset selections (same logic as generate_deterministic)
        eye_index = hash_bytes[0] % len(self.config.EYES)
        mouth_index = hash_bytes[1] % len(self.config.MOUTHS)
        hair_selection = hash_bytes[2]
        hair_index = hair_selection % len(self.config.HAIRS) if hair_selection < 128 else None
        body_shape_index = hash_bytes[3] % len(self.config.BODY_SHAPES)
        body_color_index = hash_bytes[4] % len(self.config.PALETTE)
        feet_color_index = hash_bytes[5] % len(self.config.PALETTE)
        node_color_index = hash_bytes[6] % len(self.config.PALETTE)
        while node_color_index == body_color_index:
            node_color_index = (node_color_index + 1) % len(self.config.PALETTE)
        hair_color_hash_byte = hash_bytes[7]

        body_w, body_h = self.config.BODY_SHAPES[body_shape_index]
        body_color = self.config.PALETTE[body_color_index]
        feet_color = self.config.PALETTE[feet_color_index]
        node_color = self.config.PALETTE[node_color_index]

        # Calculate opacity values for crossfade
        weight_frac = weight / 100.0
        base_opacity = 1.0 - weight_frac
        target_opacity = weight_frac

        # Determine target eye and mouth overrides based on emote
        eye_override = None
        mouth_override = None

        if emote in valid_emotes:
            # Emotional expression
            eye_override = f"emote_{emote}" if emote in ['happy', 'sad', 'surprised', 'angry', 'bored', 'fun'] else f"emote_{emote}"
            mouth_override = f"emote_{emote}"
        else:
            # Vowel shape (eyes stay open, mouth changes)
            eye_override = None  # Keep base open eyes
            mouth_override = f"vowel_{emote}"

        # Generate the transition SVG with opacity layering
        svg_content = self._generate_transition_svg(
            eye_index=eye_index,
            mouth_index=mouth_index,
            hair_index=hair_index,
            body_shape_index=body_shape_index,
            body_color=body_color,
            feet_color=feet_color,
            node_color=node_color,
            hair_color_hash_byte=hair_color_hash_byte,
            base_opacity=base_opacity,
            target_opacity=target_opacity,
            eye_override=eye_override,
            mouth_override=mouth_override
        )

        metadata = {
            'emote': emote,
            'weight': weight,
            'is_neutral': weight == 0,
            'is_full_expression': weight == 100,
            'input_hash': hashlib.sha256(input_string.encode('utf-8')).hexdigest()[:16]
        }

        return svg_content, metadata

    def _generate_transition_svg(
        self,
        eye_index: int,
        mouth_index: int,
        hair_index: Optional[int],
        body_shape_index: int,
        body_color: str,
        feet_color: str,
        node_color: str,
        hair_color_hash_byte: int,
        base_opacity: float,
        target_opacity: float,
        eye_override: Optional[str],
        mouth_override: Optional[str]
    ) -> str:
        """
        Generate SVG with opacity-based transition between base and target states.

        Strategy:
        1. Render base avatar (open eyes, closed mouth) at base_opacity
        2. Render target features (emote eyes, emote mouth) at target_opacity
        3. Layer them in the same SVG for crossfade effect
        """
        body_w, body_h = self.config.BODY_SHAPES[body_shape_index]

        # Calculate positions (same as generate_deterministic)
        cx = self.config.PAD + self.config.BOX / 2
        bx0 = cx - body_w / 2
        by0 = self.config.PAD + self.config.BOX - body_h
        bx1 = bx0 + body_w
        by1 = by0 + body_h
        foot_h = int(body_h * self.config.FOOT_H_FRAC)

        # Base eyes
        ex0, ey0, ew, eh, eyes_svg, *_ = self.config.EYES[eye_index]
        eyes_w = body_w * self.config.EYES_W_FRAC
        se = eyes_w / ew
        eyes_h = eh * se
        if eyes_h > body_h * self.config.EYE_MAX_HEIGHT_FRAC:
            eyes_h = body_h * self.config.EYE_MAX_HEIGHT_FRAC
            se = eyes_h / eh
            eyes_w = ew * se
        eyes_x = cx - eyes_w / 2
        target_eye_center_y = by0 + body_h * self.config.EYE_Y_FRAC
        clamped_eye_center_y = max(by0 + eyes_h / 2, min(by1 - eyes_h / 2, target_eye_center_y))
        eyes_y = clamped_eye_center_y - eyes_h / 2

        # Base mouth
        mx0, my0, mw, mh, mouth_svg, *_ = self.config.MOUTHS[mouth_index]
        mouth_w = body_w * self.config.MOUTH_W_REST
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

        # Nodes and feet (same as generate_deterministic)
        node_r = int(body_w * self.config.NODE_R_FRAC)
        node_y = by0 + body_h * self.config.NODE_Y_FRAC
        left_node = bx0 - node_r
        right_node = bx1 + node_r

        foot_w = int(body_w * 0.26)
        left_foot = cx - body_w / 4 - foot_w / 2
        right_foot = cx + body_w / 4 - foot_w / 2
        fy = self.config.PAD + self.config.BOX - foot_h

        # Build SVG layers
        g = []

        # Hair (if present, render once - doesn't transition)
        if hair_index is not None:
            hx0, hy0, hw, hh, hair_svg, hair_z_order, hair_width_percent, hair_position_x, hair_position_y, hair_anchor, hair_color_spec = self.config.HAIRS[hair_index]

            hair_w = body_w * (hair_width_percent / 100)
            sh = hair_w / hw
            hair_h = hh * sh

            if hair_position_x == "cell-center":
                hair_x = self.config.PAD + self.config.BOX / 2 - hair_w / 2
            elif hair_position_x.endswith("%"):
                percent = float(hair_position_x[:-1]) / 100
                hair_x = cx + (hair_w * percent) - hair_w / 2
            else:
                hair_x = cx - hair_w / 2

            if hair_position_y == "between-body-eyes":
                base_y = (by0 + eyes_y) / 2
            elif hair_position_y == "eyes":
                base_y = clamped_eye_center_y
            elif hair_position_y.endswith("%"):
                percent = float(hair_position_y[:-1]) / 100
                base_y = by0 + (hair_h * percent)
            else:
                base_y = by0

            if hair_anchor == "bottom":
                hair_y = base_y - hair_h
            elif hair_anchor == "center":
                hair_y = base_y - hair_h / 2
            else:
                hair_y = base_y

            hair_color = self._resolve_hair_color_deterministic(hair_color_spec, body_color, hair_color_hash_byte)
            hair_element = f'<g color="{hair_color}" transform="translate({hair_x},{hair_y}) scale({sh}) translate({-hx0}, {-hy0})">{hair_svg}</g>'

            if hair_z_order == "behind":
                g.append(hair_element)

        # Body and static elements
        g.append(f'<rect x="{bx0}" y="{by0}" width="{body_w}" height="{body_h}" '
                 f'fill="{body_color}" stroke="{self.config.OUTLINE}" stroke-width="{self.config.STROKE}"/>')

        # Left node
        g.append(f'<circle cx="{left_node}" cy="{node_y}" r="{node_r}" '
                 f'fill="{node_color}" stroke="{self.config.OUTLINE}" stroke-width="{self.config.STROKE}"/>')

        # Right node
        g.append(f'<circle cx="{right_node}" cy="{node_y}" r="{node_r}" '
                 f'fill="{node_color}" stroke="{self.config.OUTLINE}" stroke-width="{self.config.STROKE}"/>')

        # Feet
        g.append(f'<rect x="{left_foot}" y="{fy}" width="{foot_w}" height="{foot_h}" '
                 f'fill="{feet_color}" stroke="{self.config.OUTLINE}" stroke-width="{self.config.STROKE}"/>')
        g.append(f'<rect x="{right_foot}" y="{fy}" width="{foot_w}" height="{foot_h}" '
                 f'fill="{feet_color}" stroke="{self.config.OUTLINE}" stroke-width="{self.config.STROKE}"/>')

        # BASE LAYER: Original eyes and mouth at base_opacity
        if base_opacity > 0:
            g.append(f'<g opacity="{base_opacity:.3f}">')
            g.append(f'  <g transform="translate({eyes_x},{eyes_y}) scale({se}) translate({-ex0}, {-ey0})">{eyes_svg}</g>')
            g.append(f'  <g transform="translate({mouth_x},{mouth_y}) scale({sm}) translate({-mx0}, {-my0})">{mouth_svg}</g>')
            g.append('</g>')

        # TARGET LAYER: Emote eyes and mouth at target_opacity
        if target_opacity > 0 and (eye_override or mouth_override):
            g.append(f'<g opacity="{target_opacity:.3f}">')

            # Target eyes (if override specified)
            if eye_override and eye_override in self.config.EMOTE_EYES:
                tex0, tey0, tew, teh, target_eyes_svg = self.config.EMOTE_EYES[eye_override]
                target_eyes_w = body_w * self.config.EYES_W_FRAC
                tse = target_eyes_w / tew
                target_eyes_h = teh * tse
                if target_eyes_h > body_h * self.config.EYE_MAX_HEIGHT_FRAC:
                    target_eyes_h = body_h * self.config.EYE_MAX_HEIGHT_FRAC
                    tse = target_eyes_h / teh
                    target_eyes_w = tew * tse
                target_eyes_x = cx - target_eyes_w / 2
                target_eyes_y = clamped_eye_center_y - target_eyes_h / 2

                g.append(f'  <g transform="translate({target_eyes_x},{target_eyes_y}) scale({tse}) translate({-tex0}, {-tey0})">{target_eyes_svg}</g>')
            else:
                # No eye override, use base eyes
                g.append(f'  <g transform="translate({eyes_x},{eyes_y}) scale({se}) translate({-ex0}, {-ey0})">{eyes_svg}</g>')

            # Target mouth (if override specified)
            if mouth_override:
                if mouth_override in self.config.EMOTE_MOUTHS:
                    tmx0, tmy0, tmw, tmh, target_mouth_svg = self.config.EMOTE_MOUTHS[mouth_override]
                elif mouth_override in self.config.VOWEL_MOUTHS:
                    tmx0, tmy0, tmw, tmh, target_mouth_svg = self.config.VOWEL_MOUTHS[mouth_override]
                else:
                    # Fallback to base mouth
                    tmx0, tmy0, tmw, tmh, target_mouth_svg = mx0, my0, mw, mh, mouth_svg

                target_mouth_w = body_w * self.config.MOUTH_W_REST
                tsm = target_mouth_w / tmw
                target_mouth_h = tmh * tsm
                if target_mouth_h > max_mouth_h:
                    target_mouth_h = max_mouth_h
                    tsm = target_mouth_h / tmh
                    target_mouth_w = tmw * tsm
                target_mouth_x = cx - target_mouth_w / 2
                target_mouth_y = clamped_mouth_center_y - target_mouth_h / 2

                g.append(f'  <g transform="translate({target_mouth_x},{target_mouth_y}) scale({tsm}) translate({-tmx0}, {-tmy0})">{target_mouth_svg}</g>')
            else:
                # No mouth override, use base mouth
                g.append(f'  <g transform="translate({mouth_x},{mouth_y}) scale({sm}) translate({-mx0}, {-my0})">{mouth_svg}</g>')

            g.append('</g>')

        # Hair front layer (if present)
        if hair_index is not None and hair_z_order == "front":
            g.append(hair_element)

        # Assemble final SVG
        svg = f'<svg viewBox="0 0 {self.config.CELL} {self.config.CELL}" xmlns="http://www.w3.org/2000/svg">{"".join(g)}</svg>'

        return svg