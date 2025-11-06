#!/usr/bin/env python3
# ABOUTME: Tests for PDF bundle with transition frames
# ABOUTME: Validates multi-page PDF emote and vowel animations

import pytest
import zipfile
import io
import json
from PyPDF2 import PdfReader
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_bundle_emotes_includes_transitions():
    """Test that emotes bundle includes multi-page PDFs (7 pages each)."""
    response = client.post(
        "/avatar/bundle",
        json={"input": "test@example.com", "animations": ["emotes"]}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"

    # Extract and verify bundle contents
    zip_buffer = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_buffer) as zf:
        files = zf.namelist()

        # Check for emote PDFs (one per emote)
        emotes = ["happy", "sad", "surprised", "angry", "bored"]
        for emote in emotes:
            pdf_filename = f"emote_{emote}.pdf"
            assert pdf_filename in files, f"Missing {pdf_filename} in bundle"

            # Verify PDF has 7 pages (one for each frame: 0, 25, 50, 100, 50, 25, 0)
            pdf_bytes = zf.read(pdf_filename)
            pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
            assert len(pdf_reader.pages) == 7, f"{pdf_filename} should have 7 pages"


def test_bundle_vowels_includes_transitions():
    """Test that vowels bundle includes multi-page PDFs (5 pages each)."""
    response = client.post(
        "/avatar/bundle",
        json={"input": "test@example.com", "animations": ["vowels"]}
    )

    assert response.status_code == 200

    # Extract and verify bundle contents
    zip_buffer = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_buffer) as zf:
        files = zf.namelist()

        # Check for vowel PDFs (one per vowel)
        vowels = ["a", "e", "i", "o", "u"]
        for vowel in vowels:
            pdf_filename = f"vowel_{vowel}.pdf"
            assert pdf_filename in files, f"Missing {pdf_filename} in bundle"

            # Verify PDF has 5 pages (one for each frame: 0, 50, 100, 50, 0)
            pdf_bytes = zf.read(pdf_filename)
            pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
            assert len(pdf_reader.pages) == 5, f"{pdf_filename} should have 5 pages"


def test_bundle_metadata_includes_transitions():
    """Test that metadata.json includes proper multi-page PDF structure."""
    response = client.post(
        "/avatar/bundle",
        json={"input": "test@example.com", "animations": ["emotes", "vowels"]}
    )

    assert response.status_code == 200

    # Extract and parse metadata as JSON
    zip_buffer = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_buffer) as zf:
        metadata = json.loads(zf.read("metadata.json").decode('utf-8'))

        # Validate top-level structure
        assert "animations" in metadata
        assert "emotes" in metadata["animations"]
        assert "vowels" in metadata["animations"]

        # Validate emotes structure
        emotes = metadata["animations"]["emotes"]
        assert isinstance(emotes, dict)

        # Check each emote has correct structure
        assert "happy" in emotes
        happy = emotes["happy"]
        assert happy["file"] == "emote_happy.pdf"
        assert happy["frame_count"] == 7
        assert happy["weights"] == [0, 25, 50, 100, 50, 25, 0]
        assert happy["fps"] == 6.67

        # Verify all 5 emotes present
        assert len(emotes) == 5
        for emote_name in ["happy", "sad", "surprised", "angry", "bored"]:
            assert emote_name in emotes
            assert emotes[emote_name]["frame_count"] == 7

        # Validate vowels structure
        vowels = metadata["animations"]["vowels"]
        assert isinstance(vowels, dict)

        # Check each vowel has correct structure
        assert "a" in vowels
        a = vowels["a"]
        assert a["file"] == "vowel_a.pdf"
        assert a["frame_count"] == 5
        assert a["weights"] == [0, 50, 100, 50, 0]
        assert a["fps"] == 6.67

        # Verify all 5 vowels present
        assert len(vowels) == 5
        for vowel_name in ["a", "e", "i", "o", "u"]:
            assert vowel_name in vowels
            assert vowels[vowel_name]["frame_count"] == 5


def test_bundle_generates_pdfs_not_individual_frames():
    """Test that bundles contain multi-page PDFs, not individual frame files."""
    # Test emotes: should generate 5 PDFs (one per emote), not individual frame files
    response = client.post(
        "/avatar/bundle",
        json={"input": "test@example.com", "animations": ["emotes"]}
    )

    assert response.status_code == 200

    zip_buffer = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_buffer) as zf:
        files = zf.namelist()

        # Count PDF files
        emote_pdfs = [f for f in files if f.startswith("emote_") and f.endswith(".pdf")]
        assert len(emote_pdfs) == 5, f"Expected 5 emote PDFs, got {len(emote_pdfs)}"

        # Verify no individual SVG/frame files
        svg_files = [f for f in files if f.endswith(".svg")]
        assert len(svg_files) == 0, "Should not have individual SVG files in bundle"

        # Verify each PDF has 7 pages
        for pdf_file in emote_pdfs:
            pdf_bytes = zf.read(pdf_file)
            pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
            assert len(pdf_reader.pages) == 7, f"{pdf_file} should have 7 pages"

    # Test vowels: should generate 5 PDFs (one per vowel)
    response = client.post(
        "/avatar/bundle",
        json={"input": "test@example.com", "animations": ["vowels"]}
    )

    assert response.status_code == 200

    zip_buffer = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_buffer) as zf:
        files = zf.namelist()

        # Count PDF files
        vowel_pdfs = [f for f in files if f.startswith("vowel_") and f.endswith(".pdf")]
        assert len(vowel_pdfs) == 5, f"Expected 5 vowel PDFs, got {len(vowel_pdfs)}"

        # Verify no individual SVG files
        svg_files = [f for f in files if f.endswith(".svg")]
        assert len(svg_files) == 0, "Should not have individual SVG files in bundle"

        # Verify each PDF has 5 pages
        for pdf_file in vowel_pdfs:
            pdf_bytes = zf.read(pdf_file)
            pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
            assert len(pdf_reader.pages) == 5, f"{pdf_file} should have 5 pages"


def test_bundle_all_animations():
    """Test bundle with all animation types."""
    response = client.post(
        "/avatar/bundle",
        json={"input": "test@example.com", "animations": ["idle", "emotes", "vowels"]}
    )

    assert response.status_code == 200

    zip_buffer = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_buffer) as zf:
        files = zf.namelist()

        # Should have idle PDF
        assert "idle.pdf" in files

        # Should have emote PDFs
        assert "emote_happy.pdf" in files
        assert "emote_sad.pdf" in files

        # Should have vowel PDFs
        assert "vowel_a.pdf" in files
        assert "vowel_e.pdf" in files

        # Verify metadata
        metadata = json.loads(zf.read("metadata.json").decode('utf-8'))
        assert "idle" in metadata["animations"]
        assert "emotes" in metadata["animations"]
        assert "vowels" in metadata["animations"]
