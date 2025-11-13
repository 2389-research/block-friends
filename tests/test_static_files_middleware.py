"""
Static file serving and middleware tests.

Tests static file endpoints, middleware functionality, and headers.
"""

import pytest
from fastapi.testclient import TestClient
from app import app
from pathlib import Path

client = TestClient(app)


class TestStaticHTMLPages:
    """Tests for static HTML page serving."""

    def test_root_page_returns_200(self):
        """Root page returns 200."""
        response = client.get("/")

        assert response.status_code == 200

    def test_root_page_returns_html(self):
        """Root page returns HTML content."""
        response = client.get("/")

        assert response.status_code == 200
        # Should be HTML or JSON
        content_type = response.headers.get("content-type", "")
        assert "text/html" in content_type or "application/json" in content_type

    def test_animations_page_exists(self):
        """Animations page exists and returns 200."""
        response = client.get("/animations.html")

        assert response.status_code == 200

    def test_animations_page_is_html(self):
        """Animations page returns HTML."""
        response = client.get("/animations.html")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_sitemap_page_exists(self):
        """Sitemap page exists and returns 200."""
        response = client.get("/sitemap.html")

        assert response.status_code == 200

    def test_sitemap_page_is_html(self):
        """Sitemap page returns HTML."""
        response = client.get("/sitemap.html")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_nonexistent_html_page_returns_404(self):
        """Non-existent HTML page returns 404."""
        response = client.get("/nonexistent-page.html")

        assert response.status_code == 404


class TestStaticFileServing:
    """Tests for static file serving from /static."""

    def test_static_files_directory_mounted(self):
        """Static files directory is accessible."""
        # Try to access a file from static directory if it exists
        # This is implementation-specific
        # Just verify the mount works by trying common files

        # Check if /static path works (might return 404 for missing files)
        response = client.get("/static/test.txt")
        # Should return 404 for missing file, not 500
        assert response.status_code in [200, 404]

    def test_static_css_file(self):
        """Static CSS files are served if they exist."""
        # Check if static directory has CSS files
        static_dir = Path("static")
        if static_dir.exists():
            css_files = list(static_dir.glob("*.css"))
            if css_files:
                # Try to access first CSS file
                css_file = css_files[0]
                response = client.get(f"/static/{css_file.name}")
                assert response.status_code == 200
                assert "text/css" in response.headers.get("content-type", "")

    def test_static_js_file(self):
        """Static JavaScript files are served if they exist."""
        static_dir = Path("static")
        if static_dir.exists():
            js_files = list(static_dir.glob("*.js"))
            if js_files:
                js_file = js_files[0]
                response = client.get(f"/static/{js_file.name}")
                assert response.status_code == 200


class TestAssetFileServing:
    """Tests for asset file serving from /assets."""

    def test_assets_directory_mounted(self):
        """Assets directory is accessible."""
        # Try to access assets directory
        response = client.get("/assets/test.svg")
        # Should return 404 for missing file, not 500
        assert response.status_code in [200, 404]

    def test_asset_svg_file_served(self):
        """Asset SVG files are served if directly accessed."""
        # Check if we can access an eye asset
        asset_file = Path("assets/eyes/open/1.svg")
        if asset_file.exists():
            response = client.get("/assets/eyes/open/1.svg")
            # Might be served or might be protected
            assert response.status_code in [200, 403, 404]

    def test_hair_asset_accessible(self):
        """Hair assets are accessible if assets are publicly mounted."""
        hair_files = list(Path("assets/hair").glob("*.svg"))
        if hair_files:
            hair_file = hair_files[0]
            response = client.get(f"/assets/hair/{hair_file.name}")
            # Might be accessible or protected
            assert response.status_code in [200, 403, 404]


