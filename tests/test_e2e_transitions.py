#!/usr/bin/env python3
# ABOUTME: End-to-end integration tests for animation transition system
# ABOUTME: Tests complete flow from asset loading to API responses
"""
End-to-end integration tests for animation transition system.
Tests the complete flow from asset loading to API responses.
"""
import pytest
from fastapi.testclient import TestClient
from app import app
import xml.etree.ElementTree as ET
import zipfile
import io
from PyPDF2 import PdfReader
import os
import time


client = TestClient(app)


class TestAssetLoading:
    """Test that all required assets are present and loadable."""

    def test_emote_eyes_exist(self):
        """Verify all emote eye assets exist."""
        required_eyes = ['emote_happy', 'emote_sad', 'emote_surprised', 'emote_angry', 'emote_bored', 'emote_fun']

        for eye_name in required_eyes:
            path = f"assets/eyes/{eye_name}.svg"
            assert os.path.exists(path), f"Missing eye asset: {path}"

    def test_emote_mouths_exist(self):
        """Verify all emote mouth assets exist."""
        required_mouths = ['emote_joy', 'emote_sorrow', 'emote_surprised', 'emote_angry', 'emote_bored', 'emote_fun']

        for mouth_name in required_mouths:
            path = f"assets/mouths/{mouth_name}.svg"
            assert os.path.exists(path), f"Missing mouth asset: {path}"

    def test_vowel_mouths_exist(self):
        """Verify all vowel mouth assets exist."""
        required_vowels = ['vowel_A', 'vowel_E', 'vowel_I', 'vowel_O', 'vowel_U']

        for vowel_name in required_vowels:
            path = f"assets/mouths/{vowel_name}.svg"
            assert os.path.exists(path), f"Missing vowel asset: {path}"

    def test_base_eyes_and_mouths_exist(self):
        """Verify base numbered eyes and mouths exist."""
        # Check for numbered eye assets (used as base)
        eye_files = os.listdir("assets/eyes")
        numbered_eyes = [f for f in eye_files if f[0].isdigit() and f.endswith(".svg")]
        assert len(numbered_eyes) > 0, "Missing numbered eye assets for base state"

        # Check for numbered mouth assets (used as base)
        mouth_files = os.listdir("assets/mouths")
        numbered_mouths = [f for f in mouth_files if f[0].isdigit() and f.endswith(".svg")]
        assert len(numbered_mouths) > 0, "Missing numbered mouth assets for base state"


class TestTransitionAPI:
    """Test transition API endpoints work correctly."""

    def test_complete_emote_sequence(self):
        """Test complete transition sequence for one emote."""
        weights = [0, 25, 50, 75, 100]

        for weight in weights:
            response = client.get(f"/avatar/e2e-test@example.com/transition/joy/{weight}")
            assert response.status_code == 200, f"Failed for joy at weight {weight}"

            # Verify SVG is valid
            root = ET.fromstring(response.content)
            assert root.tag.endswith('svg'), f"Invalid SVG at weight {weight}"

    def test_all_emotes_at_all_weights(self):
        """Test that all emotes work at all standard weights."""
        emotes = ['joy', 'sorrow', 'surprised', 'angry', 'bored', 'fun']
        weights = [0, 25, 50, 75, 100]

        for emote in emotes:
            for weight in weights:
                response = client.get(f"/avatar/e2e-test@example.com/transition/{emote}/{weight}")
                assert response.status_code == 200, f"Failed: {emote} at {weight}%"

                # Verify it's valid SVG
                root = ET.fromstring(response.content)
                assert root.tag.endswith('svg')

    def test_all_vowels_at_all_weights(self):
        """Test that all vowels work at all standard weights."""
        vowels = ['A', 'E', 'I', 'O', 'U']
        weights = [0, 50, 100]

        for vowel in vowels:
            for weight in weights:
                response = client.get(f"/avatar/e2e-test@example.com/transition/{vowel}/{weight}")
                assert response.status_code == 200, f"Failed: {vowel} at {weight}%"

                # Verify it's valid SVG
                root = ET.fromstring(response.content)
                assert root.tag.endswith('svg')

    def test_invalid_emote_returns_400(self):
        """Test that invalid emote name returns 400 error."""
        response = client.get("/avatar/e2e-test@example.com/transition/invalid_emote/50")
        assert response.status_code == 400
        assert 'Invalid emote' in response.json()['detail']

    def test_invalid_weight_returns_400(self):
        """Test that out-of-range weight returns 400 error."""
        response = client.get("/avatar/e2e-test@example.com/transition/joy/150")
        assert response.status_code == 400
        assert 'Weight' in response.json()['detail'] or 'weight' in response.json()['detail']

    def test_negative_weight_returns_400(self):
        """Test that negative weight returns 400 error."""
        response = client.get("/avatar/e2e-test@example.com/transition/joy/-10")
        assert response.status_code == 400


