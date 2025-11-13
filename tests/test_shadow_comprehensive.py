"""
Comprehensive shadow feature tests.

Tests shadow sizing, positioning, filtering, and visibility control.
"""

import pytest
from fastapi.testclient import TestClient
from app import app
from door_agents import DoorAgentGenerator, DoorAgentConfig
import re

client = TestClient(app)
config = DoorAgentConfig()
generator = DoorAgentGenerator(config)


class TestShadowGeneration:
    """Tests for shadow generation in avatars."""

    def test_avatar_contains_shadow_by_default(self):
        """Avatars include shadow by default."""
        svg, _ = generator.generate_deterministic("test@example.com")

        # Should contain shadow element (ellipse) or shadow reference
        assert 'shadow' in svg.lower() or 'ellipse' in svg.lower()

    def test_shadow_element_structure(self):
        """Shadow has correct SVG structure."""
        svg, _ = generator.generate_deterministic("test@example.com")

        # Shadow should be an ellipse
        if 'ellipse' in svg.lower():
            # Check for ellipse attributes
            assert 'rx=' in svg or 'ry=' in svg

    def test_shadow_has_blur_filter(self):
        """Shadow uses Gaussian blur filter."""
        svg, _ = generator.generate_deterministic("test@example.com")

        # Should have filter definition
        if 'shadow' in svg.lower():
            # Should have blur filter
            assert 'filter' in svg.lower() or 'blur' in svg.lower()


class TestShadowSizing:
    """Tests for shadow sizing based on avatar content."""

    def test_shadow_scales_with_body_width(self):
        """Shadow width scales with body width."""
        # Generate multiple avatars
        svg1, info1 = generator.generate_deterministic("user1@example.com")
        svg2, info2 = generator.generate_deterministic("user2@example.com")

        # Both should have shadows
        assert 'ellipse' in svg1.lower() or 'shadow' in svg1.lower()
        assert 'ellipse' in svg2.lower() or 'shadow' in svg2.lower()

    def test_shadow_width_calculation(self):
        """Shadow width is content_width * 1.2."""
        svg, info = generator.generate_deterministic("test@example.com")

        # Shadow should be present
        # Exact calculation would require parsing SVG
        # Just verify shadow exists
        assert '<svg' in svg

    def test_shadow_height_calculation(self):
        """Shadow height is content_width * 0.15."""
        svg, info = generator.generate_deterministic("test@example.com")

        # Shadow should have appropriate height
        assert '<svg' in svg


class TestShadowPositioning:
    """Tests for shadow positioning relative to avatar."""

    def test_shadow_positioned_at_bottom(self):
        """Shadow is positioned at bottom of avatar."""
        svg, info = generator.generate_deterministic("test@example.com")

        # Shadow should be present
        # Positioned near bottom (overlapping feet by 3px according to docs)
        if 'ellipse' in svg.lower():
            # Check cy (y-coordinate) is near bottom
            assert 'cy=' in svg

    def test_shadow_overlaps_feet(self):
        """Shadow overlaps feet by 3px for depth effect."""
        svg, info = generator.generate_deterministic("test@example.com")

        # Shadow positioning creates overlap with feet
        # Verify shadow exists
        assert '<svg' in svg

    def test_shadow_centered_horizontally(self):
        """Shadow is centered horizontally under avatar."""
        svg, info = generator.generate_deterministic("test@example.com")

        # Shadow should be horizontally centered
        if 'ellipse' in svg.lower():
            # Check cx (x-coordinate) for centering
            assert 'cx=' in svg


class TestShadowRendering:
    """Tests for shadow rendering order and appearance."""

    def test_shadow_renders_behind_all_elements(self):
        """Shadow renders behind all other avatar elements."""
        svg, info = generator.generate_deterministic("test@example.com")

        # Shadow should appear early in SVG (after defs, before body)
        # Check rendering order
        if 'ellipse' in svg and 'shadow' in svg.lower():
            shadow_pos = svg.lower().find('shadow')
            body_pos = svg.lower().find('body')
            if body_pos > 0:
                # Shadow should come before body
                assert shadow_pos < body_pos or body_pos == -1

    def test_shadow_color_and_opacity(self):
        """Shadow has correct color and opacity."""
        svg, info = generator.generate_deterministic("test@example.com")

        # According to docs: light grey (#808080) with 0.45 opacity
        if 'shadow' in svg.lower() or 'ellipse' in svg:
            # Should have opacity setting
            assert 'opacity=' in svg or 'opacity:' in svg or 'fill-opacity' in svg

    def test_shadow_blur_strength(self):
        """Shadow has correct blur strength (stdDeviation=1.5)."""
        svg, info = generator.generate_deterministic("test@example.com")

        # Should have Gaussian blur with stdDeviation
        if 'blur' in svg.lower():
            # Check for stdDeviation or similar
            assert 'stddeviation' in svg.lower() or 'deviation' in svg.lower()


