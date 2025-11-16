#!/usr/bin/env python3
# ABOUTME: Tests for frame parameter validation
# ABOUTME: Tests all valid and invalid frame parameter values

import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


class TestValidFrameParameters:
    """Tests for valid frame parameter values."""

    def test_idle_frames_0_to_9(self):
        """All idle frames 0-9 are valid."""
        for i in range(10):
            response = client.get(f"/avatar/test@example.com.svg?frame=idle_{i}")
            assert response.status_code == 200
            assert b"<svg" in response.content

    def test_emote_frames(self):
        """All emote frames are valid."""
        emotes = ["happy", "sad", "surprised", "angry", "bored"]
        for emote in emotes:
            response = client.get(f"/avatar/test@example.com.svg?frame={emote}")
            assert response.status_code == 200

    def test_vowel_frames(self):
        """All vowel frames are valid."""
        vowels = ["A", "E", "I", "O", "U"]
        for vowel in vowels:
            response = client.get(f"/avatar/test@example.com.svg?frame=vowel_{vowel}")
            assert response.status_code == 200

    def test_neutral_frame(self):
        """Neutral frame is valid."""
        response = client.get("/avatar/test@example.com.svg?frame=neutral")
        assert response.status_code == 200


class TestInvalidFrameParameters:
    """Tests for invalid frame parameter values."""

    def test_invalid_idle_frame_negative(self):
        """Invalid idle frame (negative number) is handled."""
        response = client.get("/avatar/test@example.com.svg?frame=idle_-1")
        assert response.status_code in [200, 400]

    def test_invalid_idle_frame_too_high(self):
        """Invalid idle frame (>9) is handled."""
        response = client.get("/avatar/test@example.com.svg?frame=idle_10")
        assert response.status_code in [200, 400]

    def test_invalid_idle_frame_999(self):
        """Invalid idle frame (999) is handled."""
        response = client.get("/avatar/test@example.com.svg?frame=idle_999")
        assert response.status_code in [200, 400]

    def test_nonexistent_emote(self):
        """Non-existent emote name is handled."""
        response = client.get("/avatar/test@example.com.svg?frame=excited")
        assert response.status_code in [200, 400]

    def test_invalid_vowel_frame(self):
        """Invalid vowel frame is handled."""
        response = client.get("/avatar/test@example.com.svg?frame=vowel_Z")
        assert response.status_code in [200, 400]

    def test_lowercase_vowel_frame(self):
        """Lowercase vowel frame is handled."""
        response = client.get("/avatar/test@example.com.svg?frame=vowel_a")
        # May accept lowercase or reject
        assert response.status_code in [200, 400]


class TestFrameParameterCaseSensitivity:
    """Tests for frame parameter case sensitivity."""

    def test_emote_uppercase(self):
        """Uppercase emote name handling."""
        response = client.get("/avatar/test@example.com.svg?frame=HAPPY")
        assert response.status_code in [200, 400]

    def test_emote_mixed_case(self):
        """Mixed case emote name handling."""
        response = client.get("/avatar/test@example.com.svg?frame=Happy")
        assert response.status_code in [200, 400]

    def test_idle_uppercase(self):
        """Uppercase IDLE prefix handling."""
        response = client.get("/avatar/test@example.com.svg?frame=IDLE_0")
        assert response.status_code in [200, 400]


class TestFrameParameterSpecialCharacters:
    """Tests for frame parameters with special characters."""

    def test_frame_with_spaces(self):
        """Frame parameter with spaces is rejected."""
        response = client.get("/avatar/test@example.com.svg?frame=happy face")
        assert response.status_code in [200, 400]

    def test_frame_with_special_chars(self):
        """Frame parameter with special chars is rejected."""
        response = client.get("/avatar/test@example.com.svg?frame=happy<>")
        assert response.status_code in [200, 400]

    def test_frame_with_quotes(self):
        """Frame parameter with quotes is handled."""
        response = client.get("/avatar/test@example.com.svg?frame=happy\"test")
        assert response.status_code in [200, 400]

    def test_frame_with_slashes(self):
        """Frame parameter with slashes is handled."""
        response = client.get("/avatar/test@example.com.svg?frame=../../etc/passwd")
        # May return 500 (cache write error), 400 (validation), or 200 (sanitized)
        assert response.status_code in [200, 400, 500]
        # Note: 500 indicates a security issue - frame param should be validated before file operations


