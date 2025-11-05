#!/usr/bin/env python3
# ABOUTME: Tests for PDF bundle with transition frames
# ABOUTME: Validates multi-frame emote and vowel animations

import pytest
import zipfile
import io
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_bundle_emotes_includes_transitions():
    """Test that emotes bundle includes 7-frame transition sequence."""
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

        # Check for emote sequences (7 frames each)
        emotes = ["happy", "sad", "surprised", "angry", "bored"]
        for emote in emotes:
            # Each emote should have frames: 0, 25, 50, 100, 50, 25, 0
            expected_frames = [f"emote_{emote}_weight_{w}.svg"
                             for w in [0, 25, 50, 100, 50, 25, 0]]
            for frame_file in expected_frames:
                assert frame_file in files, f"Missing {frame_file} in bundle"


def test_bundle_vowels_includes_transitions():
    """Test that vowels bundle includes 5-frame transition sequence."""
    response = client.post(
        "/avatar/bundle",
        json={"input": "test@example.com", "animations": ["vowels"]}
    )

    assert response.status_code == 200

    # Extract and verify bundle contents
    zip_buffer = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_buffer) as zf:
        files = zf.namelist()

        # Check for vowel sequences (5 frames each)
        vowels = ["a", "e", "i", "o", "u"]
        for vowel in vowels:
            # Each vowel should have frames: 0, 50, 100, 50, 0
            expected_frames = [f"vowel_{vowel}_weight_{w}.svg"
                             for w in [0, 50, 100, 50, 0]]
            for frame_file in expected_frames:
                assert frame_file in files, f"Missing {frame_file} in bundle"


def test_bundle_metadata_includes_transitions():
    """Test that metadata.json includes transition frame info."""
    response = client.post(
        "/avatar/bundle",
        json={"input": "test@example.com", "animations": ["emotes", "vowels"]}
    )

    assert response.status_code == 200

    # Extract and check metadata
    zip_buffer = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_buffer) as zf:
        metadata = zf.read("metadata.json").decode('utf-8')

        # Verify metadata mentions transitions
        assert "emote_happy_weight_0" in metadata
        assert "emote_happy_weight_25" in metadata
        assert "emote_happy_weight_50" in metadata
        assert "emote_happy_weight_100" in metadata
        assert "vowel_a_weight_0" in metadata
        assert "vowel_a_weight_50" in metadata
        assert "vowel_a_weight_100" in metadata


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

        # Should have emote transition frames
        assert "emote_happy_weight_0.svg" in files
        assert "emote_happy_weight_100.svg" in files

        # Should have vowel transition frames
        assert "vowel_a_weight_0.svg" in files
        assert "vowel_a_weight_100.svg" in files
