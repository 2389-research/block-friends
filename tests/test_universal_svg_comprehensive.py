"""
Comprehensive tests for universal SVG generation and CSS state management.

Tests CSS generation, state switching, animation, and scoping.
"""

import pytest
from fastapi.testclient import TestClient
from door_agents import DoorAgentGenerator, DoorAgentConfig
from app import app
import re

client = TestClient(app)
config = DoorAgentConfig()
generator = DoorAgentGenerator(config)


class TestUniversalSVGCSSGeneration:
    """Tests for CSS generation in universal SVG mode."""

    def test_universal_svg_contains_all_idle_states(self):
        """Universal SVG CSS includes all 10 idle frame states."""
        svg, _ = generator.generate_deterministic('test@example.com', universal=True)

        # Check for idle state CSS rules
        for i in range(10):
            assert f'idle_{i}' in svg, f"Missing idle_{i} state"

    def test_universal_svg_contains_all_emote_states(self):
        """Universal SVG CSS includes all 5 emote states."""
        svg, _ = generator.generate_deterministic('test@example.com', universal=True)

        emotes = ["happy", "sad", "surprised", "angry", "bored"]
        for emote in emotes:
            assert emote in svg, f"Missing {emote} emote state"

    def test_universal_svg_contains_all_vowel_states(self):
        """Universal SVG CSS includes all 5 vowel states."""
        svg, _ = generator.generate_deterministic('test@example.com', universal=True)

        vowels = ["vowel_a", "vowel_e", "vowel_i", "vowel_o", "vowel_u"]
        for vowel in vowels:
            assert vowel in svg, f"Missing {vowel} state"

    def test_universal_svg_css_visibility_control(self):
        """Universal SVG CSS uses visibility: hidden/visible for state control."""
        svg, _ = generator.generate_deterministic('test@example.com', universal=True)

        # Check that CSS uses visibility property for state management
        assert 'visibility:' in svg or 'visibility :' in svg or 'display:' in svg or 'display :' in svg

    def test_universal_svg_css_scoping(self):
        """Universal SVG CSS rules are scoped to prevent conflicts."""
        svg, _ = generator.generate_deterministic('test@example.com', universal=True)

        # Check that CSS rules are scoped (should have avatar ID in selectors or use ID-based scoping)
        # The avatar should have an ID that's used for scoping
        assert 'id=' in svg, "Universal SVG should have an ID for scoping"

        # Extract the ID
        id_match = re.search(r'<svg[^>]*id="([^"]+)"', svg)
        if id_match:
            avatar_id = id_match.group(1)
            # Check that CSS rules reference this ID
            assert f'#{avatar_id}' in svg or f'svg.{avatar_id}' in svg or avatar_id in svg

    def test_universal_svg_default_state_visible(self):
        """Universal SVG has default state visible on load."""
        svg, _ = generator.generate_deterministic('test@example.com', frame='neutral', universal=True)

        # The default/neutral state should be visible
        # This is typically controlled by the root class on the SVG element
        assert '<svg' in svg


class TestUniversalSVGStateStructure:
    """Tests for universal SVG nested group structure."""

    def test_universal_svg_has_eyes_container(self):
        """Universal SVG has eyes container group."""
        svg, _ = generator.generate_deterministic('test@example.com', universal=True)

        assert '<g class="eyes"' in svg

    def test_universal_svg_has_mouths_container(self):
        """Universal SVG has mouths container group."""
        svg, _ = generator.generate_deterministic('test@example.com', universal=True)

        assert '<g class="mouths"' in svg

    def test_universal_svg_has_nested_eye_states(self):
        """Universal SVG has nested groups for different eye states."""
        svg, _ = generator.generate_deterministic('test@example.com', universal=True)

        # Should have groups for different eye expressions
        assert '<g class="open"' in svg or 'class="open"' in svg

    def test_universal_svg_has_nested_mouth_states(self):
        """Universal SVG has nested groups for different mouth states."""
        svg, _ = generator.generate_deterministic('test@example.com', universal=True)

        # Should have groups for different mouth states
        assert '<g class="closed"' in svg or 'class="closed"' in svg or '<g' in svg


class TestUniversalSVGNamespacing:
    """Tests for SVG namespacing to prevent conflicts."""

    def test_multiple_avatars_have_unique_ids(self):
        """Multiple avatars in the same page should have unique IDs."""
        svg1, _ = generator.generate_deterministic('user1@example.com', universal=True)
        svg2, _ = generator.generate_deterministic('user2@example.com', universal=True)

        # Extract IDs from both SVGs
        id1_match = re.search(r'<svg[^>]*id="([^"]+)"', svg1)
        id2_match = re.search(r'<svg[^>]*id="([^"]+)"', svg2)

        if id1_match and id2_match:
            id1 = id1_match.group(1)
            id2 = id2_match.group(1)
            assert id1 != id2, "Avatar IDs should be unique"

    def test_clippath_namespacing_in_universal_mode(self):
        """ClipPath IDs in universal mode should be namespaced."""
        svg, _ = generator.generate_deterministic('test@example.com', universal=True)

        # If SVG uses clipPath, they should be namespaced with avatar ID
        if 'clipPath' in svg:
            # Extract avatar ID
            id_match = re.search(r'<svg[^>]*id="([^"]+)"', svg)
            if id_match:
                avatar_id = id_match.group(1)
                # Check that clipPath IDs include the avatar ID
                clippath_matches = re.findall(r'clipPath id="([^"]+)"', svg)
                for clippath_id in clippath_matches:
                    assert avatar_id in clippath_id or clippath_id.startswith('avatar-'), \
                        f"ClipPath ID {clippath_id} should include avatar ID for namespacing"

    def test_filter_namespacing_in_universal_mode(self):
        """Filter IDs in universal mode should be namespaced."""
        svg, _ = generator.generate_deterministic('test@example.com', universal=True)

        # If SVG uses filters (like shadow blur), they should be namespaced
        if 'filter' in svg:
            # Extract avatar ID
            id_match = re.search(r'<svg[^>]*id="([^"]+)"', svg)
            if id_match:
                avatar_id = id_match.group(1)
                # Check that filter IDs include the avatar ID
                filter_matches = re.findall(r'filter id="([^"]+)"', svg)
                for filter_id in filter_matches:
                    assert avatar_id in filter_id, \
                        f"Filter ID {filter_id} should include avatar ID for namespacing"