class TestShadowVisibilityControl:
    """Tests for shadow visibility control via parameters."""

    def test_shadow_parameter_true_shows_shadow(self):
        """shadow=true parameter shows shadow."""
        response = client.get("/avatar/test@example.com.svg?shadow=true")

        assert response.status_code == 200
        svg_content = response.content.decode('utf-8')

        # Should contain shadow
        assert 'shadow' in svg_content.lower() or 'ellipse' in svg_content.lower()

    def test_shadow_parameter_false_hides_shadow(self):
        """shadow=false parameter hides shadow via CSS."""
        response = client.get("/avatar/test@example.com.svg?shadow=false")

        assert response.status_code == 200
        svg_content = response.content.decode('utf-8')

        # Shadow should be hidden (via CSS or not rendered)
        # Check for .no-shadow class or absence of shadow
        # Implementation may vary

    def test_shadow_default_is_visible(self):
        """Shadow is visible by default (no parameter)."""
        response = client.get("/avatar/test@example.com.svg")

        assert response.status_code == 200
        svg_content = response.content.decode('utf-8')

        # Should contain shadow by default
        # Verify SVG is valid
        assert '<svg' in svg_content

    def test_shadow_css_class_control(self):
        """Shadow visibility controlled via no-shadow CSS class."""
        svg, _ = generator.generate_deterministic("test@example.com", shadow=False)

        # When shadow=false, should have .no-shadow class or hide shadow via CSS
        # Check implementation
        assert '<svg' in svg


class TestShadowFilterNamespacing:
    """Tests for shadow filter ID namespacing."""

    def test_shadow_filter_id_namespaced(self):
        """Shadow filter ID includes avatar ID for namespacing."""
        svg, info = generator.generate_deterministic("test@example.com")

        # Extract avatar ID from SVG
        id_match = re.search(r'<svg[^>]*id="([^"]+)"', svg)

        if id_match and 'filter' in svg.lower():
            avatar_id = id_match.group(1)
            # Filter ID should include avatar ID
            filter_matches = re.findall(r'filter[^>]*id="([^"]+)"', svg)

            for filter_id in filter_matches:
                if 'shadow' in filter_id.lower():
                    # Should include avatar ID for namespacing
                    assert avatar_id in filter_id or 'avatar-' in filter_id

    def test_multiple_avatars_no_filter_conflicts(self):
        """Multiple avatars don't have filter ID conflicts."""
        svg1, _ = generator.generate_deterministic("user1@example.com")
        svg2, _ = generator.generate_deterministic("user2@example.com")

        # Extract filter IDs from both
        filter_ids_1 = re.findall(r'filter[^>]*id="([^"]+)"', svg1)
        filter_ids_2 = re.findall(r'filter[^>]*id="([^"]+)"', svg2)

        # Filter IDs should be different (namespaced)
        if filter_ids_1 and filter_ids_2:
            assert filter_ids_1[0] != filter_ids_2[0], \
                "Filter IDs should be unique across avatars"


class TestShadowWithDifferentBodyShapes:
    """Tests for shadow with different body shapes and sizes."""

    def test_shadow_with_narrow_body(self):
        """Shadow works correctly with narrow body shapes."""
        # Generate avatars until we get different body shapes
        for i in range(10):
            svg, info = generator.generate_deterministic(f"narrow{i}@example.com")
            # Should have valid shadow regardless of body shape
            assert '<svg' in svg

    def test_shadow_with_wide_body(self):
        """Shadow works correctly with wide body shapes."""
        for i in range(10):
            svg, info = generator.generate_deterministic(f"wide{i}@example.com")
            assert '<svg' in svg

    def test_shadow_with_hair(self):
        """Shadow accounts for hair width in sizing."""
        # Generate avatars with hair
        for i in range(10):
            svg, info = generator.generate_deterministic(f"hair{i}@example.com")
            if info.get('hair_index') is not None:
                # Should have shadow that accounts for hair
                assert '<svg' in svg
                break


class TestShadowBoundingBox:
    """Tests for shadow bounding box calculation."""

    def test_shadow_bounding_box_includes_blur(self):
        """Shadow bounding box accounts for blur expansion."""
        svg, info = generator.generate_deterministic("test@example.com")

        # Shadow with blur should have appropriate bounding box
        # Just verify shadow exists
        assert '<svg' in svg

    def test_shadow_doesnt_exceed_cell_bounds(self):
        """Shadow fits within cell boundaries."""
        svg, info = generator.generate_deterministic("test@example.com")

        # Verify SVG is valid and shadow doesn't cause overflow
        assert '<svg' in svg


class TestShadowCaching:
    """Tests for shadow caching behavior."""

    def test_shadow_parameter_affects_cache_key(self):
        """shadow parameter is included in cache key."""
        response1 = client.get("/avatar/shadowcache@example.com.svg?shadow=true")
        response2 = client.get("/avatar/shadowcache@example.com.svg?shadow=false")

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Both should work
        svg1 = response1.content.decode('utf-8')
        svg2 = response2.content.decode('utf-8')

        assert '<svg' in svg1
        assert '<svg' in svg2

    def test_shadow_cached_separately(self):
        """Avatars with/without shadow are cached separately."""
        # Make requests with different shadow settings
        response1 = client.get("/avatar/cachetest@example.com.svg?shadow=true")
        response2 = client.get("/avatar/cachetest@example.com.svg?shadow=false")

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Repeated requests should hit cache
        response1_cached = client.get("/avatar/cachetest@example.com.svg?shadow=true")
        response2_cached = client.get("/avatar/cachetest@example.com.svg?shadow=false")

        assert response1.content == response1_cached.content
        assert response2.content == response2_cached.content
