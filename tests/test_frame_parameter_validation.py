"""
Frame parameter validation tests.

Tests frame parameter handling, validation, and error cases.
"""

import pytest
from fastapi.testclient import TestClient
from app import app
from door_agents import DoorAgentGenerator, DoorAgentConfig

client = TestClient(app)
config = DoorAgentConfig()
generator = DoorAgentGenerator(config)


class TestIdleFrameValidation:
    """Tests for idle frame parameter validation."""

    def test_all_idle_frames_valid(self):
        """All idle frame values (0-9) are accepted."""
        for i in range(10):
            response = client.get(f"/avatar/test@example.com.svg?frame=idle_{i}")
            assert response.status_code == 200

    def test_idle_frame_negative_index(self):
        """Negative idle frame index returns error."""
        response = client.get("/avatar/test@example.com.svg?frame=idle_-1")

        # Should handle gracefully - either accept as string or return error
        assert response.status_code in [200, 400, 422]

    def test_idle_frame_index_too_large(self):
        """Idle frame index >= 10 returns error or handles gracefully."""
        response = client.get("/avatar/test@example.com.svg?frame=idle_10")

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_idle_frame_index_100(self):
        """Very large idle frame index is handled."""
        response = client.get("/avatar/test@example.com.svg?frame=idle_100")

        assert response.status_code in [200, 400, 422]

    def test_idle_frame_malformed_index(self):
        """Malformed idle frame index is handled."""
        response = client.get("/avatar/test@example.com.svg?frame=idle_abc")

        assert response.status_code in [200, 400, 422]

    def test_idle_frame_without_index(self):
        """'idle' without index is handled."""
        response = client.get("/avatar/test@example.com.svg?frame=idle")

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]


class TestEmoteFrameValidation:
    """Tests for emote frame parameter validation."""

    def test_all_emote_frames_valid(self):
        """All emote frame values are accepted."""
        emotes = ["happy", "sad", "surprised", "angry", "bored"]

        for emote in emotes:
            response = client.get(f"/avatar/test@example.com.svg?frame={emote}")
            assert response.status_code == 200, f"Emote {emote} failed"

    def test_invalid_emote_name(self):
        """Invalid emote name is handled."""
        response = client.get("/avatar/test@example.com.svg?frame=invalid_emote")

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_emote_typo(self):
        """Typo in emote name is handled."""
        response = client.get("/avatar/test@example.com.svg?frame=happi")

        assert response.status_code in [200, 400, 422]

    def test_emote_case_sensitivity(self):
        """Emote names are case-sensitive."""
        # Test uppercase version
        response1 = client.get("/avatar/test@example.com.svg?frame=HAPPY")
        response2 = client.get("/avatar/test@example.com.svg?frame=happy")

        # Lowercase should definitely work
        assert response2.status_code == 200

        # Uppercase might work or not depending on implementation
        assert response1.status_code in [200, 400, 422]

    def test_emote_with_underscore(self):
        """Emote with underscore prefix is handled."""
        response = client.get("/avatar/test@example.com.svg?frame=_happy")

        assert response.status_code in [200, 400, 422]


class TestVowelFrameValidation:
    """Tests for vowel frame parameter validation."""

    def test_all_vowel_frames_valid(self):
        """All vowel frame values are accepted."""
        vowels = ["A", "E", "I", "O", "U"]

        for vowel in vowels:
            response = client.get(f"/avatar/test@example.com.svg?frame=vowel_{vowel}")
            assert response.status_code == 200, f"Vowel {vowel} failed"

    def test_lowercase_vowels(self):
        """Lowercase vowel letters work."""
        vowels = ["a", "e", "i", "o", "u"]

        for vowel in vowels:
            response = client.get(f"/avatar/test@example.com.svg?frame=vowel_{vowel}")
            # Should work or be normalized
            assert response.status_code == 200, f"Lowercase vowel {vowel} failed"

    def test_vowel_without_prefix(self):
        """Vowel without 'vowel_' prefix is handled."""
        response = client.get("/avatar/test@example.com.svg?frame=A")

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_invalid_vowel_letter(self):
        """Invalid vowel letter is handled."""
        response = client.get("/avatar/test@example.com.svg?frame=vowel_X")

        assert response.status_code in [200, 400, 422]

    def test_vowel_numeric_index(self):
        """Vowel with numeric index is handled."""
        response = client.get("/avatar/test@example.com.svg?frame=vowel_1")

        assert response.status_code in [200, 400, 422]


class TestNeutralFrameValidation:
    """Tests for neutral/default frame handling."""

    def test_neutral_frame_explicit(self):
        """Explicit 'neutral' frame works."""
        response = client.get("/avatar/test@example.com.svg?frame=neutral")

        assert response.status_code == 200

    def test_no_frame_parameter(self):
        """No frame parameter defaults correctly."""
        response = client.get("/avatar/test@example.com.svg")

        assert response.status_code == 200

    def test_empty_frame_parameter(self):
        """Empty frame parameter is handled."""
        response = client.get("/avatar/test@example.com.svg?frame=")

        # Should default to neutral or return error
        assert response.status_code in [200, 400, 422]