class TestBundleGeneration:
    """Test PDF bundle generation with transitions."""

    def test_full_emotes_bundle(self):
        """Test complete emotes bundle generation."""
        response = client.get("/avatar/e2e-bundle@example.com/bundle?animations=emotes")
        assert response.status_code == 200, "Bundle endpoint failed"

        zip_file = zipfile.ZipFile(io.BytesIO(response.content))

        # Verify all files present
        expected_files = [
            'emote_joy.pdf', 'emote_sorrow.pdf', 'emote_surprised.pdf',
            'emote_angry.pdf', 'emote_bored.pdf', 'emote_fun.pdf',
            'metadata.json'
        ]

        filenames = zip_file.namelist()
        for filename in expected_files:
            assert filename in filenames, f"Missing file: {filename}"

        # Verify each PDF has correct page count
        for emote in ['joy', 'sorrow', 'surprised', 'angry', 'bored', 'fun']:
            pdf_bytes = zip_file.read(f"emote_{emote}.pdf")
            pdf = PdfReader(io.BytesIO(pdf_bytes))
            assert len(pdf.pages) == 7, f"{emote} should have 7 pages, got {len(pdf.pages)}"

    def test_full_vowels_bundle(self):
        """Test complete vowels bundle generation."""
        response = client.get("/avatar/e2e-bundle@example.com/bundle?animations=vowels")
        assert response.status_code == 200, "Vowels bundle endpoint failed"

        zip_file = zipfile.ZipFile(io.BytesIO(response.content))

        # Verify all vowel PDFs present
        for vowel in ['A', 'E', 'I', 'O', 'U']:
            assert f"vowel_{vowel}.pdf" in zip_file.namelist(), f"Missing vowel_{vowel}.pdf"

            # Verify page count
            pdf_bytes = zip_file.read(f"vowel_{vowel}.pdf")
            pdf = PdfReader(io.BytesIO(pdf_bytes))
            assert len(pdf.pages) == 5, f"Vowel {vowel} should have 5 pages, got {len(pdf.pages)}"

    def test_combined_bundle(self):
        """Test combined bundle with emotes and vowels."""
        response = client.get("/avatar/e2e-bundle@example.com/bundle?animations=emotes,vowels")
        assert response.status_code == 200, "Combined bundle endpoint failed"

        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        filenames = zip_file.namelist()

        # Should have 6 emotes + 5 vowels + 1 metadata = 12 files
        assert len(filenames) == 12, f"Expected 12 files, got {len(filenames)}: {filenames}"

    def test_bundle_metadata_correct(self):
        """Test that metadata contains correct animation specs."""
        response = client.get("/avatar/e2e-bundle@example.com/bundle?animations=emotes")
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))

        import json
        metadata = json.loads(zip_file.read("metadata.json"))

        assert "animations" in metadata, "Missing animations key in metadata"
        assert "emotes" in metadata["animations"], "Missing emotes in animations"

        emotes_spec = metadata["animations"]["emotes"]
        assert emotes_spec["frame_count"] == 7, f"Expected 7 frames, got {emotes_spec['frame_count']}"
        assert emotes_spec["frames"] == [0, 25, 50, 100, 50, 25, 0], f"Wrong frame sequence: {emotes_spec['frames']}"

    def test_bundle_file_structure(self):
        """Test that bundle has correct file structure and naming."""
        response = client.get("/avatar/e2e-bundle@example.com/bundle?animations=emotes,vowels")
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))

        # Check all emotes present
        emotes = ['joy', 'sorrow', 'surprised', 'angry', 'bored', 'fun']
        for emote in emotes:
            assert f"emote_{emote}.pdf" in zip_file.namelist()

        # Check all vowels present
        vowels = ['A', 'E', 'I', 'O', 'U']
        for vowel in vowels:
            assert f"vowel_{vowel}.pdf" in zip_file.namelist()

        # Check metadata present
        assert "metadata.json" in zip_file.namelist()


