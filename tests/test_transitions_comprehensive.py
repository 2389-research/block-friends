"""
Comprehensive avatar transitions system tests.

Tests transition caching, API endpoints, determinism, and edge cases.
"""

import pytest
from fastapi.testclient import TestClient
from app import app
from door_agents import DoorAgentGenerator, DoorAgentConfig
import hashlib
from pathlib import Path

client = TestClient(app)
config = DoorAgentConfig()
generator = DoorAgentGenerator(config)


class TestTransitionAPICaching:
    """Tests for transition generation and caching via API."""

    def test_transition_api_endpoint_success(self):
        """Transition API endpoint returns valid SVG."""
        response = client.get("/avatar/test@example.com/transition/happy/50")

        assert response.status_code == 200
        assert "image/svg+xml" in response.headers["content-type"]
        svg_content = response.content.decode('utf-8')
        assert '<svg' in svg_content
        assert '<g id="base-layer"' in svg_content
        assert '<g id="emote-layer"' in svg_content

    def test_transition_cache_hit(self):
        """Repeated transition requests hit cache."""
        # First request
        response1 = client.get("/avatar/cachetest@example.com/transition/happy/50")
        assert response1.status_code == 200

        # Second request should hit cache (same content)
        response2 = client.get("/avatar/cachetest@example.com/transition/happy/50")
        assert response2.status_code == 200

        # Content should be identical
        assert response1.content == response2.content

    def test_transition_cache_key_includes_emote(self):
        """Different emotes generate different cache entries."""
        response1 = client.get("/avatar/test@example.com/transition/happy/50")
        response2 = client.get("/avatar/test@example.com/transition/sad/50")

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Different emotes should produce different content
        assert response1.content != response2.content

    def test_transition_cache_key_includes_weight(self):
        """Different weights generate different cache entries."""
        response1 = client.get("/avatar/test@example.com/transition/happy/25")
        response2 = client.get("/avatar/test@example.com/transition/happy/75")

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Different weights should produce different content (different opacities)
        assert response1.content != response2.content

        # Check opacity values
        svg1 = response1.content.decode('utf-8')
        svg2 = response2.content.decode('utf-8')

        # Weight 25 should have lower emote opacity than weight 75
        assert 'opacity="0.25"' in svg1
        assert 'opacity="0.75"' in svg2

    def test_transition_cache_file_created(self):
        """Transition cache files are created in correct location."""
        input_string = "filecachetest@example.com"
        emote = "happy"
        weight = 50

        # Make request
        response = client.get(f"/avatar/{input_string}/transition/{emote}/{weight}")
        assert response.status_code == 200

        # Check cache file exists
        hash_hex = hashlib.sha256(input_string.encode('utf-8')).hexdigest()[:16]
        cache_key = f"{hash_hex}_transition_{emote}_{weight}"
        cache_path = Path("out/avatar") / f"{cache_key}.svg"

        assert cache_path.exists(), f"Cache file not found at {cache_path}"


class TestTransitionWeightValidation:
    """Tests for weight parameter validation."""

    def test_transition_weight_0(self):
        """Weight 0 shows only base layer."""
        response = client.get("/avatar/test@example.com/transition/happy/0")

        assert response.status_code == 200
        svg_content = response.content.decode('utf-8')

        # Base at 100%, emote at 0%
        assert 'opacity="1.0"' in svg_content
        assert 'opacity="0.0"' in svg_content

    def test_transition_weight_100(self):
        """Weight 100 shows full emote overlay."""
        response = client.get("/avatar/test@example.com/transition/happy/100")

        assert response.status_code == 200
        svg_content = response.content.decode('utf-8')

        # Both at 100% (emote fully overlays base)
        assert '<g id="base-layer" opacity="1.0">' in svg_content
        assert '<g id="emote-layer" opacity="1.0">' in svg_content

    def test_transition_weight_midpoint(self):
        """Weight 50 shows equal blend."""
        response = client.get("/avatar/test@example.com/transition/happy/50")

        assert response.status_code == 200
        svg_content = response.content.decode('utf-8')

        # Base at 100%, emote at 50%
        assert '<g id="base-layer" opacity="1.0">' in svg_content
        assert '<g id="emote-layer" opacity="0.5">' in svg_content

    def test_transition_invalid_weight_negative(self):
        """Negative weight returns error."""
        response = client.get("/avatar/test@example.com/transition/happy/-10")

        # Should return 400 or 422 validation error
        assert response.status_code in [400, 422, 500]

    def test_transition_invalid_weight_over_100(self):
        """Weight > 100 returns error."""
        response = client.get("/avatar/test@example.com/transition/happy/150")

        # Should return 400 or 422 validation error
        assert response.status_code in [400, 422, 500]

    def test_transition_invalid_weight_non_numeric(self):
        """Non-numeric weight returns error."""
        response = client.get("/avatar/test@example.com/transition/happy/abc")

        # Should return 422 validation error
        assert response.status_code in [400, 422]


