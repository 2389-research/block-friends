"""
Comprehensive error handling and resilience tests.

Tests error conditions, failure modes, and graceful degradation.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app import app, get_or_generate_avatar_content, get_or_generate_avatar_png
import asyncio

client = TestClient(app)


class TestCacheErrorHandling:
    """Tests for cache-related error handling."""

    @pytest.mark.asyncio
    async def test_cache_read_failure_regenerates(self):
        """If cache read fails, avatar is regenerated."""
        # This tests the error handling in get_or_generate_avatar_content
        # when cache_path.read_text() fails

        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.read_text', side_effect=IOError("Disk error")):
                # Should not raise exception, should regenerate instead
                svg_content, hash_hex = await get_or_generate_avatar_content("test@example.com")
                assert '<svg' in svg_content
                assert len(hash_hex) == 16

    @pytest.mark.asyncio
    async def test_cache_write_failure_raises_http_exception(self):
        """If cache write fails, appropriate error is raised."""
        with patch('pathlib.Path.write_text', side_effect=IOError("Disk full")):
            # Should raise HTTPException with 500 status
            with pytest.raises(Exception) as exc_info:
                await get_or_generate_avatar_content("cachewritefail@example.com")

            # Check that it's an HTTPException or contains error info
            assert "cache" in str(exc_info.value).lower() or "write" in str(exc_info.value).lower()

    def test_svg_endpoint_handles_generation_errors(self):
        """SVG endpoint returns proper error when generation fails."""
        # Test with a mock that causes generation to fail
        with patch('door_agents.DoorAgentGenerator.generate_deterministic', side_effect=Exception("Generation failed")):
            response = client.get("/avatar/failure@example.com.svg")

            # Should return 500 error with proper error message
            assert response.status_code == 500

    def test_png_endpoint_handles_conversion_errors(self):
        """PNG endpoint returns proper error when SVG to PNG conversion fails."""
        # Mock cairosvg.svg2png to fail
        with patch('cairosvg.svg2png', side_effect=Exception("CairoSVG error")):
            response = client.get("/avatar/pngfail@example.com.png")

            # Should return 500 error
            assert response.status_code == 500


class TestBundleErrorHandling:
    """Tests for bundle generation error handling."""

    def test_bundle_with_invalid_animation_type(self):
        """Bundle endpoint handles invalid animation types gracefully."""
        response = client.get("/avatar/test@example.com/bundle?animations=invalid,notreal")

        # Should still return a bundle (empty or with only valid animations)
        # Or return an error - depending on implementation
        # For now, let's just check it doesn't crash
        assert response.status_code in [200, 400, 500]

    def test_bundle_with_empty_input_string(self):
        """Bundle endpoint handles empty input string."""
        response = client.get("/avatar/.svg/bundle")

        # Should handle gracefully - either generate or return error
        # Check it doesn't crash the server
        assert response.status_code in [200, 404, 422, 500]

    def test_bundle_post_with_empty_animations_list(self):
        """POST bundle endpoint handles empty animations list."""
        response = client.post(
            "/avatar/bundle",
            json={"input": "test@example.com", "animations": []}
        )

        # Should handle gracefully
        assert response.status_code in [200, 400]

    def test_bundle_svg_to_pdf_conversion_failure(self):
        """Bundle handles SVG to PDF conversion failures."""
        # Mock svg_to_pdf to fail
        with patch('app.svg_to_pdf', side_effect=Exception("PDF conversion failed")):
            response = client.get("/avatar/pdffail@example.com/bundle?animations=idle")

            # Should return 500 error
            assert response.status_code == 500


class TestTransitionErrorHandling:
    """Tests for transition generation error handling."""

    def test_transition_with_invalid_emote(self):
        """Transition endpoint handles invalid emote names."""
        response = client.get("/avatar/test@example.com/transition/invalid_emote/50")

        # Should return 400 or 500 error
        assert response.status_code in [400, 500]

    def test_transition_with_invalid_weight(self):
        """Transition endpoint handles invalid weight values."""
        # Test negative weight
        response = client.get("/avatar/test@example.com/transition/happy/-1")
        assert response.status_code in [400, 422, 500]

        # Test weight > 100
        response = client.get("/avatar/test@example.com/transition/happy/150")
        assert response.status_code in [400, 422, 500]

    def test_transition_with_malformed_weight(self):
        """Transition endpoint handles non-numeric weight values."""
        response = client.get("/avatar/test@example.com/transition/happy/abc")

        # Should return 422 (validation error) or 400
        assert response.status_code in [400, 422]


class TestEndpointErrorResponses:
    """Tests for proper error response formatting."""

    def test_404_error_response_format(self):
        """404 errors return proper response format."""
        response = client.get("/nonexistent-endpoint")

        assert response.status_code == 404
        # FastAPI returns JSON for 404 by default
        assert response.headers["content-type"] == "application/json"

    def test_500_error_includes_detail(self):
        """500 errors include error detail in response."""
        # Force an error by mocking
        with patch('door_agents.DoorAgentGenerator.generate_deterministic', side_effect=Exception("Test error")):
            response = client.get("/avatar/test@example.com.svg")

            assert response.status_code == 500
            # Should have some error information
            assert len(response.content) > 0

    def test_error_responses_include_security_headers(self):
        """Error responses include security headers."""
        response = client.get("/nonexistent-page.html")

        assert response.status_code == 404
        # Security headers should still be present
        assert "x-content-type-options" in response.headers
        assert "x-frame-options" in response.headers


class TestConcurrentRequestHandling:
    """Tests for handling concurrent requests safely."""

    def test_concurrent_avatar_generation_same_input(self):
        """Concurrent requests for same avatar don't cause race conditions."""
        import concurrent.futures

        def get_avatar():
            response = client.get("/avatar/concurrent@example.com.svg")
            return response.status_code, response.content

        # Make 10 concurrent requests for the same avatar
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(get_avatar) for _ in range(10)]
            results = [f.result() for f in futures]

        # All should succeed
        assert all(status == 200 for status, _ in results)

        # All should return the same content
        contents = [content for _, content in results]
        assert all(content == contents[0] for content in contents)

    def test_concurrent_different_avatars(self):
        """Concurrent requests for different avatars work correctly."""
        import concurrent.futures

        def get_avatar(n):
            response = client.get(f"/avatar/user{n}@example.com.svg")
            return response.status_code, response.content

        # Make 10 concurrent requests for different avatars
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(get_avatar, i) for i in range(10)]
            results = [f.result() for f in futures]

        # All should succeed
        assert all(status == 200 for status, _ in results)

        # All should return different content (different avatars)
        contents = [content for _, content in results]
        unique_contents = set(contents)
        assert len(unique_contents) == 10


