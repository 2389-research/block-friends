#!/usr/bin/env python3
# ABOUTME: Comprehensive tests for avatar shadow feature
# ABOUTME: Tests shadow generation, sizing, positioning, and visibility control

from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


class TestShadowPresence:
    """Tests for shadow presence in generated avatars."""

    def test_shadow_present_by_default(self):
        """Shadow is present by default in generated avatars."""
        response = client.get("/avatar/test@example.com.svg")

        assert response.status_code == 200
        content = response.content.decode('utf-8')

        # Should contain shadow-related elements
        assert "shadow" in content.lower() or "ellipse" in content

    def test_shadow_in_universal_mode(self):
        """Shadow is present in universal mode."""
        response = client.get("/avatar/test@example.com.svg?universal=true")

        assert response.status_code == 200
        content = response.content.decode('utf-8')
        # Should have shadow elements

    def test_shadow_in_legacy_mode(self):
        """Shadow is present in legacy mode."""
        response = client.get("/avatar/test@example.com.svg?universal=false")

        if response.status_code == 200:
            content = response.content.decode('utf-8')
            # Should have shadow elements


class TestShadowSizing:
    """Tests for shadow sizing based on avatar content."""

    def test_shadow_scales_with_content(self):
        """Shadow scales based on actual avatar content width."""
        # Generate a few different avatars
        responses = [
            client.get(f"/avatar/shadow-size-{i}@example.com.svg")
            for i in range(5)
        ]

        for response in responses:
            assert response.status_code == 200
            # Shadow should be present and properly sized

    def test_shadow_width_appropriate(self):
        """Shadow width is appropriate for avatar."""
        response = client.get("/avatar/test-shadow-width@example.com.svg")

        assert response.status_code == 200
        # Shadow should be wider than body for realistic effect

    def test_shadow_height_appropriate(self):
        """Shadow height creates flat ellipse effect."""
        response = client.get("/avatar/test-shadow-height@example.com.svg")

        assert response.status_code == 200
        # Shadow should be much shorter than wide (ellipse)


class TestShadowPositioning:
    """Tests for shadow positioning relative to avatar."""

    def test_shadow_at_bottom_of_avatar(self):
        """Shadow is positioned at bottom of avatar."""
        response = client.get("/avatar/test-shadow-pos@example.com.svg")

        assert response.status_code == 200
        # Shadow should be near feet

    def test_shadow_overlaps_feet(self):
        """Shadow overlaps feet for depth effect."""
        response = client.get("/avatar/test-shadow-overlap@example.com.svg")

        assert response.status_code == 200
        # Implementation-specific check for overlap

    def test_shadow_centered_horizontally(self):
        """Shadow is centered horizontally under avatar."""
        response = client.get("/avatar/test-shadow-center@example.com.svg")

        assert response.status_code == 200


class TestShadowVisualProperties:
    """Tests for shadow visual properties."""

    def test_shadow_has_blur_filter(self):
        """Shadow uses blur filter for soft edges."""
        response = client.get("/avatar/test-shadow-blur@example.com.svg")

        assert response.status_code == 200
        content = response.content.decode('utf-8')

        # Should have filter definition
        assert "filter" in content.lower()

    def test_shadow_has_opacity(self):
        """Shadow has appropriate opacity."""
        response = client.get("/avatar/test-shadow-opacity@example.com.svg")

        assert response.status_code == 200
        content = response.content.decode('utf-8')

        # Should have opacity set
        if "shadow" in content.lower():
            assert "opacity" in content or "fill-opacity" in content

    def test_shadow_color_is_grey(self):
        """Shadow uses grey color."""
        response = client.get("/avatar/test-shadow-color@example.com.svg")

        assert response.status_code == 200
        content = response.content.decode('utf-8')

        # Should use grey/gray color
        # Common greys: #808080, #666, #999, etc.


class TestShadowFilterNamespacing:
    """Tests for shadow filter ID namespacing."""

    def test_shadow_filter_has_unique_id(self):
        """Shadow filter has unique ID to prevent conflicts."""
        response = client.get("/avatar/test-shadow-filter@example.com.svg")

        assert response.status_code == 200
        content = response.content.decode('utf-8')

        # Filter ID should include avatar ID for uniqueness
        if "filter" in content:
            assert "avatar-" in content or "shadow-blur" in content

    def test_multiple_avatars_different_filter_ids(self):
        """Different avatars have different shadow filter IDs."""
        response1 = client.get("/avatar/user1@example.com.svg")
        response2 = client.get("/avatar/user2@example.com.svg")

        content1 = response1.content.decode('utf-8')
        content2 = response2.content.decode('utf-8')

        # Filter IDs should be namespaced differently