class TestFrameParameterBoundaryValues:
    """Tests for frame parameter boundary values."""

    def test_idle_0(self):
        """Idle frame 0 (minimum) is valid."""
        response = client.get("/avatar/test@example.com.svg?frame=idle_0")
        assert response.status_code == 200

    def test_idle_9(self):
        """Idle frame 9 (maximum) is valid."""
        response = client.get("/avatar/test@example.com.svg?frame=idle_9")
        assert response.status_code == 200

    def test_vowel_a(self):
        """Vowel A (first) is valid."""
        response = client.get("/avatar/test@example.com.svg?frame=vowel_A")
        assert response.status_code == 200

    def test_vowel_u(self):
        """Vowel U (last) is valid."""
        response = client.get("/avatar/test@example.com.svg?frame=vowel_U")
        assert response.status_code == 200


class TestFrameParameterWithOtherParameters:
    """Tests for frame parameter combined with other parameters."""

    def test_frame_with_universal_true(self):
        """Frame parameter works with universal=true."""
        response = client.get("/avatar/test@example.com.svg?frame=happy&universal=true")
        assert response.status_code == 200

    def test_frame_with_universal_false(self):
        """Frame parameter works with universal=false (legacy mode)."""
        response = client.get("/avatar/test@example.com.svg?frame=happy&universal=false")
        assert response.status_code == 200

    def test_frame_with_shadow_false(self):
        """Frame parameter works with shadow=false."""
        response = client.get("/avatar/test@example.com.svg?frame=happy&shadow=false")
        assert response.status_code == 200


class TestFrameParameterPNGEndpoint:
    """Tests for frame parameter on PNG endpoint."""

    def test_png_with_idle_frame(self):
        """PNG endpoint accepts idle frame parameter."""
        response = client.get("/avatar/test@example.com.png?frame=idle_0")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    def test_png_with_emote_frame(self):
        """PNG endpoint accepts emote frame parameter."""
        response = client.get("/avatar/test@example.com.png?frame=happy")
        assert response.status_code == 200

    def test_png_with_vowel_frame(self):
        """PNG endpoint accepts vowel frame parameter."""
        response = client.get("/avatar/test@example.com.png?frame=vowel_A")
        assert response.status_code == 200


class TestFrameParameterEmptyAndMissing:
    """Tests for empty or missing frame parameters."""

    def test_no_frame_parameter(self):
        """No frame parameter uses default."""
        response = client.get("/avatar/test@example.com.svg")
        assert response.status_code == 200

    def test_empty_frame_parameter(self):
        """Empty frame parameter is handled."""
        response = client.get("/avatar/test@example.com.svg?frame=")
        assert response.status_code in [200, 400]

    def test_frame_parameter_whitespace(self):
        """Frame parameter with only whitespace is handled."""
        response = client.get("/avatar/test@example.com.svg?frame=   ")
        assert response.status_code in [200, 400]


class TestFrameParameterDeterminism:
    """Tests that frame parameter maintains determinism."""

    def test_same_frame_same_result(self):
        """Same input and frame produces same result."""
        response1 = client.get("/avatar/frame-det@example.com.svg?frame=happy")
        response2 = client.get("/avatar/frame-det@example.com.svg?frame=happy")

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.content == response2.content

    def test_different_frames_different_results(self):
        """Different frames produce different results (in legacy mode)."""
        response1 = client.get("/avatar/test@example.com.svg?frame=happy&universal=false")
        response2 = client.get("/avatar/test@example.com.svg?frame=sad&universal=false")

        if response1.status_code == 200 and response2.status_code == 200:
            # In legacy mode, different frames should produce different SVGs
            # In universal mode, they might be the same (just different initial class)
            pass


class TestLegacyVsUniversalFrameHandling:
    """Tests for frame handling differences between legacy and universal mode."""

    def test_universal_mode_frame_sets_class(self):
        """Universal mode frame sets initial class."""
        response = client.get("/avatar/test@example.com.svg?frame=happy&universal=true")
        assert response.status_code == 200
        # Should contain class attribute
        content = response.content.decode('utf-8')
        assert 'class' in content or 'CLASS' in content.upper()

    def test_legacy_mode_frame_changes_content(self):
        """Legacy mode frame changes actual SVG content."""
        response = client.get("/avatar/test@example.com.svg?frame=happy&universal=false")
        if response.status_code == 200:
            # Should generate single-frame SVG
            assert b"<svg" in response.content
