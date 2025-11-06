"""
API integration tests for avatar service endpoints.

Tests all HTTP endpoints to ensure correct responses, headers, and error handling.
"""

import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


class TestAvatarSVGEndpoint:
    """Tests for /avatar/{input}.svg endpoint."""

    def test_get_avatar_svg_success(self):
        """Avatar SVG endpoint returns 200 with correct headers."""
        response = client.get("/avatar/test@example.com.svg")

        assert response.status_code == 200
        assert "image/svg+xml" in response.headers["content-type"]
        assert "cache-control" in response.headers
        assert "public" in response.headers["cache-control"]
        assert "max-age" in response.headers["cache-control"]
        assert "etag" in response.headers

    def test_avatar_svg_contains_valid_svg(self):
        """Avatar SVG response contains valid SVG content."""
        response = client.get("/avatar/test@example.com.svg")

        assert response.status_code == 200
        assert b"<svg" in response.content
        assert b"xmlns" in response.content

    def test_avatar_svg_deterministic(self):
        """Same input returns same avatar (deterministic)."""
        response1 = client.get("/avatar/deterministic-test.svg")
        response2 = client.get("/avatar/deterministic-test.svg")

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.content == response2.content
        assert response1.headers["etag"] == response2.headers["etag"]

    def test_avatar_svg_different_inputs(self):
        """Different inputs return different avatars."""
        response1 = client.get("/avatar/user1@example.com.svg")
        response2 = client.get("/avatar/user2@example.com.svg")

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.content != response2.content
        assert response1.headers["etag"] != response2.headers["etag"]

    def test_avatar_svg_with_frame_parameter(self):
        """Avatar SVG accepts frame parameter."""
        response = client.get("/avatar/test@example.com.svg?frame=happy")

        assert response.status_code == 200
        assert "image/svg+xml" in response.headers["content-type"]

    def test_avatar_svg_idle_frames(self):
        """Avatar SVG accepts all idle frame parameters."""
        for i in range(10):
            response = client.get(f"/avatar/test@example.com.svg?frame=idle_{i}")
            assert response.status_code == 200

    def test_avatar_svg_emote_frames(self):
        """Avatar SVG accepts all emote frame parameters."""
        emotes = ["happy", "sad", "surprised", "angry", "bored"]
        for emote in emotes:
            response = client.get(f"/avatar/test@example.com.svg?frame={emote}")
            assert response.status_code == 200

    def test_avatar_svg_vowel_frames(self):
        """Avatar SVG accepts all vowel frame parameters."""
        vowels = ["A", "E", "I", "O", "U"]
        for vowel in vowels:
            response = client.get(f"/avatar/test@example.com.svg?frame=vowel_{vowel}")
            assert response.status_code == 200


class TestAvatarPNGEndpoint:
    """Tests for /avatar/{input}.png endpoint."""

    def test_get_avatar_png_success(self):
        """Avatar PNG endpoint returns 200 with correct headers."""
        response = client.get("/avatar/test@example.com.png")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert "cache-control" in response.headers
        assert "etag" in response.headers

    def test_avatar_png_contains_valid_png(self):
        """Avatar PNG response contains valid PNG content."""
        response = client.get("/avatar/test@example.com.png")

        assert response.status_code == 200
        # PNG magic number
        assert response.content[:8] == b'\x89PNG\r\n\x1a\n'

    def test_avatar_png_deterministic(self):
        """Same input returns same PNG (deterministic)."""
        response1 = client.get("/avatar/deterministic-test.png")
        response2 = client.get("/avatar/deterministic-test.png")

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.content == response2.content

    def test_avatar_png_with_frame_parameter(self):
        """Avatar PNG accepts frame parameter."""
        response = client.get("/avatar/test@example.com.png?frame=happy")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"


class TestInfoEndpoint:
    """Tests for /avatar/{input}.svg/info endpoint."""

    def test_get_avatar_info_success(self):
        """Info endpoint returns 200 with JSON."""
        response = client.get("/avatar/test@example.com.svg/info")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_avatar_info_contains_expected_fields(self):
        """Info endpoint returns expected configuration fields."""
        response = client.get("/avatar/test@example.com.svg/info")
        data = response.json()

        assert "input_string" in data
        assert "body_shape" in data
        assert "body_color" in data
        assert "node_color" in data
        assert "cache_info" in data

    def test_avatar_info_cache_info(self):
        """Info endpoint includes cache information."""
        response = client.get("/avatar/test@example.com.svg/info")
        data = response.json()

        assert "cache_info" in data
        assert "hash" in data["cache_info"]
        assert "cached" in data["cache_info"]


