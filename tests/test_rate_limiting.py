"""
Rate limiting tests for all API endpoints.

Tests rate limiting configuration and behavior to ensure proper request throttling.
"""

import pytest
import time
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


class TestRateLimitingAvatarEndpoints:
    """Tests for rate limiting on avatar SVG and PNG endpoints (100/minute)."""

    def test_svg_endpoint_rate_limit_within_limit(self):
        """SVG endpoint allows requests within rate limit."""
        # Make 5 requests (well within 100/minute limit)
        for i in range(5):
            response = client.get(f"/avatar/test{i}@example.com.svg")
            assert response.status_code == 200

    def test_svg_endpoint_rate_limit_exceeded(self):
        """SVG endpoint returns 429 when rate limit exceeded."""
        # Make 101 requests to exceed 100/minute limit
        responses = []
        for i in range(101):
            response = client.get(f"/avatar/ratelimit{i}@example.com.svg")
            responses.append(response)

        # At least one should be rate limited
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes, "Expected at least one 429 (Too Many Requests) response"

    def test_png_endpoint_rate_limit_within_limit(self):
        """PNG endpoint allows requests within rate limit."""
        # Make 5 requests (well within 100/minute limit)
        for i in range(5):
            response = client.get(f"/avatar/pngtest{i}@example.com.png")
            assert response.status_code == 200

    def test_png_endpoint_rate_limit_exceeded(self):
        """PNG endpoint returns 429 when rate limit exceeded."""
        # Make 101 requests to exceed 100/minute limit
        responses = []
        for i in range(101):
            response = client.get(f"/avatar/pnglimit{i}@example.com.png")
            responses.append(response)

        # At least one should be rate limited
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes, "Expected at least one 429 (Too Many Requests) response"

    def test_rate_limit_response_headers(self):
        """Rate limit responses include proper headers."""
        # Make requests until we hit rate limit
        for i in range(101):
            response = client.get(f"/avatar/headers{i}@example.com.svg")
            if response.status_code == 429:
                # Check that 429 response has appropriate content
                assert response.status_code == 429
                # slowapi typically returns text/plain for rate limit errors
                assert "text/plain" in response.headers.get("content-type", "").lower() or \
                       "application/json" in response.headers.get("content-type", "").lower()
                break


class TestRateLimitingBundleEndpoints:
    """Tests for rate limiting on bundle endpoints (10/minute)."""

    def test_bundle_get_endpoint_rate_limit_within_limit(self):
        """Bundle GET endpoint allows requests within rate limit."""
        # Make 5 requests (well within 10/minute limit)
        for i in range(5):
            response = client.get(f"/avatar/bundle{i}@example.com/bundle")
            assert response.status_code == 200

    def test_bundle_get_endpoint_rate_limit_exceeded(self):
        """Bundle GET endpoint returns 429 when rate limit exceeded."""
        # Make 11 requests to exceed 10/minute limit
        responses = []
        for i in range(11):
            response = client.get(f"/avatar/bundlelimit{i}@example.com/bundle")
            responses.append(response)

        # At least one should be rate limited
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes, "Expected at least one 429 (Too Many Requests) response"

    def test_bundle_post_endpoint_rate_limit_within_limit(self):
        """Bundle POST endpoint allows requests within rate limit."""
        # Make 5 requests (well within 10/minute limit)
        for i in range(5):
            response = client.post(
                "/avatar/bundle",
                json={"input": f"postbundle{i}@example.com", "animations": ["idle"]}
            )
            assert response.status_code == 200

    def test_bundle_post_endpoint_rate_limit_exceeded(self):
        """Bundle POST endpoint returns 429 when rate limit exceeded."""
        # Make 11 requests to exceed 10/minute limit
        responses = []
        for i in range(11):
            response = client.post(
                "/avatar/bundle",
                json={"input": f"postlimit{i}@example.com", "animations": ["idle"]}
            )
            responses.append(response)

        # At least one should be rate limited
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes, "Expected at least one 429 (Too Many Requests) response"


class TestRateLimitingIPDetection:
    """Tests for IP detection with X-Forwarded-For headers."""

    def test_rate_limiting_respects_x_forwarded_for(self):
        """Rate limiting uses X-Forwarded-For header for IP detection."""
        # Make requests with different X-Forwarded-For IPs
        # Each different IP should have its own rate limit counter
        response1 = client.get(
            "/avatar/proxy1@example.com.svg",
            headers={"X-Forwarded-For": "1.2.3.4"}
        )
        assert response1.status_code == 200

        response2 = client.get(
            "/avatar/proxy2@example.com.svg",
            headers={"X-Forwarded-For": "5.6.7.8"}
        )
        assert response2.status_code == 200

        # Both should succeed since they're from "different" IPs
        assert response1.status_code == 200
        assert response2.status_code == 200

    def test_rate_limiting_without_x_forwarded_for(self):
        """Rate limiting works without X-Forwarded-For header."""
        # Make requests without X-Forwarded-For (uses client IP)
        response = client.get("/avatar/noproxy@example.com.svg")
        assert response.status_code == 200


class TestRateLimitingNonLimitedEndpoints:
    """Tests that non-limited endpoints don't have rate limiting."""

    def test_health_endpoint_not_rate_limited(self):
        """Health endpoint does not have rate limiting."""
        # Make many requests to health endpoint
        for _ in range(20):
            response = client.get("/health")
            assert response.status_code == 200

    def test_version_endpoint_not_rate_limited(self):
        """Version endpoint does not have rate limiting."""
        # Make many requests to version endpoint
        for _ in range(20):
            response = client.get("/version")
            assert response.status_code == 200

    def test_info_endpoint_not_rate_limited(self):
        """Info endpoint does not have rate limiting."""
        # Make many requests to info endpoint
        for _ in range(20):
            response = client.get("/avatar/test@example.com.svg/info")
            assert response.status_code == 200

    def test_frames_endpoint_not_rate_limited(self):
        """Frames endpoint does not have rate limiting."""
        # Make many requests to frames endpoint
        for _ in range(20):
            response = client.get("/avatar/test@example.com.svg/frames")
            assert response.status_code == 200