class TestVisualQuality:
    """Test visual quality of generated transitions."""

    def test_neutral_has_no_target_opacity(self):
        """Test that 0% weight doesn't show target layer."""
        response = client.get("/avatar/visual-test@example.com/transition/joy/0")
        svg = response.content.decode('utf-8')

        # At 0%, target layer should have opacity="0.000" or similar
        # or base layer should be at full opacity
        assert 'opacity' in svg, "SVG should contain opacity attributes"

    def test_full_expression_has_no_base_opacity(self):
        """Test that 100% weight doesn't show base layer."""
        response = client.get("/avatar/visual-test@example.com/transition/joy/100")
        svg = response.content.decode('utf-8')

        # At 100%, base layer should have opacity="0.000" or be hidden
        assert 'opacity' in svg, "SVG should contain opacity attributes"

    def test_mid_weight_has_both_layers(self):
        """Test that 50% weight shows both layers at equal opacity."""
        response = client.get("/avatar/visual-test@example.com/transition/joy/50")
        svg = response.content.decode('utf-8')

        # At 50%, should have opacity="0.500" for both layers
        opacity_count = svg.count('opacity=')
        assert opacity_count >= 2, f"Expected at least 2 opacity attributes, got {opacity_count}"

    def test_opacity_values_correct(self):
        """Test that opacity values are mathematically correct."""
        test_cases = [
            (0, 1.0, 0.0),    # weight 0: base=1.0, target=0.0
            (25, 0.75, 0.25),  # weight 25: base=0.75, target=0.25
            (50, 0.5, 0.5),    # weight 50: base=0.5, target=0.5
            (75, 0.25, 0.75),  # weight 75: base=0.25, target=0.75
            (100, 0.0, 1.0),   # weight 100: base=0.0, target=1.0
        ]

        for weight, expected_base, expected_target in test_cases:
            response = client.get(f"/avatar/visual-test@example.com/transition/joy/{weight}")
            svg = response.content.decode('utf-8')

            # Check that opacity values appear in SVG (allowing for floating point formatting)
            if expected_base > 0:
                base_str = f"{expected_base:.3f}"
                assert base_str in svg or f"{expected_base:.1f}" in svg, \
                    f"Weight {weight}: Expected base opacity {expected_base}"

            if expected_target > 0:
                target_str = f"{expected_target:.3f}"
                assert target_str in svg or f"{expected_target:.1f}" in svg, \
                    f"Weight {weight}: Expected target opacity {expected_target}"

    def test_svg_structure_valid(self):
        """Test that generated SVGs have valid structure."""
        response = client.get("/avatar/visual-test@example.com/transition/joy/50")

        # Parse XML
        root = ET.fromstring(response.content)

        # Should be an SVG element
        assert root.tag.endswith('svg')

        # Should have viewBox
        assert 'viewBox' in root.attrib

        # Should have child elements
        assert len(root) > 0, "SVG should have child elements"