class TestTransitionEmoteValidation:
    """Tests for emote parameter validation."""

    def test_transition_all_valid_emotes(self):
        """All valid emotes work correctly."""
        emotes = ["happy", "sad", "surprised", "angry", "bored"]

        for emote in emotes:
            response = client.get(f"/avatar/test@example.com/transition/{emote}/50")
            assert response.status_code == 200, f"Emote {emote} failed"
            svg_content = response.content.decode('utf-8')
            assert '<g id="emote-layer"' in svg_content

    def test_transition_all_valid_vowels(self):
        """All valid vowels work correctly."""
        vowels = ["vowel_a", "vowel_e", "vowel_i", "vowel_o", "vowel_u"]

        for vowel in vowels:
            response = client.get(f"/avatar/test@example.com/transition/{vowel}/50")
            assert response.status_code == 200, f"Vowel {vowel} failed"

    def test_transition_invalid_emote_name(self):
        """Invalid emote name returns error."""
        response = client.get("/avatar/test@example.com/transition/invalid_emote/50")

        # Should return 400 or 500 error
        assert response.status_code in [400, 500]

    def test_transition_malformed_emote_name(self):
        """Malformed emote name returns error."""
        response = client.get("/avatar/test@example.com/transition/happy_sad/50")

        # Should return error (not a valid emote)
        assert response.status_code in [400, 500]

    def test_transition_empty_emote_name(self):
        """Empty emote name returns error."""
        response = client.get("/avatar/test@example.com/transition//50")

        # Should return 404 or 422 error
        assert response.status_code in [404, 422]


class TestTransitionInputValidation:
    """Tests for input string validation in transitions."""

    def test_transition_with_empty_input(self):
        """Transition with empty input string."""
        response = client.get("/avatar//transition/happy/50")

        # Should handle gracefully
        assert response.status_code in [200, 404, 422]

    def test_transition_with_unicode_input(self):
        """Transition with Unicode characters."""
        response = client.get("/avatar/测试@example.com/transition/happy/50")

        # Should work (hash handles any UTF-8)
        assert response.status_code == 200

    def test_transition_with_special_characters(self):
        """Transition with special characters in input."""
        response = client.get("/avatar/test+user@example.com/transition/happy/50")

        # Should work
        assert response.status_code == 200


class TestTransitionDeterminism:
    """Tests for deterministic transition generation."""

    def test_transition_deterministic_generation(self):
        """Same input produces same transition."""
        response1 = client.get("/avatar/deterministic@example.com/transition/happy/50")
        response2 = client.get("/avatar/deterministic@example.com/transition/happy/50")

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.content == response2.content

    def test_transition_deterministic_different_weights(self):
        """Different weights produce different but deterministic results."""
        input_string = "weighttest@example.com"

        # Get transitions at different weights
        weights = [0, 25, 50, 75, 100]
        results = []

        for weight in weights:
            response = client.get(f"/avatar/{input_string}/transition/happy/{weight}")
            assert response.status_code == 200
            results.append(response.content)

        # All should be different (except possibly 0 and 100 edge cases)
        unique_results = set(results)
        assert len(unique_results) >= 4, "Different weights should produce different results"

        # Requesting again should give same results
        for i, weight in enumerate(weights):
            response = client.get(f"/avatar/{input_string}/transition/happy/{weight}")
            assert response.status_code == 200
            assert response.content == results[i], f"Weight {weight} not deterministic"


class TestTransitionSVGStructure:
    """Tests for transition SVG structure and validity."""

    def test_transition_svg_contains_both_layers(self):
        """Transition SVG contains both base and emote layers."""
        response = client.get("/avatar/test@example.com/transition/happy/50")

        assert response.status_code == 200
        svg_content = response.content.decode('utf-8')

        # Check structure
        assert '<svg' in svg_content
        assert '<g id="base-layer"' in svg_content
        assert '<g id="emote-layer"' in svg_content
        assert 'opacity=' in svg_content

    def test_transition_svg_valid_xmlns(self):
        """Transition SVG has valid XML namespace."""
        response = client.get("/avatar/test@example.com/transition/happy/50")

        assert response.status_code == 200
        svg_content = response.content.decode('utf-8')

        assert 'xmlns="http://www.w3.org/2000/svg"' in svg_content

    def test_transition_svg_has_viewbox(self):
        """Transition SVG has viewBox attribute."""
        response = client.get("/avatar/test@example.com/transition/happy/50")

        assert response.status_code == 200
        svg_content = response.content.decode('utf-8')

        assert 'viewBox=' in svg_content or 'viewbox=' in svg_content.lower()

    def test_transition_opacity_calculation(self):
        """Transition opacity values are correctly calculated."""
        test_cases = [
            (0, "0.0"),
            (25, "0.25"),
            (50, "0.5"),
            (75, "0.75"),
            (100, "1.0"),
        ]

        for weight, expected_emote_opacity in test_cases:
            response = client.get(f"/avatar/test@example.com/transition/happy/{weight}")
            assert response.status_code == 200

            svg_content = response.content.decode('utf-8')
            # Check that emote layer has correct opacity
            assert f'opacity="{expected_emote_opacity}"' in svg_content, \
                f"Weight {weight} should produce emote opacity {expected_emote_opacity}"


class TestTransitionPerformance:
    """Tests for transition generation performance."""

    def test_transition_generation_reasonable_time(self):
        """Transition generation completes in reasonable time."""
        import time

        start_time = time.time()
        response = client.get("/avatar/performance@example.com/transition/happy/50")
        elapsed_time = time.time() - start_time

        assert response.status_code == 200
        # Should complete in less than 5 seconds (first generation)
        assert elapsed_time < 5.0, f"Transition took {elapsed_time}s, expected < 5s"

    def test_transition_cached_request_fast(self):
        """Cached transition requests are fast."""
        import time

        # First request (cache miss)
        client.get("/avatar/fastcache@example.com/transition/happy/50")

        # Second request (cache hit) should be very fast
        start_time = time.time()
        response = client.get("/avatar/fastcache@example.com/transition/happy/50")
        elapsed_time = time.time() - start_time

        assert response.status_code == 200
        # Cached request should complete in less than 1 second
        assert elapsed_time < 1.0, f"Cached transition took {elapsed_time}s, expected < 1s"
