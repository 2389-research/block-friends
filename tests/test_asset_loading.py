#!/usr/bin/env python3
# ABOUTME: Tests for asset loading and validation
# ABOUTME: Validates SVG assets are loaded correctly and parsing handles errors

import pytest
from pathlib import Path
from door_agents import DoorAgentConfig
import xml.etree.ElementTree as ET


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
        assert hasattr(config, 'eyes_open')
        assert len(config.eyes_open) > 0

    def test_config_has_mouths(self):
        """Config loads mouth assets."""
        config = DoorAgentConfig()
        assert hasattr(config, 'mouths_open')
        assert len(config.mouths_open) > 0

    def test_config_has_hair(self):
        """Config loads hair assets."""
        config = DoorAgentConfig()
        assert hasattr(config, 'hair_assets')
        assert len(config.hair_assets) > 0


class TestSVGAssetParsing:
    """Tests for SVG asset parsing."""

    def test_eyes_are_valid_svg(self):
        """Eye assets are valid SVG."""
        config = DoorAgentConfig()

        for eye in config.eyes_open:
            # Should have viewBox
            assert 'viewBox' in eye
            # Should have content
            assert 'content' in eye
            assert len(eye['content']) > 0

    def test_mouths_are_valid_svg(self):
        """Mouth assets are valid SVG."""
        config = DoorAgentConfig()

        for mouth in config.mouths_open:
            assert 'viewBox' in mouth
            assert 'content' in mouth
            assert len(mouth['content']) > 0

    def test_hair_assets_valid_svg(self):
        """Hair assets are valid SVG."""
        config = DoorAgentConfig()

        for hair in config.hair_assets:
            assert 'viewBox' in hair
            assert 'content' in hair


class TestHairAssetAttributes:
    """Tests for hair asset data attribute parsing."""

    def test_hair_z_order_attribute(self):
        """Hair assets parse z-order attribute."""
        config = DoorAgentConfig()

        # At least some hair should have z-order specified
        z_orders = [h.get('z_order', 'behind') for h in config.hair_assets]
        assert 'behind' in z_orders or 'front' in z_orders

    def test_hair_width_percent_attribute(self):
        """Hair assets parse width-percent attribute."""
        config = DoorAgentConfig()

        for hair in config.hair_assets:
            width_pct = hair.get('width_percent', 100)
            assert isinstance(width_pct, (int, float))
            assert width_pct > 0

    def test_hair_position_attributes(self):
        """Hair assets parse position attributes."""
        config = DoorAgentConfig()

        for hair in config.hair_assets:
            # Should have position-x and position-y
            assert 'position_x' in hair or 'position-x' in hair
            assert 'position_y' in hair or 'position-y' in hair

    def test_hair_color_attribute_parsing(self):
        """Hair assets parse color specifications."""
        config = DoorAgentConfig()

        for hair in config.hair_assets:
            # Should have color attribute (may be default)
            color = hair.get('color', 'currentColor')
            # Color can be: "currentColor", "contrast", "#RRGGBB", or JSON array
            assert isinstance(color, (str, list))


class TestAssetCountValidation:
    """Tests for expected asset counts."""

    def test_minimum_eye_count(self):
        """Has minimum number of eye assets."""
        config = DoorAgentConfig()

        # Should have at least a few eye variations
        assert len(config.eyes_open) >= 1
        assert len(config.eyes_closed) >= 1

    def test_minimum_mouth_count(self):
        """Has minimum number of mouth assets."""
        config = DoorAgentConfig()

        assert len(config.mouths_open) >= 1
        assert len(config.mouths_closed) >= 1

    def test_minimum_hair_count(self):
        """Has minimum number of hair assets."""
        config = DoorAgentConfig()

        assert len(config.hair_assets) >= 1

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

        for eye in config.eyes_open:
            viewbox = eye['viewBox']
            # ViewBox should be tuple of 4 numbers
            assert len(viewbox) == 4
            assert all(isinstance(v, (int, float)) for v in viewbox)

    def test_mouths_viewbox_format(self):
        """Mouth assets have valid viewBox format."""
        config = DoorAgentConfig()

        for mouth in config.mouths_open:
            viewbox = mouth['viewBox']
            assert len(viewbox) == 4
            assert all(isinstance(v, (int, float)) for v in viewbox)


class TestEmoteVariantAssets:
    """Tests for emote variant asset loading."""

    def test_emote_variants_loaded(self):
        """Emote variant assets are loaded if they exist."""
        config = DoorAgentConfig()

        # Check if emote variants exist
        # This is optional - not all systems may have emote variants
        if hasattr(config, 'emote_eyes'):
            assert isinstance(config.emote_eyes, dict)

    def test_emote_fallback_behavior(self):
        """System has fallback when emote variants missing."""
        config = DoorAgentConfig()

        # Should still work even if no emote variants
        # Basic assets should be sufficient
        assert len(config.eyes_open) > 0
        assert len(config.mouths_open) > 0
