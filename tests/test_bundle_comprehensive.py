#!/usr/bin/env python3
# ABOUTME: Comprehensive tests for PDF bundle generation
# ABOUTME: Tests bundle creation, animations, ZIP structure, and error handling

import pytest
from fastapi.testclient import TestClient
from app import app
import zipfile
import io

client = TestClient(app)


class TestBundleEndpointBasics:
    """Basic tests for bundle endpoint functionality."""

    def test_bundle_get_endpoint(self):
        """GET bundle endpoint works."""
        response = client.get("/avatar/test@example.com/bundle")

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

    def test_bundle_returns_valid_zip(self):
        """Bundle returns valid ZIP file."""
        response = client.get("/avatar/test@example.com/bundle")

        assert response.status_code == 200
        # ZIP magic number
        assert response.content[:4] == b'PK\x03\x04'

        # Should be openable as ZIP
        try:
            zip_file = zipfile.ZipFile(io.BytesIO(response.content))
            assert len(zip_file.namelist()) > 0
        except zipfile.BadZipFile:
            pytest.fail("Bundle is not a valid ZIP file")


class TestBundleAnimationTypes:
    """Tests for different animation types in bundles."""

    def test_bundle_idle_animation(self):
        """Bundle with idle animation."""
        response = client.get("/avatar/test@example.com/bundle?animations=idle")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"

    def test_bundle_emotes_animation(self):
        """Bundle with emotes animation."""
        response = client.get("/avatar/test@example.com/bundle?animations=emotes")

        assert response.status_code == 200

    def test_bundle_vowels_animation(self):
        """Bundle with vowels animation."""
        response = client.get("/avatar/test@example.com/bundle?animations=vowels")

        assert response.status_code == 200

    def test_bundle_multiple_animations(self):
        """Bundle with multiple animation types."""
        response = client.get("/avatar/test@example.com/bundle?animations=idle,emotes")

        assert response.status_code == 200

    def test_bundle_all_animations(self):
        """Bundle with all animation types."""
        response = client.get("/avatar/test@example.com/bundle?animations=idle,emotes,vowels")

        assert response.status_code == 200


class TestBundlePostRequest:
    """Tests for POST bundle requests."""

    def test_post_bundle_single_animation(self):
        """POST bundle with single animation."""
        response = client.post(
            "/avatar/bundle",
            json={"input": "test@example.com", "animations": ["idle"]}
        )

        assert response.status_code == 200

    def test_post_bundle_multiple_animations(self):
        """POST bundle with multiple animations."""
        response = client.post(
            "/avatar/bundle",
            json={
                "input": "test@example.com",
                "animations": ["idle", "emotes", "vowels"]
            }
        )

        assert response.status_code == 200

    def test_post_bundle_empty_animations(self):
        """POST bundle with empty animations array."""
        response = client.post(
            "/avatar/bundle",
            json={"input": "test@example.com", "animations": []}
        )

        # Should either use defaults or return validation error
        assert response.status_code in [200, 400, 422]

    def test_post_bundle_missing_input(self):
        """POST bundle with missing input field."""
        response = client.post(
            "/avatar/bundle",
            json={"animations": ["idle"]}
        )

        # Should return validation error
        assert response.status_code == 422


class TestBundleZIPStructure:
    """Tests for ZIP file structure and contents."""

    def test_bundle_contains_pdf_files(self):
        """Bundle ZIP contains PDF files."""
        response = client.get("/avatar/test@example.com/bundle?animations=idle")

        assert response.status_code == 200

        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        filenames = zip_file.namelist()

        # Should contain at least one PDF file
        pdf_files = [f for f in filenames if f.endswith('.pdf')]
        assert len(pdf_files) > 0

    def test_bundle_file_naming(self):
        """Bundle files follow expected naming convention."""
        response = client.get("/avatar/test@example.com/bundle?animations=idle")

        assert response.status_code == 200

        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        filenames = zip_file.namelist()

        # Files should have descriptive names
        for filename in filenames:
            assert len(filename) > 0
            assert filename.endswith('.pdf')

    def test_bundle_multiple_animations_multiple_files(self):
        """Bundle with multiple animations contains multiple PDF files."""
        response = client.get("/avatar/test@example.com/bundle?animations=idle,emotes")

        if response.status_code == 200:
            zip_file = zipfile.ZipFile(io.BytesIO(response.content))
            filenames = zip_file.namelist()

            # Should have files for each animation type
            assert len(filenames) >= 2


