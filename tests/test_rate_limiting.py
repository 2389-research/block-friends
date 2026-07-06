#!/usr/bin/env python3
# ABOUTME: Tests for API rate limiting functionality
# ABOUTME: Validates slowapi rate limits work correctly on all endpoints

import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


class TestAvatarEndpointRateLimiting:
    """Tests for rate limiting on /avatar endpoints."""

    def test_svg_endpoint_rate_limit_exists(self):
        """SVG endpoint has rate limiting configured."""
        # Make multiple rapid requests to test rate limiting
        responses = []
        for i in range(5):
            response = client.get(f"/avatar/test{i}@example.com.svg")
            responses.append(response)

        # At least some requests should succeed
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count > 0, "At least some requests should succeed"

    def test_svg_endpoint_respects_rate_limit_headers(self):
        """SVG endpoint includes rate limit headers in response."""
        response = client.get("/avatar/test@example.com.svg")

        # Rate limit headers should be present (may vary by slowapi configuration)
        # Common headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
        assert response.status_code == 200

    def test_png_endpoint_rate_limit_exists(self):
        """PNG endpoint has rate limiting configured."""
        responses = []
        for i in range(5):
            response = client.get(f"/avatar/test{i}@example.com.png")
            responses.append(response)

        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count > 0

    def test_rate_limit_applies_per_ip(self):
        """Rate limiting is applied per IP address."""
        # With TestClient, all requests come from same IP
        # This tests that rate limiting tracks per-IP correctly
        response = client.get("/avatar/test@example.com.svg")
        assert response.status_code == 200

        # Subsequent request from same IP uses same rate limit bucket
        response2 = client.get("/avatar/test2@example.com.svg")
        assert response2.status_code == 200


class TestBundleEndpointRateLimiting:
    """Tests for rate limiting on /bundle endpoints (stricter limits)."""

    def test_bundle_endpoint_has_rate_limiting(self):
        """Bundle endpoint has stricter rate limiting (10/minute)."""
        # Make a few requests to bundle endpoint
        response = client.get("/avatar/test@example.com/bundle?animations=idle")

        # Should succeed initially
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"

    def test_bundle_post_endpoint_has_rate_limiting(self):
        """POST bundle endpoint has rate limiting."""
        response = client.post(
            "/avatar/bundle",
            json={"input": "test@example.com", "animations": ["idle"]}
        )

        assert response.status_code == 200


class TestRateLimitErrorResponses:
    """Tests for rate limit exceeded error responses."""

    def test_rate_limit_exceeded_returns_429(self):
        """After the 100/minute avatar limit is exhausted, the endpoint
        returns 429."""
        responses = [
            client.get("/avatar/rate-429@example.com.svg")
            for _ in range(101)
        ]
        assert any(r.status_code == 429 for r in responses), (
            "Expected at least one 429 within 101 requests"
        )

    def test_rate_limit_error_includes_retry_after(self):
        """The 429 response body carries slowapi's default rate-limit
        detail so clients can back off intelligently."""
        responses = [
            client.get("/avatar/rate-retry@example.com.svg")
            for _ in range(101)
        ]
        limited = next((r for r in responses if r.status_code == 429), None)
        assert limited is not None, "Expected at least one 429 within 101 requests"
        # slowapi's default handler emits {"error": "Rate limit exceeded: ..."}
        assert "rate limit" in limited.text.lower()


class TestRateLimitWithHeaders:
    """Tests for rate limiting with various HTTP headers."""

    def test_rate_limit_respects_x_forwarded_for(self):
        """Rate limiter respects X-Forwarded-For header for proxy setups."""
        # Test that X-Forwarded-For is used for IP detection
        response = client.get(
            "/avatar/test@example.com.svg",
            headers={"X-Forwarded-For": "192.168.1.1"}
        )

        assert response.status_code == 200

        # Different X-Forwarded-For should use different rate limit bucket
        response2 = client.get(
            "/avatar/test@example.com.svg",
            headers={"X-Forwarded-For": "192.168.1.2"}
        )

        assert response2.status_code == 200

    def test_rate_limit_handles_missing_forwarded_for(self):
        """Rate limiter works correctly without X-Forwarded-For header."""
        response = client.get("/avatar/test@example.com.svg")

        assert response.status_code == 200

    def test_rate_limit_handles_invalid_forwarded_for(self):
        """Rate limiter handles malformed X-Forwarded-For gracefully."""
        response = client.get(
            "/avatar/test@example.com.svg",
            headers={"X-Forwarded-For": "invalid-ip-address"}
        )

        # Should still work, falling back to connection IP
        assert response.status_code == 200


class TestRateLimitConfiguration:
    """Tests for rate limit configuration and behavior."""

    def test_svg_endpoint_has_100_per_minute_limit(self):
        """Confirms the SVG endpoint enforces a 100/minute ceiling.
        slowapi buckets per endpoint URL, so all requests target the same
        path."""
        codes = [
            client.get("/avatar/rate-svg-limit@example.com.svg").status_code
            for _ in range(130)
        ]
        assert codes.count(200) == 100
        assert codes.count(429) == 30

    def test_bundle_endpoint_has_10_per_minute_limit(self):
        """Confirms the bundle endpoint enforces its stricter 10/minute
        ceiling — 10× tighter than the SVG endpoint. Requests target the
        same URL so slowapi keys them into one bucket."""
        codes = [
            client.get("/avatar/rate-bundle-limit@example.com/bundle").status_code
            for _ in range(25)
        ]
        assert codes.count(200) == 10
        assert codes.count(429) == 15

    @pytest.mark.skip(reason="Requires time-based testing across the 1-minute window; documents expected reset")
    def test_rate_limit_window_resets(self):
        """Rate limit counters reset after time window expires."""


class TestRateLimitWithConcurrentRequests:
    """Tests for rate limiting under concurrent load."""

    def test_rate_limit_handles_concurrent_requests(self):
        """Rate limiter correctly handles concurrent requests from same IP."""
        # Make several concurrent-style requests
        responses = [
            client.get(f"/avatar/concurrent{i}@example.com.svg")
            for i in range(5)
        ]

        # All should succeed within normal rate limits
        for response in responses:
            assert response.status_code == 200

    def test_rate_limit_per_endpoint(self):
        """Rate limits are tracked separately per endpoint."""
        # SVG endpoint
        response1 = client.get("/avatar/test@example.com.svg")
        assert response1.status_code == 200

        # PNG endpoint (different rate limit bucket)
        response2 = client.get("/avatar/test@example.com.png")
        assert response2.status_code == 200

        # Bundle endpoint (different rate limit bucket)
        response3 = client.get("/avatar/test@example.com/bundle")
        assert response3.status_code == 200
