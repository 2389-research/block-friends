#!/usr/bin/env python3
import pytest
from fastapi.testclient import TestClient
from app import app
import zipfile
import io
from PyPDF2 import PdfReader


client = TestClient(app)


def test_bundle_with_emotes():
    """Test that emotes bundle contains correct PDFs."""
    response = client.get("/avatar/test@example.com/bundle?animations=emotes")
    assert response.status_code == 200
    assert response.headers['content-type'] == 'application/zip'

    # Open ZIP
    zip_file = zipfile.ZipFile(io.BytesIO(response.content))
    filenames = zip_file.namelist()

    # Should have 6 emote PDFs + metadata
    expected_emotes = ['joy', 'sorrow', 'surprised', 'angry', 'bored', 'fun']
    for emote in expected_emotes:
        assert f"emote_{emote}.pdf" in filenames

    assert "metadata.json" in filenames


def test_bundle_emote_pdf_has_7_pages():
    """Test that each emote PDF has 7 pages (0, 25, 50, 100, 50, 25, 0)."""
    response = client.get("/avatar/test@example.com/bundle?animations=emotes")
    zip_file = zipfile.ZipFile(io.BytesIO(response.content))

    # Check joy PDF
    joy_pdf_bytes = zip_file.read("emote_joy.pdf")
    pdf_reader = PdfReader(io.BytesIO(joy_pdf_bytes))

    assert len(pdf_reader.pages) == 7


def test_bundle_with_vowels():
    """Test that vowels bundle contains correct PDFs."""
    response = client.get("/avatar/test@example.com/bundle?animations=vowels")
    assert response.status_code == 200

    zip_file = zipfile.ZipFile(io.BytesIO(response.content))
    filenames = zip_file.namelist()

    # Should have 5 vowel PDFs + metadata
    expected_vowels = ['A', 'E', 'I', 'O', 'U']
    for vowel in expected_vowels:
        assert f"vowel_{vowel}.pdf" in filenames

    assert "metadata.json" in filenames


def test_bundle_vowel_pdf_has_5_pages():
    """Test that each vowel PDF has 5 pages (0, 50, 100, 50, 0)."""
    response = client.get("/avatar/test@example.com/bundle?animations=vowels")
    zip_file = zipfile.ZipFile(io.BytesIO(response.content))

    # Check A PDF
    vowel_pdf_bytes = zip_file.read("vowel_A.pdf")
    pdf_reader = PdfReader(io.BytesIO(vowel_pdf_bytes))

    assert len(pdf_reader.pages) == 5


def test_bundle_combined():
    """Test that combined bundle includes both emotes and vowels."""
    response = client.get("/avatar/test@example.com/bundle?animations=emotes,vowels")
    assert response.status_code == 200

    zip_file = zipfile.ZipFile(io.BytesIO(response.content))
    filenames = zip_file.namelist()

    # Should have 6 emotes + 5 vowels + metadata = 12 files
    expected_count = 6 + 5 + 1  # emotes + vowels + metadata
    assert len(filenames) == expected_count


def test_bundle_metadata_correct():
    """Test that metadata contains correct animation specs."""
    response = client.get("/avatar/test@example.com/bundle?animations=emotes")
    zip_file = zipfile.ZipFile(io.BytesIO(response.content))

    import json
    metadata = json.loads(zip_file.read("metadata.json"))

    assert "animations" in metadata
    assert "emotes" in metadata["animations"]

    emotes_spec = metadata["animations"]["emotes"]
    assert emotes_spec["frame_count"] == 7
    assert emotes_spec["frames"] == [0, 25, 50, 100, 50, 25, 0]


def test_bundle_deterministic():
    """Test that same input produces same structure and page counts."""
    response1 = client.get("/avatar/same@input.com/bundle?animations=emotes")
    response2 = client.get("/avatar/same@input.com/bundle?animations=emotes")

    # Both should be valid ZIP files
    assert response1.status_code == 200
    assert response2.status_code == 200

    # Open and compare contents
    zip1 = zipfile.ZipFile(io.BytesIO(response1.content))
    zip2 = zipfile.ZipFile(io.BytesIO(response2.content))

    # Should have same files
    assert sorted(zip1.namelist()) == sorted(zip2.namelist())

    # Each PDF should have same page count (PDFs may differ in internal structure but should be functionally identical)
    for filename in zip1.namelist():
        if filename.endswith('.pdf'):
            pdf1 = PdfReader(io.BytesIO(zip1.read(filename)))
            pdf2 = PdfReader(io.BytesIO(zip2.read(filename)))
            assert len(pdf1.pages) == len(pdf2.pages), f"PDF {filename} has different page counts"
