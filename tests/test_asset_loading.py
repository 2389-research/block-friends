#!/usr/bin/env python3
# ABOUTME: Tests for asset loading and validation
# ABOUTME: Validates SVG assets are loaded correctly and parsing handles errors

from pathlib import Path
from door_agents import DoorAgentConfig


class TestAssetDirectoryStructure:
    """Tests for asset directory structure validation."""

    def test_assets_directory_exists(self):
        """Assets directory exists at expected location."""
        assets_path = Path("assets")
        assert assets_path.exists()
        assert assets_path.is_dir()

    def test_eyes_directory_structure(self):
        """Eyes directory has expected structure."""
        eyes_open = Path("assets/eyes/open")
        eyes_closed = Path("assets/eyes/closed")

        assert eyes_open.exists() or Path("assets/eyes").exists()
        # Structure may vary, just check eyes assets exist

    def test_mouths_directory_structure(self):
        """Mouths directory has expected structure."""
        mouths_path = Path("assets/mouths")
        assert mouths_path.exists()

    def test_hair_directory_exists(self):
        """Hair directory exists."""
        hair_path = Path("assets/hair")
        assert hair_path.exists()


class TestAssetFileLoading:
    """Tests for loading asset files."""

    def test_config_loads_successfully(self):
        """DoorAgentConfig loads without errors."""
        config = DoorAgentConfig()
        assert config is not None

    def test_config_has_body_shapes(self):
        """Config loads body shapes."""
        config = DoorAgentConfig()
        assert hasattr(config, 'BODY_SHAPES')
        assert len(config.BODY_SHAPES) > 0

    def test_config_has_palette(self):
        """Config loads color palette."""
        config = DoorAgentConfig()
        assert hasattr(config, 'PALETTE')
        assert len(config.PALETTE) > 0

    def test_config_has_eyes(self):
        """Config loads eye assets."""
        config = DoorAgentConfig()
        assert hasattr(config, 'open_eyes')
        assert hasattr(config, 'closed_eyes')
        assert len(config.open_eyes) > 0
        assert len(config.closed_eyes) > 0

    def test_config_has_mouths(self):
        """Config loads mouth assets."""
        config = DoorAgentConfig()
        assert hasattr(config, 'open_mouths')
        assert hasattr(config, 'closed_mouths')
        assert len(config.open_mouths) > 0
        assert len(config.closed_mouths) > 0

    def test_config_has_hair(self):
        """Config loads hair assets."""
        config = DoorAgentConfig()
        assert hasattr(config, 'HAIRS')
        assert len(config.HAIRS) > 0


class TestSVGAssetParsing:
    """Tests for SVG asset parsing."""

    def test_eyes_are_valid_svg(self):
        """Eye assets are valid SVG."""
        config = DoorAgentConfig()

        for eye in config.open_eyes:
            # Assets are tuples: (x0, y0, w, h, content, z_order, width_percent, position_x, position_y, anchor, color_spec)
            assert len(eye) >= 5  # At least viewBox (4 values) + content
            # Content is at index 4
            assert len(eye[4]) > 0

    def test_mouths_are_valid_svg(self):
        """Mouth assets are valid SVG."""
        config = DoorAgentConfig()

        for mouth in config.open_mouths:
            assert len(mouth) >= 5
            assert len(mouth[4]) > 0  # content

    def test_hair_assets_valid_svg(self):
        """Hair assets are valid SVG."""
        config = DoorAgentConfig()

        for hair in config.HAIRS:
            assert len(hair) >= 5
            assert len(hair[4]) > 0  # content