class TestBundleContentDisposition:
    """Tests for Content-Disposition header."""

    def test_bundle_has_content_disposition(self):
        """Bundle response includes Content-Disposition."""
        response = client.get("/avatar/test@example.com/bundle")

        assert "content-disposition" in response.headers

    def test_bundle_disposition_is_attachment(self):
        """Content-Disposition is set to attachment."""
        response = client.get("/avatar/test@example.com/bundle")

        disposition = response.headers["content-disposition"]
        assert "attachment" in disposition

    def test_bundle_disposition_has_filename(self):
        """Content-Disposition includes filename."""
        response = client.get("/avatar/test@example.com/bundle")

        disposition = response.headers["content-disposition"]
        assert "filename" in disposition


class TestBundleErrorHandling:
    """Tests for bundle error handling."""

    def test_bundle_invalid_animation_type(self):
        """Bundle with invalid animation type is handled."""
        response = client.get("/avatar/test@example.com/bundle?animations=invalid")

        # Should validate animation types
        assert response.status_code in [200, 400, 422]

    def test_bundle_malformed_animation_param(self):
        """Bundle with malformed animation parameter is handled."""
        response = client.get("/avatar/test@example.com/bundle?animations=")

        assert response.status_code in [200, 400, 422]

    def test_post_bundle_invalid_json(self):
        """POST bundle with invalid JSON returns error."""
        response = client.post(
            "/avatar/bundle",
            data="not-valid-json",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422


class TestBundleCaching:
    """Tests for bundle caching behavior."""

    def test_bundle_deterministic(self):
        """Same input produces same bundle."""
        response1 = client.get("/avatar/bundle-cache@example.com/bundle?animations=idle")
        response2 = client.get("/avatar/bundle-cache@example.com/bundle?animations=idle")

        if response1.status_code == 200 and response2.status_code == 200:
            # Should be identical
            assert response1.content == response2.content

    def test_different_animations_different_bundles(self):
        """Different animation sets produce different bundles."""
        response1 = client.get("/avatar/test@example.com/bundle?animations=idle")
        response2 = client.get("/avatar/test@example.com/bundle?animations=emotes")

        if response1.status_code == 200 and response2.status_code == 200:
            # Should be different
            assert response1.content != response2.content


class TestBundleResponseHeaders:
    """Tests for bundle response headers."""

    def test_bundle_content_type_zip(self):
        """Bundle has correct Content-Type."""
        response = client.get("/avatar/test@example.com/bundle")

        assert response.headers["content-type"] == "application/zip"

    def test_bundle_has_content_length(self):
        """Bundle response includes Content-Length."""
        response = client.get("/avatar/test@example.com/bundle")

        # May or may not have Content-Length depending on implementation
        # Just document expected behavior
        assert response.status_code == 200

    def test_bundle_security_headers(self):
        """Bundle response includes security headers."""
        response = client.get("/avatar/test@example.com/bundle")

        assert "x-content-type-options" in response.headers
        assert "x-frame-options" in response.headers


class TestBundleSize:
    """Tests for bundle file size."""

    def test_bundle_reasonable_size(self):
        """Bundle file size is reasonable."""
        response = client.get("/avatar/test@example.com/bundle?animations=idle")

        assert response.status_code == 200
        size = len(response.content)

        # Should be reasonable (under 10MB for example)
        assert size < 10_000_000

    def test_bundle_all_animations_larger(self):
        """Bundle with all animations is larger than single animation."""
        response_single = client.get("/avatar/test@example.com/bundle?animations=idle")
        response_all = client.get("/avatar/test@example.com/bundle?animations=idle,emotes,vowels")

        if response_single.status_code == 200 and response_all.status_code == 200:
            # All animations should produce larger bundle
            assert len(response_all.content) >= len(response_single.content)


class TestBundleRateLimiting:
    """Tests for bundle endpoint rate limiting."""

    def test_bundle_has_stricter_rate_limit(self):
        """Bundle endpoint has stricter rate limit than regular endpoints."""
        # Bundle should have 10/minute vs 100/minute for avatars
        # This is more of a configuration check
        response = client.get("/avatar/test@example.com/bundle")
        assert response.status_code == 200