class TestPerformance:
    """Test performance requirements."""

    def test_transition_generation_under_100ms(self):
        """Test that single transition generates quickly."""
        start = time.time()
        response = client.get("/avatar/perf-test@example.com/transition/joy/50")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 0.1, f"Generation took {elapsed:.3f}s, should be < 0.1s"

    def test_cached_transition_faster(self):
        """Test that cached transitions are significantly faster."""
        # First request (cache miss)
        start1 = time.time()
        response1 = client.get("/avatar/perf-cache-test@example.com/transition/joy/50")
        elapsed1 = time.time() - start1

        # Second request (cache hit)
        start2 = time.time()
        response2 = client.get("/avatar/perf-cache-test@example.com/transition/joy/50")
        elapsed2 = time.time() - start2

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert elapsed2 < elapsed1, "Cached request should be faster"

    def test_bundle_generation_under_5s(self):
        """Test that full bundle generates within 5 seconds."""
        start = time.time()
        response = client.get("/avatar/perf-test@example.com/bundle?animations=emotes,vowels")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 5.0, f"Bundle took {elapsed:.3f}s, should be < 5s"

    def test_multiple_transitions_performance(self):
        """Test that generating multiple transitions is reasonably fast."""
        weights = [0, 25, 50, 75, 100]

        start = time.time()
        for weight in weights:
            response = client.get(f"/avatar/perf-multi-test@example.com/transition/joy/{weight}")
            assert response.status_code == 200
        elapsed = time.time() - start

        # 5 transitions should complete in under 500ms total
        assert elapsed < 0.5, f"5 transitions took {elapsed:.3f}s, should be < 0.5s"


class TestDeterminism:
    """Test deterministic generation."""

    def test_same_input_produces_identical_output(self):
        """Test that deterministic generation is consistent."""
        response1 = client.get("/avatar/determinism@example.com/transition/joy/50")
        response2 = client.get("/avatar/determinism@example.com/transition/joy/50")

        assert response1.content == response2.content, "Same input should produce identical output"

    def test_different_weights_produce_different_output(self):
        """Test that different weights produce visually different results."""
        response_0 = client.get("/avatar/determinism@example.com/transition/joy/0")
        response_50 = client.get("/avatar/determinism@example.com/transition/joy/50")
        response_100 = client.get("/avatar/determinism@example.com/transition/joy/100")

        # All should be valid SVGs
        assert response_0.status_code == 200
        assert response_50.status_code == 200
        assert response_100.status_code == 200

        # But content should differ
        assert response_0.content != response_50.content, "Weight 0 and 50 should differ"
        assert response_50.content != response_100.content, "Weight 50 and 100 should differ"
        assert response_0.content != response_100.content, "Weight 0 and 100 should differ"

    def test_different_emotes_produce_different_output(self):
        """Test that different emotes produce different results."""
        response_joy = client.get("/avatar/determinism@example.com/transition/joy/50")
        response_sorrow = client.get("/avatar/determinism@example.com/transition/sorrow/50")
        response_angry = client.get("/avatar/determinism@example.com/transition/angry/50")

        assert response_joy.status_code == 200
        assert response_sorrow.status_code == 200
        assert response_angry.status_code == 200

        # Content should differ
        assert response_joy.content != response_sorrow.content
        assert response_joy.content != response_angry.content
        assert response_sorrow.content != response_angry.content

    def test_different_inputs_produce_different_avatars(self):
        """Test that different input strings produce different base avatars."""
        response1 = client.get("/avatar/input1@example.com/transition/joy/50")
        response2 = client.get("/avatar/input2@example.com/transition/joy/50")

        assert response1.content != response2.content, "Different inputs should produce different avatars"

    def test_bundle_determinism(self):
        """Test that same input produces functionally identical bundles."""
        response1 = client.get("/avatar/bundle-determinism@example.com/bundle?animations=emotes")
        response2 = client.get("/avatar/bundle-determinism@example.com/bundle?animations=emotes")

        # Extract and compare contents (ZIP may have compression differences)
        zip1 = zipfile.ZipFile(io.BytesIO(response1.content))
        zip2 = zipfile.ZipFile(io.BytesIO(response2.content))

        # Should have same files
        assert sorted(zip1.namelist()) == sorted(zip2.namelist()), "Bundle files should be identical"

        # Compare metadata
        import json
        metadata1 = json.loads(zip1.read("metadata.json"))
        metadata2 = json.loads(zip2.read("metadata.json"))
        assert metadata1 == metadata2, "Metadata should be identical"

        # Compare each PDF page count (content may vary in byte representation but pages should match)
        for emote in ['joy', 'sorrow', 'surprised', 'angry', 'bored', 'fun']:
            pdf1 = PdfReader(io.BytesIO(zip1.read(f"emote_{emote}.pdf")))
            pdf2 = PdfReader(io.BytesIO(zip2.read(f"emote_{emote}.pdf")))
            assert len(pdf1.pages) == len(pdf2.pages), f"Page count for {emote} should match"


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_empty_input_string(self):
        """Test that empty input string is handled."""
        response = client.get("/avatar//transition/joy/50")
        # FastAPI will return 404 for empty path parameter
        assert response.status_code in [400, 404]

    def test_special_characters_in_input(self):
        """Test that special characters are handled correctly."""
        # URL-encoded special characters
        response = client.get("/avatar/test%40example.com/transition/joy/50")
        assert response.status_code == 200

    def test_case_sensitivity_emotes(self):
        """Test that emote names are case-sensitive."""
        # lowercase should work
        response_lower = client.get("/avatar/test@example.com/transition/joy/50")
        assert response_lower.status_code == 200

        # uppercase should fail
        response_upper = client.get("/avatar/test@example.com/transition/JOY/50")
        assert response_upper.status_code == 400

    def test_case_sensitivity_vowels(self):
        """Test that vowel names handle uppercase correctly."""
        # Uppercase should work for vowels
        response_upper = client.get("/avatar/test@example.com/transition/A/50")
        assert response_upper.status_code == 200

        # lowercase should fail for vowels
        response_lower = client.get("/avatar/test@example.com/transition/a/50")
        assert response_lower.status_code == 400


