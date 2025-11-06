#!/usr/bin/env python3
# ABOUTME: Tests for security headers and CORS middleware
# ABOUTME: Validates that all HTTP responses include proper security headers

import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_cors_headers_present():
    """Test that CORS headers are present in responses when Origin header is provided."""
    response = client.get(
        "/avatar/test@example.com.svg",
        headers={"Origin": "https://example.com"}
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "*"


def test_security_header_x_content_type_options():
    """Test that X-Content-Type-Options header is present."""
    response = client.get("/avatar/test@example.com.svg")

    assert response.status_code == 200
    assert "x-content-type-options" in response.headers
    assert response.headers["x-content-type-options"] == "nosniff"


def test_security_header_x_frame_options():
    """Test that X-Frame-Options header is present."""
    response = client.get("/avatar/test@example.com.svg")

    assert response.status_code == 200
    assert "x-frame-options" in response.headers
    assert response.headers["x-frame-options"] == "SAMEORIGIN"


def test_security_header_x_xss_protection():
    """Test that X-XSS-Protection header is present."""
    response = client.get("/avatar/test@example.com.svg")

    assert response.status_code == 200
    assert "x-xss-protection" in response.headers
    assert response.headers["x-xss-protection"] == "1; mode=block"


def test_security_header_referrer_policy():
    """Test that Referrer-Policy header is present."""
    response = client.get("/avatar/test@example.com.svg")

    assert response.status_code == 200
    assert "referrer-policy" in response.headers
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"


def test_security_headers_on_all_endpoints():
    """Test that security headers are present on various endpoints."""
    endpoints = [
        "/avatar/test@example.com.svg",
        "/avatar/test@example.com.png",
        "/",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)

        # All responses should have security headers
        assert "x-content-type-options" in response.headers, f"Missing header on {endpoint}"
        assert "x-frame-options" in response.headers, f"Missing header on {endpoint}"
        assert "x-xss-protection" in response.headers, f"Missing header on {endpoint}"
        assert "referrer-policy" in response.headers, f"Missing header on {endpoint}"


def test_cors_headers_on_all_endpoints():
    """Test that CORS headers are present on various endpoints when Origin is provided."""
    endpoints = [
        "/avatar/test@example.com.svg",
        "/avatar/test@example.com.png",
        "/",
    ]

    for endpoint in endpoints:
        response = client.get(
            endpoint,
            headers={"Origin": "https://example.com"}
        )

        # All responses should have CORS headers when Origin is present
        assert "access-control-allow-origin" in response.headers, f"Missing CORS header on {endpoint}"


def test_cors_allows_all_origins():
    """Test that CORS allows requests from any origin."""
    response = client.get(
        "/avatar/test@example.com.svg",
        headers={"Origin": "https://example.com"}
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"


def test_security_headers_on_error_responses():
    """Test that security headers are present even on error responses."""
    response = client.get("/avatar/test@example.com/transition/invalid_emote/50")

    # Should be an error response
    assert response.status_code == 400

    # But still should have security headers
    assert "x-content-type-options" in response.headers
    assert "x-frame-options" in response.headers
    assert "x-xss-protection" in response.headers
    assert "referrer-policy" in response.headers


def test_no_csp_header():
    """Test that Content-Security-Policy is NOT present (by design for public SVG API)."""
    response = client.get("/avatar/test@example.com.svg")

    assert response.status_code == 200
    # CSP should NOT be present since we serve embeddable SVGs
    assert "content-security-policy" not in response.headers
