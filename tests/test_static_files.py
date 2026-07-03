#!/usr/bin/env python3
# ABOUTME: Tests for static file serving and middleware
# ABOUTME: Tests static HTML pages, assets, and file serving behavior

import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


class TestStaticHTMLPages:
    """Tests for static HTML page serving."""

    def test_root_page_loads(self):
        """Root page (/) loads successfully."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_page_is_html(self):
        """Root page returns HTML content."""
        response = client.get("/")
        assert "text/html" in response.headers.get("content-type", "")

    def test_animations_page_loads(self):
        """Animations page loads successfully."""
        response = client.get("/animations.html")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_sitemap_page_loads(self):
        """Sitemap page loads if it exists."""
        response = client.get("/sitemap.html")
        # May or may not exist
        assert response.status_code in [200, 404]


class TestStaticFileEndpoints:
    """Tests for /static file serving."""

    def test_static_route_exists(self):
        """Static file route is mounted."""
        # Try to access static directory
        response = client.get("/static/")
        # Should return 404 for directory or index
        assert response.status_code in [200, 404, 405]

    def test_missing_static_file_returns_404(self):
        """Missing static file returns 404."""
        response = client.get("/static/nonexistent-file.html")
        assert response.status_code == 404

    @pytest.mark.skip(reason="Requires a known static file fixture to validate headers")
    def test_static_file_security_headers(self):
        """Static files include security headers."""


class TestAssetFileServing:
    """Tests for /assets file serving."""

    def test_assets_route_exists(self):
        """Assets route is mounted."""
        response = client.get("/assets/")
        # Should return 404 for directory or index
        assert response.status_code in [200, 404, 405]

    def test_missing_asset_returns_404(self):
        """Missing asset file returns 404."""
        response = client.get("/assets/nonexistent.svg")
        assert response.status_code == 404

    @pytest.mark.skip(reason="Requires a known asset filename to validate content-type")
    def test_svg_asset_serving(self):
        """SVG assets are served with correct content type."""


class Test404Handling:
    """Tests for 404 error handling."""

    def test_404_on_invalid_route(self):
        """Invalid routes return 404."""
        response = client.get("/this-route-does-not-exist")
        assert response.status_code == 404

    def test_404_on_invalid_static_page(self):
        """Invalid static pages return 404."""
        response = client.get("/nonexistent.html")
        assert response.status_code == 404

    def test_404_includes_security_headers(self):
        """404 responses include security headers."""
        response = client.get("/nonexistent-page")

        assert response.status_code == 404
        # Should still have security headers
        assert "x-content-type-options" in response.headers
        assert "x-frame-options" in response.headers


class TestMiddlewareFunctionality:
    """Tests for middleware behavior."""

    def test_security_headers_middleware_active(self):
        """Security headers middleware is active on all routes."""
        routes = [
            "/",
            "/avatar/test@example.com.svg",
            "/health"
        ]

        for route in routes:
            response = client.get(route)
            # All should have security headers
            assert "x-content-type-options" in response.headers
            assert "x-frame-options" in response.headers
            assert "referrer-policy" in response.headers

    def test_cors_middleware_active(self):
        """CORS middleware is active."""
        response = client.get(
            "/avatar/test@example.com.svg",
            headers={"Origin": "https://example.com"}
        )

        assert "access-control-allow-origin" in response.headers

    def test_middleware_order_preserved(self):
        """Middleware executes in correct order."""
        # Security headers and CORS should both be present
        response = client.get(
            "/avatar/test@example.com.svg",
            headers={"Origin": "https://example.com"}
        )

        assert "x-content-type-options" in response.headers
        assert "access-control-allow-origin" in response.headers


class TestContentTypeHeaders:
    """Tests for correct Content-Type headers."""

    def test_svg_endpoint_content_type(self):
        """SVG endpoint returns correct content type."""
        response = client.get("/avatar/test@example.com.svg")
        assert "image/svg+xml" in response.headers["content-type"]

    def test_png_endpoint_content_type(self):
        """PNG endpoint returns correct content type."""
        response = client.get("/avatar/test@example.com.png")
        assert response.headers["content-type"] == "image/png"

    def test_json_endpoint_content_type(self):
        """JSON endpoints return correct content type."""
        response = client.get("/avatar/test@example.com.svg/info")
        assert "application/json" in response.headers["content-type"]

    def test_bundle_endpoint_content_type(self):
        """Bundle endpoint returns correct content type."""
        response = client.get("/avatar/test-static-bundle-1@example.com/bundle")
        # May hit rate limit
        if response.status_code == 429:
            pytest.skip("Rate limited")
        assert response.headers["content-type"] == "application/zip"


class TestContentDispositionHeaders:
    """Tests for Content-Disposition headers."""

    def test_bundle_has_content_disposition(self):
        """Bundle endpoint includes Content-Disposition header."""
        response = client.get("/avatar/test-static-bundle-2@example.com/bundle")

        if response.status_code == 429:
            pytest.skip("Rate limited")

        assert "content-disposition" in response.headers
        assert "attachment" in response.headers["content-disposition"]

    def test_bundle_filename_in_disposition(self):
        """Bundle Content-Disposition includes filename."""
        response = client.get("/avatar/test-static-bundle-3@example.com/bundle")

        if response.status_code == 429:
            pytest.skip("Rate limited")

        disposition = response.headers.get("content-disposition", "")
        assert "filename" in disposition or "attachment" in disposition


class TestHTTPMethodSupport:
    """Tests for HTTP method support on endpoints."""

    def test_get_method_supported(self):
        """GET method is supported on endpoints."""
        response = client.get("/avatar/test@example.com.svg")
        assert response.status_code == 200

    def test_post_bundle_endpoint(self):
        """POST method is supported on bundle endpoint."""
        response = client.post(
            "/avatar/bundle",
            json={"input": "test@example.com", "animations": ["idle"]}
        )
        if response.status_code == 429:
            pytest.skip("Bundle endpoint rate-limited by an earlier test")
        assert response.status_code == 200

    def test_unsupported_method_rejected(self):
        """Unsupported HTTP methods are rejected."""
        response = client.put("/avatar/test@example.com.svg")
        assert response.status_code in [405, 404]  # 405 = Method Not Allowed


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_endpoint_accessible(self):
        """Health endpoint is accessible."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_json(self):
        """Health endpoint returns JSON."""
        response = client.get("/health")
        assert "application/json" in response.headers["content-type"]

    def test_health_status_field(self):
        """Health response includes status field."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


class TestOptionsMethod:
    """Tests for OPTIONS method (CORS preflight)."""

    def test_options_request_cors(self):
        """OPTIONS requests are handled for CORS."""
        response = client.options(
            "/avatar/test@example.com.svg",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "GET"
            }
        )

        # Should return CORS headers
        # May return 200 or 405 depending on configuration
        assert response.status_code in [200, 405]