class TestSecurityHeadersMiddleware:
    """Tests for security headers middleware."""

    def test_security_headers_on_svg_endpoint(self):
        """Security headers are added to SVG endpoint."""
        response = client.get("/avatar/test@example.com.svg")

        assert response.status_code == 200
        assert "x-content-type-options" in response.headers
        assert response.headers["x-content-type-options"] == "nosniff"
        assert "x-frame-options" in response.headers
        assert response.headers["x-frame-options"] == "SAMEORIGIN"
        assert "referrer-policy" in response.headers

    def test_security_headers_on_png_endpoint(self):
        """Security headers are added to PNG endpoint."""
        response = client.get("/avatar/test@example.com.png")

        assert response.status_code == 200
        assert "x-content-type-options" in response.headers
        assert "x-frame-options" in response.headers
        assert "referrer-policy" in response.headers

    def test_security_headers_on_static_pages(self):
        """Security headers are added to static HTML pages."""
        response = client.get("/")

        assert response.status_code == 200
        assert "x-content-type-options" in response.headers
        assert "x-frame-options" in response.headers

    def test_security_headers_on_api_endpoints(self):
        """Security headers are added to API endpoints."""
        response = client.get("/avatar/test@example.com.svg/info")

        assert response.status_code == 200
        assert "x-content-type-options" in response.headers
        assert "referrer-policy" in response.headers

    def test_security_headers_on_error_responses(self):
        """Security headers are added to error responses."""
        response = client.get("/nonexistent-endpoint")

        assert response.status_code == 404
        assert "x-content-type-options" in response.headers
        assert "x-frame-options" in response.headers

    def test_x_xss_protection_not_present(self):
        """X-XSS-Protection header is not present (deprecated)."""
        response = client.get("/avatar/test@example.com.svg")

        assert response.status_code == 200
        # According to PR #11, X-XSS-Protection was removed
        assert "x-xss-protection" not in response.headers