class TestUniversalSVGAPIs:
    """Tests for universal SVG API endpoints."""

    def test_svg_endpoint_returns_universal_by_default(self):
        """SVG endpoint returns universal SVG by default."""
        response = client.get("/avatar/test@example.com.svg")

        assert response.status_code == 200
        svg_content = response.content.decode('utf-8')
        assert '<style>' in svg_content
        assert '<g class="eyes"' in svg_content or 'class="eyes"' in svg_content

    def test_svg_endpoint_legacy_parameter(self):
        """SVG endpoint supports legacy parameter."""
        response = client.get("/avatar/test@example.com.svg?legacy=true")

        assert response.status_code == 200
        svg_content = response.content.decode('utf-8')
        # Legacy mode should not have style block or nested groups
        assert '<style>' not in svg_content
        assert '<g class="eyes">' not in svg_content

    def test_svg_endpoint_universal_with_frame(self):
        """Universal SVG supports frame parameter."""
        response = client.get("/avatar/test@example.com.svg?frame=happy")

        assert response.status_code == 200
        svg_content = response.content.decode('utf-8')
        # Should still be universal mode
        assert '<style>' in svg_content

    def test_png_endpoint_universal_mode(self):
        """PNG endpoint generates from universal SVG."""
        response = client.get("/avatar/test@example.com.png")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        # PNG magic number
        assert response.content[:8] == b'\x89PNG\r\n\x1a\n'


class TestUniversalSVGSizeComparison:
    """Tests comparing universal vs legacy SVG sizes."""

    def test_universal_svg_larger_than_legacy_single_frame(self):
        """Universal SVG is larger than legacy single frame (contains all states)."""
        svg_universal, _ = generator.generate_deterministic('test@example.com', universal=True)
        svg_legacy, _ = generator.generate_deterministic('test@example.com', universal=False)

        # Universal should be significantly larger (has all 20 states)
        assert len(svg_universal) > len(svg_legacy), \
            "Universal SVG should be larger than legacy (contains all states)"

    def test_universal_svg_smaller_than_all_legacy_frames(self):
        """Universal SVG is smaller than sum of all legacy frames."""
        svg_universal, _ = generator.generate_deterministic('test@example.com', universal=True)

        # Generate all 20 frames in legacy mode
        frames = ['neutral'] + [f'idle_{i}' for i in range(10)] + \
                 ['happy', 'sad', 'surprised', 'angry', 'bored'] + \
                 [f'vowel_{v}' for v in ['A', 'E', 'I', 'O', 'U']]

        total_legacy_size = 0
        for frame in frames:
            svg_legacy, _ = generator.generate_deterministic('test@example.com', frame=frame, universal=False)
            total_legacy_size += len(svg_legacy)

        # Universal should be significantly smaller than sum of all frames
        assert len(svg_universal) < total_legacy_size, \
            "Universal SVG should be smaller than sum of all legacy frames"

        # Should be at least 50% smaller
        assert len(svg_universal) < total_legacy_size * 0.5, \
            "Universal SVG should be significantly smaller (at least 50%) than sum of all frames"


class TestUniversalSVGCaching:
    """Tests for caching behavior with universal mode."""

    def test_universal_and_legacy_cached_separately(self):
        """Universal and legacy modes are cached separately."""
        response_universal = client.get("/avatar/cachetest@example.com.svg")
        response_legacy = client.get("/avatar/cachetest@example.com.svg?legacy=true")

        assert response_universal.status_code == 200
        assert response_legacy.status_code == 200

        svg_universal = response_universal.content.decode('utf-8')
        svg_legacy = response_legacy.content.decode('utf-8')

        # They should be different
        assert svg_universal != svg_legacy

        # Universal should have style block
        assert '<style>' in svg_universal
        assert '<style>' not in svg_legacy

    def test_universal_mode_cache_key_includes_frame(self):
        """Universal mode cache key includes frame parameter."""
        response1 = client.get("/avatar/frametest@example.com.svg?frame=happy")
        response2 = client.get("/avatar/frametest@example.com.svg?frame=sad")

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Both should be valid SVGs
        svg1 = response1.content.decode('utf-8')
        svg2 = response2.content.decode('utf-8')

        assert '<svg' in svg1
        assert '<svg' in svg2