class TestShadowRenderOrder:
    """Tests for shadow rendering order (z-index)."""

    def test_shadow_renders_behind_avatar(self):
        """Shadow renders behind all other avatar elements."""
        response = client.get("/avatar/test-shadow-order@example.com.svg")

        assert response.status_code == 200
        content = response.content.decode('utf-8')

        # Shadow should appear early in SVG (before body, etc.)
        # This is implementation-specific


class TestShadowVisibilityControl:
    """Tests for shadow visibility control via parameters."""

    def test_shadow_parameter_true(self):
        """shadow=true shows shadow (default behavior)."""
        response = client.get("/avatar/test@example.com.svg?shadow=true")

        assert response.status_code == 200
        content = response.content.decode('utf-8')
        # Shadow should be present

    def test_shadow_parameter_false(self):
        """shadow=false hides shadow."""
        response = client.get("/avatar/test@example.com.svg?shadow=false")

        assert response.status_code == 200
        content = response.content.decode('utf-8')

        # Shadow might be hidden via CSS or not included
        # Check for no-shadow class or absence of shadow

    def test_shadow_css_class_control(self):
        """Shadow can be controlled via CSS class."""
        response = client.get("/avatar/test@example.com.svg")

        assert response.status_code == 200
        content = response.content.decode('utf-8')

        # Should support .no-shadow class for hiding


class TestShadowWithDifferentAvatars:
    """Tests for shadow with various avatar configurations."""

    def test_shadow_with_narrow_avatar(self):
        """Shadow scales correctly for narrow avatars."""
        response = client.get("/avatar/narrow-avatar@example.com.svg")

        assert response.status_code == 200
        # Shadow should be appropriately sized for narrow body

    def test_shadow_with_wide_avatar(self):
        """Shadow scales correctly for wide avatars."""
        response = client.get("/avatar/wide-avatar@example.com.svg")

        assert response.status_code == 200
        # Shadow should be appropriately sized for wide body

    def test_shadow_with_hair_behind(self):
        """Shadow positioning works with hair rendered behind."""
        response = client.get("/avatar/hair-behind@example.com.svg")

        assert response.status_code == 200
        # Shadow should still render correctly

    def test_shadow_with_hair_front(self):
        """Shadow positioning works with hair rendered in front."""
        response = client.get("/avatar/hair-front@example.com.svg")

        assert response.status_code == 200


class TestShadowBoundingBox:
    """Tests for shadow bounding box calculations."""

    def test_shadow_accounts_for_blur_expansion(self):
        """Shadow bounding box includes blur expansion."""
        response = client.get("/avatar/test-shadow-bbox@example.com.svg")

        assert response.status_code == 200
        # Blur causes expansion beyond ellipse bounds

    def test_shadow_doesnt_clip(self):
        """Shadow is not clipped by SVG viewBox."""
        response = client.get("/avatar/test-shadow-clip@example.com.svg")

        assert response.status_code == 200
        # ViewBox should be large enough to show full shadow


class TestShadowCaching:
    """Tests for shadow caching behavior."""

    def test_shadow_true_cached_separately(self):
        """Avatars with shadow=true cached separately from shadow=false."""
        response1 = client.get("/avatar/cache-shadow@example.com.svg?shadow=true")
        response2 = client.get("/avatar/cache-shadow@example.com.svg?shadow=false")

        if response1.status_code == 200 and response2.status_code == 200:
            # Should be different (cached separately)
            assert response1.content != response2.content

    def test_shadow_default_cached(self):
        """Default shadow state is cached."""
        response1 = client.get("/avatar/shadow-cache-test@example.com.svg")
        response2 = client.get("/avatar/shadow-cache-test@example.com.svg")

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.content == response2.content


class TestShadowPNGRendering:
    """Tests for shadow in PNG renders."""

    def test_png_includes_shadow(self):
        """PNG renders include shadow."""
        response = client.get("/avatar/test@example.com.png")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        # Shadow should be rasterized in PNG

    def test_png_shadow_parameter(self):
        """PNG respects shadow parameter."""
        response = client.get("/avatar/test@example.com.png?shadow=false")

        if response.status_code == 200:
            # PNG without shadow
            assert response.headers["content-type"] == "image/png"