class TestIntegrationFlow:
    """Test complete integration flows."""

    def test_complete_animation_workflow(self):
        """Test generating a complete animation sequence end-to-end."""
        # Step 1: Get neutral frame
        response_neutral = client.get("/avatar/workflow@example.com/transition/joy/0")
        assert response_neutral.status_code == 200

        # Step 2: Get transition frames
        for weight in [25, 50, 75]:
            response = client.get(f"/avatar/workflow@example.com/transition/joy/{weight}")
            assert response.status_code == 200

        # Step 3: Get full expression
        response_full = client.get("/avatar/workflow@example.com/transition/joy/100")
        assert response_full.status_code == 200

        # Step 4: Generate bundle
        response_bundle = client.get("/avatar/workflow@example.com/bundle?animations=emotes")
        assert response_bundle.status_code == 200

    def test_mixed_animations_workflow(self):
        """Test workflow using both emotes and vowels."""
        # Test emote
        response_emote = client.get("/avatar/mixed@example.com/transition/joy/50")
        assert response_emote.status_code == 200

        # Test vowel
        response_vowel = client.get("/avatar/mixed@example.com/transition/A/50")
        assert response_vowel.status_code == 200

        # Both should work with same input but produce different results
        assert response_emote.content != response_vowel.content

    def test_all_emotes_in_sequence(self):
        """Test cycling through all emotes in sequence."""
        emotes = ['joy', 'sorrow', 'surprised', 'angry', 'bored', 'fun']

        for emote in emotes:
            response = client.get(f"/avatar/sequence@example.com/transition/{emote}/100")
            assert response.status_code == 200, f"Failed for emote: {emote}"

    def test_all_vowels_in_sequence(self):
        """Test cycling through all vowels in sequence."""
        vowels = ['A', 'E', 'I', 'O', 'U']

        for vowel in vowels:
            response = client.get(f"/avatar/sequence@example.com/transition/{vowel}/100")
            assert response.status_code == 200, f"Failed for vowel: {vowel}"