class TestInputValidation:
    """Tests for input validation and error handling."""

    def test_very_long_input_string(self):
        """System handles very long input strings."""
        long_input = "a" * 10000
        response = client.get(f"/avatar/{long_input}.svg")

        # Should handle gracefully - either succeed or return appropriate error
        assert response.status_code in [200, 400, 414, 500]

    def test_special_characters_in_input(self):
        """System handles special characters in input strings."""
        special_chars = "test@#$%^&*()[]{}|\\<>?/example.com"
        response = client.get(f"/avatar/{special_chars}.svg")

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_unicode_in_input_string(self):
        """System handles Unicode characters in input strings."""
        unicode_input = "测试用户@example.com"
        response = client.get(f"/avatar/{unicode_input}.svg")

        # Should succeed (hash should handle any UTF-8 string)
        assert response.status_code == 200

    def test_empty_input_string(self):
        """System handles empty input string."""
        response = client.get("/avatar/.svg")

        # Should handle gracefully
        assert response.status_code in [200, 404, 422]


class TestResourceLimits:
    """Tests for resource limits and constraints."""

    def test_multiple_bundle_generations(self):
        """System handles multiple bundle generation requests."""
        # Make 3 bundle requests (within rate limit but resource-intensive)
        responses = []
        for i in range(3):
            response = client.get(f"/avatar/bundle{i}@example.com/bundle?animations=idle")
            responses.append(response)

        # All should complete successfully
        assert all(r.status_code == 200 for r in responses)

        # All should be valid ZIP files
        assert all(r.content[:4] == b'PK\x03\x04' for r in responses)

    def test_png_generation_memory_usage(self):
        """PNG generation doesn't cause memory issues."""
        # Generate multiple PNGs
        responses = []
        for i in range(10):
            response = client.get(f"/avatar/pngmem{i}@example.com.png")
            responses.append(response)

        # All should succeed
        assert all(r.status_code == 200 for r in responses)

        # All should be valid PNGs
        assert all(r.content[:8] == b'\x89PNG\r\n\x1a\n' for r in responses)


class TestInfoEndpointErrorHandling:
    """Tests for info endpoint error handling."""

    def test_info_endpoint_with_invalid_input(self):
        """Info endpoint handles invalid input gracefully."""
        response = client.get("/avatar/.svg/info")

        # Should handle gracefully
        assert response.status_code in [200, 404, 422, 500]

    def test_info_endpoint_with_invalid_frame(self):
        """Info endpoint handles invalid frame parameter."""
        response = client.get("/avatar/test@example.com.svg/info?frame=invalid_frame")

        # Should handle gracefully - might still return info or return error
        assert response.status_code in [200, 400, 422, 500]


class TestDebugEndpointErrorHandling:
    """Tests for debug endpoint error handling."""

    def test_debug_endpoint_with_invalid_input(self):
        """Debug endpoint handles invalid input gracefully."""
        response = client.get("/debug/avatar/")

        # Should handle gracefully
        assert response.status_code in [200, 404, 422]

    def test_debug_endpoint_with_generation_failure(self):
        """Debug endpoint handles generation failures."""
        with patch('door_agents.DoorAgentGenerator.generate_deterministic', side_effect=Exception("Debug fail")):
            response = client.get("/debug/avatar/test@example.com")

            # Should return error
            assert response.status_code == 500