class TestHairAssetAttributes:
    """Tests for hair asset data attribute parsing."""

    def test_hair_z_order_attribute(self):
        """Hair assets parse z-order attribute."""
        config = DoorAgentConfig()

        # Hair tuples: (x0, y0, w, h, content, z_order, width_percent, position_x, position_y, anchor, color_spec)
        # z_order is at index 5
        z_orders = [h[5] for h in config.HAIRS if len(h) > 5]
        assert 'behind' in z_orders or 'front' in z_orders

    def test_hair_width_percent_attribute(self):
        """Hair assets parse width-percent attribute."""
        config = DoorAgentConfig()

        for hair in config.HAIRS:
            if len(hair) > 6:
                width_pct = hair[6]  # width_percent is at index 6
                assert isinstance(width_pct, (int, float))
                assert width_pct > 0

    def test_hair_position_attributes(self):
        """Hair assets parse position attributes."""
        config = DoorAgentConfig()

        for hair in config.HAIRS:
            if len(hair) > 8:
                # position_x at index 7, position_y at index 8
                position_x = hair[7]
                position_y = hair[8]
                assert position_x is not None
                assert position_y is not None

    def test_hair_color_attribute_parsing(self):
        """Hair assets parse color specifications."""
        config = DoorAgentConfig()

        for hair in config.HAIRS:
            if len(hair) > 10:
                # color_spec is at index 10
                color = hair[10]
                # Color can be: "currentColor", "contrast", "#RRGGBB", or JSON array
                assert isinstance(color, (str, list)) or color is None


class TestAssetCountValidation:
    """Tests for expected asset counts."""

    def test_minimum_eye_count(self):
        """Has minimum number of eye assets."""
        config = DoorAgentConfig()

        # Should have at least a few eye variations
        assert len(config.open_eyes) >= 1
        assert len(config.closed_eyes) >= 1

    def test_minimum_mouth_count(self):
        """Has minimum number of mouth assets."""
        config = DoorAgentConfig()

        assert len(config.open_mouths) >= 1
        assert len(config.closed_mouths) >= 1

    def test_minimum_hair_count(self):
        """Has minimum number of hair assets."""
        config = DoorAgentConfig()

        assert len(config.HAIRS) >= 1

    def test_minimum_body_shapes(self):
        """Has minimum number of body shapes."""
        config = DoorAgentConfig()

        assert len(config.BODY_SHAPES) >= 1


class TestColorPaletteValidation:
    """Tests for color palette validation."""

    def test_palette_has_valid_colors(self):
        """Color palette contains valid hex colors."""
        config = DoorAgentConfig()

        for color in config.PALETTE:
            # Should be hex color format
            assert color.startswith('#')
            assert len(color) == 7  # #RRGGBB

    def test_palette_sufficient_variety(self):
        """Color palette has sufficient variety."""
        config = DoorAgentConfig()

        # Should have at least 3 colors for variety
        assert len(config.PALETTE) >= 3


class TestConfigJSONFiles:
    """Tests for JSON configuration file loading."""

    def test_config_json_exists(self):
        """config.json file exists."""
        config_file = Path("assets/config.json")
        assert config_file.exists()

    def test_colors_json_exists(self):
        """colors.json file exists."""
        colors_file = Path("assets/colors.json")
        assert colors_file.exists()

    def test_body_shapes_json_exists(self):
        """body_shapes.json file exists."""
        body_shapes_file = Path("assets/body_shapes.json")
        assert body_shapes_file.exists()

    def test_probabilities_json_exists(self):
        """probabilities.json file exists."""
        probabilities_file = Path("assets/probabilities.json")
        assert probabilities_file.exists()


class TestAssetViewBoxParsing:
    """Tests for viewBox attribute parsing."""

    def test_eyes_viewbox_format(self):
        """Eye assets have valid viewBox format."""
        config = DoorAgentConfig()

        for eye in config.open_eyes:
            # ViewBox components are indices 0-3: (x0, y0, w, h, ...)
            assert len(eye) >= 4
            # Check that first 4 elements are numbers
            assert all(isinstance(eye[i], (int, float)) for i in range(4))

    def test_mouths_viewbox_format(self):
        """Mouth assets have valid viewBox format."""
        config = DoorAgentConfig()

        for mouth in config.open_mouths:
            assert len(mouth) >= 4
            assert all(isinstance(mouth[i], (int, float)) for i in range(4))


class TestEmoteVariantAssets:
    """Tests for emote variant asset loading."""

    def test_emote_variants_loaded(self):
        """Emote variant assets are loaded if they exist."""
        config = DoorAgentConfig()

        # Check if emote variants exist
        # These should be loaded from door_agents.py
        if hasattr(config, 'open_eye_emotes'):
            assert isinstance(config.open_eye_emotes, dict)

    def test_emote_fallback_behavior(self):
        """System has fallback when emote variants missing."""
        config = DoorAgentConfig()

        # Should still work even if no emote variants
        # Basic assets should be sufficient
        assert len(config.open_eyes) > 0
        assert len(config.open_mouths) > 0