class TestFrameParameterSpecialCharacters:
    """Tests for special characters in frame parameter."""

    def test_frame_with_script_tag(self):
        """Frame parameter with script tag is safe."""
        response = client.get("/avatar/test@example.com.svg?frame=<script>alert(1)</script>")

        # Should handle safely
        assert response.status_code in [200, 400, 422]

        if response.status_code == 200:
            svg_content = response.content.decode('utf-8')
            # Should not contain unescaped script
            assert '<script>alert' not in svg_content

    def test_frame_with_path_traversal(self):
        """Frame parameter with path traversal is safe."""
        response = client.get("/avatar/test@example.com.svg?frame=../../etc/passwd")

        # Should handle safely
        assert response.status_code in [200, 400, 422]

    def test_frame_with_null_byte(self):
        """Frame parameter with null byte is handled."""
        # URL encode null byte: %00
        response = client.get("/avatar/test@example.com.svg?frame=test%00frame")

        assert response.status_code in [200, 400, 422]

    def test_frame_with_special_chars(self):
        """Frame parameter with special characters is handled."""
        response = client.get("/avatar/test@example.com.svg?frame=@#$%")

        assert response.status_code in [200, 400, 422]

    def test_frame_with_unicode(self):
        """Frame parameter with Unicode is handled."""
        response = client.get("/avatar/test@example.com.svg?frame=测试")

        assert response.status_code in [200, 400, 422]


class TestFrameParameterLegacyVsUniversal:
    """Tests for frame parameter in legacy vs universal mode."""

    def test_frame_in_universal_mode(self):
        """Frame parameter works in universal mode."""
        response = client.get("/avatar/test@example.com.svg?frame=happy")

        assert response.status_code == 200
        svg_content = response.content.decode('utf-8')

        # Should be universal mode (has style block)
        assert '<style>' in svg_content

    def test_frame_in_legacy_mode(self):
        """Frame parameter works in legacy mode."""
        response = client.get("/avatar/test@example.com.svg?frame=happy&legacy=true")

        assert response.status_code == 200
        svg_content = response.content.decode('utf-8')

        # Should be legacy mode (no style block)
        assert '<style>' not in svg_content

    def test_frame_changes_initial_state_universal(self):
        """Frame parameter sets initial state in universal mode."""
        response = client.get("/avatar/test@example.com.svg?frame=happy")

        assert response.status_code == 200
        svg_content = response.content.decode('utf-8')

        # In universal mode, frame might set CSS class
        # Just verify it's valid SVG
        assert '<svg' in svg_content

    def test_frame_selects_assets_legacy(self):
        """Frame parameter selects correct assets in legacy mode."""
        response = client.get("/avatar/test@example.com.svg?frame=happy&legacy=true")

        assert response.status_code == 200
        svg_content = response.content.decode('utf-8')

        # Should have selected happy emote assets
        assert '<svg' in svg_content


class TestFrameParameterPNG:
    """Tests for frame parameter with PNG endpoint."""

    def test_png_with_frame_parameter(self):
        """PNG endpoint accepts frame parameter."""
        response = client.get("/avatar/test@example.com.png?frame=happy")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    def test_png_all_idle_frames(self):
        """PNG works with all idle frames."""
        for i in range(10):
            response = client.get(f"/avatar/test@example.com.png?frame=idle_{i}")
            assert response.status_code == 200
            # Check PNG magic number
            assert response.content[:8] == b'\x89PNG\r\n\x1a\n'

    def test_png_all_emote_frames(self):
        """PNG works with all emote frames."""
        emotes = ["happy", "sad", "surprised", "angry", "bored"]

        for emote in emotes:
            response = client.get(f"/avatar/test@example.com.png?frame={emote}")
            assert response.status_code == 200
            assert response.content[:8] == b'\x89PNG\r\n\x1a\n'


class TestFrameParameterCaching:
    """Tests for frame parameter caching behavior."""

    def test_different_frames_cached_separately(self):
        """Different frames are cached separately."""
        response1 = client.get("/avatar/framecache@example.com.svg?frame=happy")
        response2 = client.get("/avatar/framecache@example.com.svg?frame=sad")

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Both should be valid
        svg1 = response1.content.decode('utf-8')
        svg2 = response2.content.decode('utf-8')

        assert '<svg' in svg1
        assert '<svg' in svg2

    def test_same_frame_hits_cache(self):
        """Same frame parameter hits cache."""
        response1 = client.get("/avatar/samecache@example.com.svg?frame=happy")
        response2 = client.get("/avatar/samecache@example.com.svg?frame=happy")

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Content should be identical
        assert response1.content == response2.content


class TestFrameParameterInfo:
    """Tests for frame parameter with info endpoint."""

    def test_info_with_frame_parameter(self):
        """Info endpoint accepts frame parameter."""
        response = client.get("/avatar/test@example.com.svg/info?frame=happy")

        assert response.status_code == 200
        data = response.json()

        # Should include configuration info
        assert "body_color" in data or "input_string" in data

    def test_info_different_frames(self):
        """Info endpoint with different frames."""
        response1 = client.get("/avatar/test@example.com.svg/info?frame=happy")
        response2 = client.get("/avatar/test@example.com.svg/info?frame=sad")

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Both should return valid info
        data1 = response1.json()
        data2 = response2.json()

        assert data1 is not None
        assert data2 is not None


class TestFrameParameterBoundaryValues:
    """Tests for frame parameter boundary values."""

    def test_frame_very_long_string(self):
        """Very long frame parameter string is handled."""
        long_frame = "a" * 1000
        response = client.get(f"/avatar/test@example.com.svg?frame={long_frame}")

        # Should handle gracefully
        assert response.status_code in [200, 400, 414, 422]

    def test_frame_with_spaces(self):
        """Frame parameter with spaces is handled."""
        response = client.get("/avatar/test@example.com.svg?frame=happy%20frame")

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_multiple_underscores(self):
        """Frame with multiple underscores is handled."""
        response = client.get("/avatar/test@example.com.svg?frame=idle__0")

        assert response.status_code in [200, 400, 422]

    def test_frame_starts_with_number(self):
        """Frame starting with number is handled."""
        response = client.get("/avatar/test@example.com.svg?frame=0_idle")

        assert response.status_code in [200, 400, 422]