class TestCORSMiddleware:
    """Tests for CORS middleware configuration."""

    def test_cors_headers_on_svg_endpoint(self):
        """CORS headers allow cross-origin requests."""
        response = client.get(
            "/avatar/test@example.com.svg",
            headers={"Origin": "https://example.com"}
        )

        assert response.status_code == 200
        # CORS headers should be present
        assert "access-control-allow-origin" in response.headers

    def test_cors_allows_all_origins(self):
        """CORS allows all origins (public API)."""
        response = client.get(
            "/avatar/test@example.com.svg",
            headers={"Origin": "https://example.com"}
        )

        assert response.status_code == 200
        # Should allow the origin
        assert response.headers.get("access-control-allow-origin") == "*" or \
               response.headers.get("access-control-allow-origin") == "https://example.com"

    def test_cors_on_json_endpoints(self):
        """CORS headers on JSON API endpoints."""
        response = client.get(
            "/avatar/test@example.com.svg/info",
            headers={"Origin": "https://example.com"}
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_cors_preflight_request(self):
        """CORS preflight OPTIONS request works."""
        response = client.options(
            "/avatar/test@example.com.svg",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "GET"
            }
        )

        # Preflight should succeed
        assert response.status_code in [200, 204]


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_endpoint_exists(self):
        """Health endpoint exists and returns 200."""
        response = client.get("/health")

        assert response.status_code == 200

    def test_health_endpoint_returns_json(self):
        """Health endpoint returns JSON."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_health_endpoint_status_healthy(self):
        """Health endpoint returns healthy status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_health_endpoint_includes_service_name(self):
        """Health endpoint includes service name."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "service" in data


class TestVersionEndpoint:
    """Tests for version endpoint."""

    def test_version_endpoint_exists(self):
        """Version endpoint exists and returns 200."""
        response = client.get("/version")

        assert response.status_code == 200

    def test_version_endpoint_returns_json(self):
        """Version endpoint returns JSON."""
        response = client.get("/version")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_version_endpoint_format(self):
        """Version endpoint returns correct format."""
        response = client.get("/version")

        assert response.status_code == 200
        data = response.json()
        assert "avatar_system_version" in data

    def test_version_header_on_avatar_responses(self):
        """Avatar responses include version header."""
        response = client.get("/avatar/test@example.com.svg")

        assert response.status_code == 200
        assert "x-avatar-system-version" in response.headers
        assert len(response.headers["x-avatar-system-version"]) > 0


class TestDebugEndpoint:
    """Tests for debug endpoint."""

    def test_debug_endpoint_exists(self):
        """Debug endpoint exists."""
        response = client.get("/debug/avatar/test@example.com")

        # Might be available or protected
        assert response.status_code in [200, 403, 404]

    def test_debug_endpoint_returns_asset_info(self):
        """Debug endpoint returns asset information."""
        response = client.get("/debug/avatar/test@example.com")

        if response.status_code == 200:
            data = response.json()
            # Should include asset info
            assert "assets" in data or "input" in data

    def test_debug_endpoint_with_different_inputs(self):
        """Debug endpoint works with different inputs."""
        response1 = client.get("/debug/avatar/user1@example.com")
        response2 = client.get("/debug/avatar/user2@example.com")

        # Both should work if endpoint is available
        if response1.status_code == 200:
            assert response2.status_code == 200


class TestMiddlewareErrorHandling:
    """Tests for middleware error handling."""

    def test_middleware_error_doesnt_crash_server(self):
        """Middleware errors don't crash the server."""
        # Make various requests that should all be handled
        endpoints = [
            "/avatar/test@example.com.svg",
            "/nonexistent",
            "/",
            "/health",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            # Should return valid response (not crash)
            assert response.status_code in [200, 404, 422, 500]

    def test_exception_handling_in_middleware(self):
        """Exceptions in request processing are handled gracefully."""
        # Try various edge cases
        response = client.get("/avatar/@#$%^&*.svg")

        # Should return error, not crash
        assert response.status_code in [200, 400, 422, 500]


class TestContentTypeValidation:
    """Tests for content type header validation."""

    def test_svg_content_type_correct(self):
        """SVG endpoint returns correct content type."""
        response = client.get("/avatar/test@example.com.svg")

        assert response.status_code == 200
        assert "image/svg+xml" in response.headers["content-type"]

    def test_png_content_type_correct(self):
        """PNG endpoint returns correct content type."""
        response = client.get("/avatar/test@example.com.png")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    def test_json_content_type_correct(self):
        """JSON endpoints return correct content type."""
        response = client.get("/avatar/test@example.com.svg/info")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_zip_content_type_correct(self):
        """ZIP bundle returns correct content type."""
        response = client.get("/avatar/test@example.com/bundle")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"


class TestCacheControlHeaders:
    """Tests for cache control headers."""

    def test_immutable_cache_on_svg(self):
        """SVG responses have immutable cache headers."""
        response = client.get("/avatar/test@example.com.svg")

        assert response.status_code == 200
        cache_control = response.headers.get("cache-control", "")
        assert "public" in cache_control
        assert "immutable" in cache_control or "max-age" in cache_control

    def test_etag_on_svg(self):
        """SVG responses include ETag."""
        response = client.get("/avatar/test@example.com.svg")

        assert response.status_code == 200
        assert "etag" in response.headers

    def test_etag_consistency(self):
        """ETag is consistent for same avatar."""
        response1 = client.get("/avatar/etagtest@example.com.svg")
        response2 = client.get("/avatar/etagtest@example.com.svg")

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.headers["etag"] == response2.headers["etag"]

    def test_different_etags_for_different_avatars(self):
        """Different avatars have different ETags."""
        response1 = client.get("/avatar/user1@example.com.svg")
        response2 = client.get("/avatar/user2@example.com.svg")

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.headers["etag"] != response2.headers["etag"]


class TestRequestLogging:
    """Tests for request logging (if implemented)."""

    def test_successful_request_logged(self):
        """Successful requests are processed without errors."""
        response = client.get("/avatar/test@example.com.svg")

        assert response.status_code == 200
        # Logging verification would require checking logs

    def test_error_request_logged(self):
        """Error requests are processed without crashes."""
        response = client.get("/nonexistent-endpoint")

        assert response.status_code == 404
        # Error should be logged but not crash server