class TestFramesEndpoint:
    """Tests for /avatar/{input}.svg/frames endpoint."""

    def test_get_frames_success(self):
        """Frames endpoint returns 200 with JSON."""
        response = client.get("/avatar/test@example.com.svg/frames")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_frames_contains_expected_structure(self):
        """Frames endpoint returns expected structure."""
        response = client.get("/avatar/test@example.com.svg/frames")
        data = response.json()

        assert "frames" in data
        assert "idle" in data["frames"]
        assert "emotes" in data["frames"]
        assert "vowels" in data["frames"]
        assert "total_frames" in data

    def test_frames_idle_info(self):
        """Frames endpoint includes idle animation info."""
        response = client.get("/avatar/test@example.com.svg/frames")
        data = response.json()

        idle = data["frames"]["idle"]
        assert "frame_count" in idle
        assert idle["frame_count"] == 10
        assert "frames" in idle
        assert len(idle["frames"]) == 10
        assert "fps" in idle

    def test_frames_emotes_info(self):
        """Frames endpoint includes emote info."""
        response = client.get("/avatar/test@example.com.svg/frames")
        data = response.json()

        emotes = data["frames"]["emotes"]
        assert "frame_count" in emotes
        assert emotes["frame_count"] == 5
        assert "frames" in emotes


class TestBundleEndpoint:
    """Tests for /avatar/{input}/bundle endpoint."""

    def test_get_bundle_success(self):
        """Bundle endpoint returns 200 with ZIP."""
        response = client.get("/avatar/test@example.com/bundle")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
        assert "content-disposition" in response.headers
        assert "attachment" in response.headers["content-disposition"]

    def test_bundle_contains_valid_zip(self):
        """Bundle response contains valid ZIP content."""
        response = client.get("/avatar/test@example.com/bundle")

        assert response.status_code == 200
        # ZIP magic number
        assert response.content[:4] == b'PK\x03\x04'

    def test_bundle_with_animation_parameter(self):
        """Bundle endpoint accepts animations parameter."""
        response = client.get("/avatar/test@example.com/bundle?animations=idle")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"

    def test_bundle_post_endpoint(self):
        """POST bundle endpoint works."""
        response = client.post(
            "/avatar/bundle",
            json={"input": "test@example.com", "animations": ["idle"]}
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_check_success(self):
        """Health check endpoint returns 200."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


class TestStaticPages:
    """Tests for static HTML pages."""

    def test_root_page(self):
        """Root page returns 200."""
        response = client.get("/")

        assert response.status_code == 200

    def test_animations_page(self):
        """Animations page returns 200."""
        response = client.get("/animations.html")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"


class TestSecurityHeaders:
    """Tests for security headers on all endpoints."""

    def test_svg_endpoint_has_security_headers(self):
        """SVG endpoint includes security headers."""
        response = client.get("/avatar/test@example.com.svg")

        assert "x-content-type-options" in response.headers
        assert response.headers["x-content-type-options"] == "nosniff"
        assert "x-frame-options" in response.headers
        assert response.headers["x-frame-options"] == "SAMEORIGIN"
        assert "referrer-policy" in response.headers
        # Note: X-XSS-Protection removed as deprecated in PR #11

    def test_png_endpoint_has_security_headers(self):
        """PNG endpoint includes security headers."""
        response = client.get("/avatar/test@example.com.png")

        assert "x-content-type-options" in response.headers
        assert "x-frame-options" in response.headers
        assert "referrer-policy" in response.headers

    def test_api_endpoint_has_security_headers(self):
        """API endpoints include security headers."""
        response = client.get("/avatar/test@example.com.svg/info")

        assert "x-content-type-options" in response.headers
        assert "referrer-policy" in response.headers


class TestCacheHeaders:
    """Tests for cache headers."""

    def test_svg_endpoint_has_cache_headers(self):
        """SVG endpoint includes proper cache headers."""
        response = client.get("/avatar/test@example.com.svg")

        assert "cache-control" in response.headers
        cache_control = response.headers["cache-control"]
        assert "public" in cache_control
        assert "max-age=31536000" in cache_control and "immutable" in cache_control

    def test_png_endpoint_has_cache_headers(self):
        """PNG endpoint includes proper cache headers."""
        response = client.get("/avatar/test@example.com.png")

        assert "cache-control" in response.headers
        assert "etag" in response.headers


class TestErrorHandling:
    """Tests for error handling."""

    def test_404_on_missing_static_page(self):
        """Returns 404 for missing static pages."""
        response = client.get("/nonexistent-page.html")

        assert response.status_code == 404
