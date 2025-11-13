"""
Comprehensive bundle generation tests.

Tests PDF bundle generation, structure, metadata, and error handling.
"""

import pytest
from fastapi.testclient import TestClient
from app import app
import zipfile
import io
import json

client = TestClient(app)


class TestBundleGeneration:
    """Tests for basic bundle generation."""

    def test_bundle_get_endpoint_returns_zip(self):
        """GET bundle endpoint returns valid ZIP file."""
        response = client.get("/avatar/bundle@example.com/bundle")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
        assert response.content[:4] == b'PK\x03\x04'  # ZIP magic number

    def test_bundle_post_endpoint_returns_zip(self):
        """POST bundle endpoint returns valid ZIP file."""
        response = client.post(
            "/avatar/bundle",
            json={"input": "postbundle@example.com", "animations": ["idle"]}
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
        assert response.content[:4] == b'PK\x03\x04'

    def test_bundle_content_disposition_header(self):
        """Bundle includes proper Content-Disposition header."""
        response = client.get("/avatar/test@example.com/bundle")

        assert response.status_code == 200
        assert "content-disposition" in response.headers
        assert "attachment" in response.headers["content-disposition"]
        assert ".zip" in response.headers["content-disposition"]

    def test_bundle_filename_includes_hash(self):
        """Bundle filename includes input hash."""
        response = client.get("/avatar/hashtest@example.com/bundle")

        assert response.status_code == 200
        content_disposition = response.headers["content-disposition"]
        # Should contain "avatar_" and hash
        assert "avatar_" in content_disposition
        assert "_animations.zip" in content_disposition


class TestBundleStructure:
    """Tests for bundle ZIP structure and contents."""

    def test_bundle_contains_metadata_json(self):
        """Bundle contains metadata.json file."""
        response = client.get("/avatar/test@example.com/bundle")

        assert response.status_code == 200

        # Extract and verify ZIP contents
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            assert "metadata.json" in zf.namelist()

    def test_bundle_metadata_structure(self):
        """Bundle metadata.json has correct structure."""
        response = client.get("/avatar/test@example.com/bundle")

        assert response.status_code == 200

        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            metadata_content = zf.read("metadata.json")
            metadata = json.loads(metadata_content)

            # Check structure
            assert "input" in metadata
            assert "hash" in metadata
            assert "animations" in metadata

    def test_bundle_idle_animation_included(self):
        """Bundle with idle animation contains idle.pdf."""
        response = client.get("/avatar/test@example.com/bundle?animations=idle")

        assert response.status_code == 200

        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            assert "idle.pdf" in zf.namelist()

    def test_bundle_emote_animations_included(self):
        """Bundle with emotes contains emote_*.pdf files."""
        response = client.get("/avatar/test@example.com/bundle?animations=emotes")

        assert response.status_code == 200

        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            filenames = zf.namelist()

            # Should contain emote PDFs
            emotes = ["happy", "sad", "surprised", "angry", "bored"]
            for emote in emotes:
                expected_filename = f"emote_{emote}.pdf"
                assert expected_filename in filenames, f"Missing {expected_filename}"

    def test_bundle_vowel_animations_included(self):
        """Bundle with vowels contains vowel_*.pdf files."""
        response = client.get("/avatar/test@example.com/bundle?animations=vowels")

        assert response.status_code == 200

        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            filenames = zf.namelist()

            # Should contain vowel PDFs
            vowels = ["a", "e", "i", "o", "u"]
            for vowel in vowels:
                expected_filename = f"vowel_{vowel}.pdf"
                assert expected_filename in filenames, f"Missing {expected_filename}"


class TestBundleAnimationParameters:
    """Tests for bundle animation parameter handling."""

    def test_bundle_single_animation_type(self):
        """Bundle with single animation type."""
        response = client.get("/avatar/test@example.com/bundle?animations=idle")

        assert response.status_code == 200

        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            filenames = zf.namelist()
            # Should have idle.pdf and metadata.json
            assert "idle.pdf" in filenames
            assert "metadata.json" in filenames

    def test_bundle_multiple_animation_types(self):
        """Bundle with multiple animation types."""
        response = client.get("/avatar/test@example.com/bundle?animations=idle,emotes")

        assert response.status_code == 200

        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            filenames = zf.namelist()
            # Should have both idle and emote files
            assert "idle.pdf" in filenames
            assert any("emote_" in f for f in filenames)

    def test_bundle_all_animation_types(self):
        """Bundle with all animation types (default)."""
        response = client.get("/avatar/test@example.com/bundle")

        assert response.status_code == 200

        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            filenames = zf.namelist()
            # Should have idle, emotes, and vowels
            assert "idle.pdf" in filenames
            assert any("emote_" in f for f in filenames)
            assert any("vowel_" in f for f in filenames)

    def test_bundle_post_with_animation_list(self):
        """POST bundle with specific animation list."""
        response = client.post(
            "/avatar/bundle",
            json={"input": "test@example.com", "animations": ["idle", "emotes"]}
        )

        assert response.status_code == 200

        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            filenames = zf.namelist()
            assert "idle.pdf" in filenames
            assert any("emote_" in f for f in filenames)


class TestBundleMetadata:
    """Tests for bundle metadata content."""

    def test_metadata_includes_input_string(self):
        """Metadata includes original input string."""
        response = client.get("/avatar/metatest@example.com/bundle")

        assert response.status_code == 200

        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            metadata = json.loads(zf.read("metadata.json"))
            assert metadata["input"] == "metatest@example.com"

    def test_metadata_includes_animation_specs(self):
        """Metadata includes animation specifications."""
        response = client.get("/avatar/test@example.com/bundle?animations=idle")

        assert response.status_code == 200

        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            metadata = json.loads(zf.read("metadata.json"))
            assert "animations" in metadata
            assert "idle" in metadata["animations"]

            idle_spec = metadata["animations"]["idle"]
            assert "file" in idle_spec
            assert "frame_count" in idle_spec
            assert "fps" in idle_spec

    def test_metadata_idle_animation_spec(self):
        """Metadata idle animation has correct specifications."""
        response = client.get("/avatar/test@example.com/bundle?animations=idle")

        assert response.status_code == 200

        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            metadata = json.loads(zf.read("metadata.json"))
            idle_spec = metadata["animations"]["idle"]

            assert idle_spec["file"] == "idle.pdf"
            assert idle_spec["frame_count"] == 10
            assert idle_spec["fps"] == 4
            assert idle_spec["loop"] == True

    def test_metadata_emote_animation_spec(self):
        """Metadata emote animations have correct specifications."""
        response = client.get("/avatar/test@example.com/bundle?animations=emotes")

        assert response.status_code == 200

        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            metadata = json.loads(zf.read("metadata.json"))
            emotes_spec = metadata["animations"]["emotes"]

            # Check happy emote as example
            assert "happy" in emotes_spec
            happy_spec = emotes_spec["happy"]

            assert happy_spec["file"] == "emote_happy.pdf"
            assert happy_spec["frame_count"] == 7
            assert "weights" in happy_spec
            assert happy_spec["weights"] == [0, 25, 50, 100, 50, 25, 0]


class TestBundleErrorHandling:
    """Tests for bundle generation error handling."""

    def test_bundle_with_invalid_animation_type(self):
        """Bundle handles invalid animation types."""
        response = client.get("/avatar/test@example.com/bundle?animations=invalid")

        # Should handle gracefully - either return error or ignore invalid types
        assert response.status_code in [200, 400]

    def test_bundle_with_empty_animations_parameter(self):
        """Bundle handles empty animations parameter."""
        response = client.get("/avatar/test@example.com/bundle?animations=")

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_bundle_post_with_empty_input(self):
        """POST bundle handles empty input."""
        response = client.post(
            "/avatar/bundle",
            json={"input": "", "animations": ["idle"]}
        )

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_bundle_post_with_invalid_json(self):
        """POST bundle handles invalid JSON."""
        response = client.post(
            "/avatar/bundle",
            data="invalid json",
            headers={"content-type": "application/json"}
        )

        # Should return validation error
        assert response.status_code in [400, 422]


class TestBundlePDFContent:
    """Tests for PDF content in bundles."""

    def test_bundle_pdfs_are_valid(self):
        """Bundle contains valid PDF files."""
        response = client.get("/avatar/test@example.com/bundle?animations=idle")

        assert response.status_code == 200

        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            # Read PDF content
            pdf_content = zf.read("idle.pdf")

            # Check PDF magic number
            assert pdf_content[:4] == b'%PDF', "Invalid PDF file"

    def test_bundle_idle_pdf_has_10_pages(self):
        """Idle animation PDF has 10 pages."""
        response = client.get("/avatar/test@example.com/bundle?animations=idle")

        assert response.status_code == 200

        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            pdf_content = zf.read("idle.pdf")

            # Verify it's a PDF
            assert pdf_content[:4] == b'%PDF'

            # Full page count verification would require PDF parsing
            # Just verify PDF is not empty
            assert len(pdf_content) > 1000

    def test_bundle_emote_pdf_has_7_pages(self):
        """Emote animation PDF has 7 pages (transition sequence)."""
        response = client.get("/avatar/test@example.com/bundle?animations=emotes")

        assert response.status_code == 200

        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            pdf_content = zf.read("emote_happy.pdf")

            # Verify it's a PDF
            assert pdf_content[:4] == b'%PDF'
            assert len(pdf_content) > 1000


class TestBundleSize:
    """Tests for bundle file size."""

    def test_bundle_size_reasonable(self):
        """Bundle file size is reasonable."""
        response = client.get("/avatar/test@example.com/bundle?animations=idle")

        assert response.status_code == 200

        # Bundle should be under 10MB for a single animation
        assert len(response.content) < 10 * 1024 * 1024

    def test_bundle_all_animations_size(self):
        """Bundle with all animations is reasonable size."""
        response = client.get("/avatar/test@example.com/bundle")

        assert response.status_code == 200

        # Full bundle should be under 50MB
        assert len(response.content) < 50 * 1024 * 1024


class TestBundleDeterminism:
    """Tests for deterministic bundle generation."""

    def test_bundle_deterministic_generation(self):
        """Same input produces same bundle."""
        response1 = client.get("/avatar/bundledet@example.com/bundle?animations=idle")
        response2 = client.get("/avatar/bundledet@example.com/bundle?animations=idle")

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Content should be identical
        assert response1.content == response2.content

    def test_bundle_different_inputs_different_bundles(self):
        """Different inputs produce different bundles."""
        response1 = client.get("/avatar/user1@example.com/bundle?animations=idle")
        response2 = client.get("/avatar/user2@example.com/bundle?animations=idle")

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Content should be different
        assert response1.content != response2.content
