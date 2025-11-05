#!/usr/bin/env python3
# ABOUTME: Tests for PDF bundle with transition frames
# ABOUTME: Validates multi-frame emote and vowel animations

import pytest
import zipfile
import io
import json
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
    """Test that metadata.json includes proper transition frame structure."""
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
        assert "frames" in emotes
        assert "sequences" in emotes

        # Check emotes frames list structure
        assert isinstance(emotes["frames"], list)
        assert len(emotes["frames"]) == 20  # 5 emotes × 4 unique weights

        # Validate a sample frame object
        happy_zero = next(f for f in emotes["frames"]
                         if f["emote"] == "happy" and f["weight"] == 0)
        assert happy_zero["filename"] == "emote_happy_weight_0.svg"
        assert happy_zero["type"] == "emote"

        # Check emotes sequences structure
        assert isinstance(emotes["sequences"], dict)
        assert "happy" in emotes["sequences"]
        happy_seq = emotes["sequences"]["happy"]
        assert len(happy_seq) == 7  # 7 frames in sequence
        assert happy_seq == [
            "emote_happy_weight_0.svg",
            "emote_happy_weight_25.svg",
            "emote_happy_weight_50.svg",
            "emote_happy_weight_100.svg",
            "emote_happy_weight_50.svg",
            "emote_happy_weight_25.svg",
            "emote_happy_weight_0.svg"
        ]

        # Validate vowels structure
        vowels = metadata["animations"]["vowels"]
        assert "frames" in vowels
        assert "sequences" in vowels

        # Check vowels frames list structure
        assert isinstance(vowels["frames"], list)
        assert len(vowels["frames"]) == 15  # 5 vowels × 3 unique weights

        # Validate a sample frame object
        a_zero = next(f for f in vowels["frames"]
                     if f["vowel"] == "a" and f["weight"] == 0)
        assert a_zero["filename"] == "vowel_a_weight_0.svg"
        assert a_zero["type"] == "vowel"

        # Check vowels sequences structure
        assert isinstance(vowels["sequences"], dict)
        assert "a" in vowels["sequences"]
        a_seq = vowels["sequences"]["a"]
        assert len(a_seq) == 5  # 5 frames in sequence
        assert a_seq == [
            "vowel_a_weight_0.svg",
            "vowel_a_weight_50.svg",
            "vowel_a_weight_100.svg",
            "vowel_a_weight_50.svg",
            "vowel_a_weight_0.svg"
        ]


def test_bundle_generates_only_unique_weight_files():
    """Test that duplicate weights in sequences don't generate duplicate files."""
    # Test emotes: should generate 20 files (4 weights × 5 emotes), not 35 (7 × 5)
    response = client.post(
        "/avatar/bundle",
        json={"input": "test@example.com", "animations": ["emotes"]}
    )

    assert response.status_code == 200

    zip_buffer = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_buffer) as zf:
        emote_files = [f for f in zf.namelist() if f.startswith("emote_")]
        assert len(emote_files) == 20, f"Expected 20 unique emote files, got {len(emote_files)}"

        # Verify each emote has exactly 4 weight files (0, 25, 50, 100)
        emotes = ["happy", "sad", "surprised", "angry", "bored"]
        for emote in emotes:
            emote_weights = [f for f in emote_files if f"emote_{emote}_" in f]
            assert len(emote_weights) == 4, f"{emote} should have 4 weight files, got {len(emote_weights)}"

        # Verify sequences reference the same files multiple times
        metadata = json.loads(zf.read("metadata.json").decode('utf-8'))
        happy_seq = metadata["animations"]["emotes"]["sequences"]["happy"]
        assert len(happy_seq) == 7, "Happy sequence should have 7 frames"
        # The sequence should reuse files: 0, 25, 50, 100, 50, 25, 0
        assert happy_seq[1] == happy_seq[5], "Frame 1 and 5 should be the same file (weight 25)"
        assert happy_seq[2] == happy_seq[4], "Frame 2 and 4 should be the same file (weight 50)"

    # Test vowels: should generate 15 files (3 weights × 5 vowels), not 25 (5 × 5)
    response = client.post(
        "/avatar/bundle",
        json={"input": "test@example.com", "animations": ["vowels"]}
    )

    assert response.status_code == 200

    zip_buffer = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_buffer) as zf:
        vowel_files = [f for f in zf.namelist() if f.startswith("vowel_")]
        assert len(vowel_files) == 15, f"Expected 15 unique vowel files, got {len(vowel_files)}"

        # Verify each vowel has exactly 3 weight files (0, 50, 100)
        vowels = ["a", "e", "i", "o", "u"]
        for vowel in vowels:
            vowel_weights = [f for f in vowel_files if f"vowel_{vowel}_" in f]
            assert len(vowel_weights) == 3, f"{vowel} should have 3 weight files, got {len(vowel_weights)}"

        # Verify sequences reference the same files multiple times
        metadata = json.loads(zf.read("metadata.json").decode('utf-8'))
        a_seq = metadata["animations"]["vowels"]["sequences"]["a"]
        assert len(a_seq) == 5, "Vowel 'a' sequence should have 5 frames"
        # The sequence should reuse files: 0, 50, 100, 50, 0
        assert a_seq[1] == a_seq[3], "Frame 1 and 3 should be the same file (weight 50)"
        assert a_seq[0] == a_seq[4], "Frame 0 and 4 should be the same file (weight 0)"


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
