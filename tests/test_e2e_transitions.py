#!/usr/bin/env python3
# ABOUTME: End-to-end tests for transition system
# ABOUTME: Tests full workflow from generation to API to caching

import pytest
import hashlib
import io
import zipfile
from pathlib import Path
from PyPDF2 import PdfReader
from fastapi.testclient import TestClient
from app import app, CACHE_DIR
from door_agents import DoorAgentConfig, DoorAgentGenerator

client = TestClient(app)


class TestTransitionWorkflow:
    """Test complete transition workflow from generation to API."""

    def test_full_transition_workflow(self):
        """Test complete workflow: generate -> cache -> retrieve."""
        input_str = "workflow@example.com"
        emote = "happy"
        weight = 75

        # Clear cache
        hash_hex = hashlib.sha256(input_str.encode('utf-8')).hexdigest()[:16]
        cache_path = CACHE_DIR / f"{hash_hex}_transition_{emote}_{weight}.svg"
        if cache_path.exists():
            cache_path.unlink()

        # First request generates
        response1 = client.get(f"/avatar/{input_str}/transition/{emote}/{weight}")
        assert response1.status_code == 200
        content1 = response1.content

        # Verify cache was created
        assert cache_path.exists()

        # Second request uses cache
        response2 = client.get(f"/avatar/{input_str}/transition/{emote}/{weight}")
        assert response2.status_code == 200
        assert response2.content == content1

    def test_bundle_contains_valid_transitions(self):
        """Test that bundle contains valid multi-page PDFs."""
        response = client.post(
            "/avatar/bundle",
            json={"input": "bundle@example.com", "animations": ["emotes"]}
        )

        assert response.status_code == 200

        # Extract and validate PDFs
        zip_buffer = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_buffer) as zf:
            # Check one emote PDF
            pdf_bytes = zf.read("emote_happy.pdf")
            pdf_reader = PdfReader(io.BytesIO(pdf_bytes))

            # Verify it's a valid multi-page PDF with 7 pages
            assert len(pdf_reader.pages) == 7, "Happy emote PDF should have 7 pages"

            # Verify each page is valid (can be read without error)
            for i, page in enumerate(pdf_reader.pages):
                # Just accessing the page should work without error
                assert page is not None, f"Page {i} should be valid"

    def test_transition_determinism_across_api(self):
        """Test that same input produces identical transitions via API."""
        input_str = "determinism@example.com"

        responses = []
        for _ in range(3):
            resp = client.get(f"/avatar/{input_str}/transition/sad/33")
            assert resp.status_code == 200
            responses.append(resp.content)

        # All responses should be identical
        assert responses[0] == responses[1] == responses[2]

    def test_all_emotes_work_end_to_end(self):
        """Test that all emotes work through complete pipeline."""
        emotes = ["happy", "sad", "surprised", "angry", "bored"]
        input_str = "allemootes@example.com"

        for emote in emotes:
            # Test API endpoint
            response = client.get(f"/avatar/{input_str}/transition/{emote}/50")
            assert response.status_code == 200

            # Verify SVG structure
            content = response.content.decode('utf-8')
            assert '<svg' in content
            assert 'base-layer' in content
            assert 'emote-layer' in content

    def test_all_vowels_work_end_to_end(self):
        """Test that all vowels work through complete pipeline."""
        vowels = ["a", "e", "i", "o", "u"]
        input_str = "allvowels@example.com"

        for vowel in vowels:
            # Test API endpoint
            response = client.get(f"/avatar/{input_str}/transition/vowel_{vowel}/50")
            assert response.status_code == 200

            # Verify SVG structure
            content = response.content.decode('utf-8')
            assert '<svg' in content
            assert 'base-layer' in content
            assert 'emote-layer' in content

    def test_weight_progression_visual_correctness(self):
        """Test that weight progression makes visual sense."""
        input_str = "progression@example.com"
        emote = "happy"

        # Get transitions at different weights
        weights = [0, 25, 50, 75, 100]
        transitions = {}

        for weight in weights:
            response = client.get(f"/avatar/{input_str}/transition/{emote}/{weight}")
            assert response.status_code == 200
            transitions[weight] = response.content.decode('utf-8')

        # Verify opacity values are correct
        import re
        for weight in weights:
            content = transitions[weight]

            # Extract opacities from SVG
            base_match = re.search(r'id="base-layer"[^>]*opacity="([0-9.]+)"', content)
            emote_match = re.search(r'id="emote-layer"[^>]*opacity="([0-9.]+)"', content)

            assert base_match and emote_match

            base_opacity = float(base_match.group(1))
            emote_opacity = float(emote_match.group(1))

            expected_base = 1.0  # Base is always fully opaque
            expected_emote = weight / 100.0  # Emote varies from 0 to 1

            assert abs(base_opacity - expected_base) < 0.01
            assert abs(emote_opacity - expected_emote) < 0.01

    def test_error_handling_end_to_end(self):
        """Test that errors are handled gracefully."""
        # Invalid emote
        response = client.get("/avatar/test@example.com/transition/invalid/50")
        assert response.status_code == 400
        assert "Unknown emote" in response.json()["detail"]

        # Invalid weight
        response = client.get("/avatar/test@example.com/transition/happy/200")
        assert response.status_code == 400
        assert "Weight must be between 0 and 100" in response.json()["detail"]

    def test_cache_invalidation_per_input(self):
        """Test that different inputs have separate caches."""
        emote = "happy"
        weight = 50

        input1 = "cache1@example.com"
        input2 = "cache2@example.com"

        # Get transitions for both inputs
        response1 = client.get(f"/avatar/{input1}/transition/{emote}/{weight}")
        response2 = client.get(f"/avatar/{input2}/transition/{emote}/{weight}")

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Content should be different (different avatars)
        assert response1.content != response2.content

        # Both should have separate cache entries
        hash1 = hashlib.sha256(input1.encode('utf-8')).hexdigest()[:16]
        hash2 = hashlib.sha256(input2.encode('utf-8')).hexdigest()[:16]

        cache1 = CACHE_DIR / f"{hash1}_transition_{emote}_{weight}.svg"
        cache2 = CACHE_DIR / f"{hash2}_transition_{emote}_{weight}.svg"

        assert cache1.exists()
        assert cache2.exists()
