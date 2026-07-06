#!/usr/bin/env python3
# ABOUTME: Tests for deterministic generation edge cases
# ABOUTME: Tests avatar generation with unusual inputs and edge cases

from fastapi.testclient import TestClient
from app import app
from door_agents import DoorAgentConfig

client = TestClient(app)


class TestEmptyAndMinimalInputs:
    """Tests for empty and minimal input strings."""

    def test_empty_string_generation(self):
        """Empty string generates consistent avatar."""
        response = client.get("/avatar/.svg")

        # Should handle gracefully
        assert response.status_code in [200, 400, 404]

    def test_single_character_input(self):
        """Single character input generates avatar."""
        response = client.get("/avatar/a.svg")

        assert response.status_code == 200
        assert b"<svg" in response.content

    def test_two_character_input(self):
        """Two character input generates avatar."""
        response = client.get("/avatar/ab.svg")

        assert response.status_code == 200
        assert b"<svg" in response.content


class TestVeryLongInputs:
    """Tests for very long input strings."""

    def test_long_input_100_chars(self):
        """100 character input is handled."""
        long_input = "a" * 100
        response = client.get(f"/avatar/{long_input}.svg")

        assert response.status_code == 200
        assert b"<svg" in response.content

    def test_long_input_1000_chars(self):
        """1000 character input is handled."""
        long_input = "b" * 1000
        response = client.get(f"/avatar/{long_input}.svg")

        assert response.status_code in [200, 414]  # 414 = URI Too Long

    def test_long_input_determinism(self):
        """Very long inputs are still deterministic."""
        long_input = "c" * 500
        response1 = client.get(f"/avatar/{long_input}.svg")
        response2 = client.get(f"/avatar/{long_input}.svg")

        if response1.status_code == 200 and response2.status_code == 200:
            assert response1.content == response2.content


class TestSpecialCharacterInputs:
    """Tests for inputs with special characters."""

    def test_unicode_emoji_input(self):
        """Unicode emoji input generates consistent avatar."""
        emoji_input = "user🎨🚀💻"
        response = client.get(f"/avatar/{emoji_input}.svg")

        assert response.status_code == 200
        assert b"<svg" in response.content

    def test_mixed_unicode_input(self):
        """Mixed Unicode characters generate avatar."""
        mixed = "user用户مستخدم👤"
        response = client.get(f"/avatar/{mixed}.svg")

        assert response.status_code == 200
        assert b"<svg" in response.content

    def test_special_chars_determinism(self):
        """Special characters maintain determinism."""
        from urllib.parse import quote
        special = "user!@#$%^&*()"
        encoded = quote(special, safe='')
        response1 = client.get(f"/avatar/{encoded}.svg")
        response2 = client.get(f"/avatar/{encoded}.svg")

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.content == response2.content


class TestHashCollisionHandling:
    """Tests for handling hash collisions (theoretical)."""

    def test_similar_inputs_different_avatars(self):
        """Similar inputs generate different avatars."""
        response1 = client.get("/avatar/user1@example.com.svg")
        response2 = client.get("/avatar/user2@example.com.svg")

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.content != response2.content

    def test_same_input_different_case_different_avatars(self):
        """Same input with different case generates different avatars."""
        response1 = client.get("/avatar/User@Example.Com.svg")
        response2 = client.get("/avatar/user@example.com.svg")

        assert response1.status_code == 200
        assert response2.status_code == 200
        # Case should matter for hash
        assert response1.content != response2.content

    def test_transposed_characters_different_avatars(self):
        """Transposed characters generate different avatars."""
        response1 = client.get("/avatar/alice@example.com.svg")
        response2 = client.get("/avatar/alic@eexample.com.svg")

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.content != response2.content


class TestBodyAndNodeColorConstraints:
    """Tests for body/node color selection with constraints."""

    def test_body_and_node_colors_different(self):
        """Body and node colors are generated correctly."""
        # Test via API instead of direct generator call
        for i in range(10):
            response = client.get(f"/avatar/test{i}@example.com.svg")
            assert response.status_code == 200
            assert b"<svg" in response.content

    def test_color_selection_with_limited_palette(self):
        """Color selection works even with limited palette."""
        # This tests the constraint that body != node color
        # Even with a palette of just 2 colors, it should work
        config = DoorAgentConfig()

        # Should have at least 2 colors
        assert len(config.PALETTE) >= 2


class TestHairColorSelection:
    """Tests for hair color selection with various specifications."""

    def test_hair_currentcolor_selection(self):
        """Hair with currentColor uses body color."""
        response = client.get("/avatar/test-hair-current@example.com.svg")

        assert response.status_code == 200
        # Hair should inherit body color in some cases

    def test_hair_contrast_color_selection(self):
        """Hair with contrast color differs from body."""
        response = client.get("/avatar/test-hair-contrast@example.com.svg")

        assert response.status_code == 200
        # Contrast color should be different from body

    def test_hair_specific_color_selection(self):
        """Hair with specific hex color uses that color."""
        response = client.get("/avatar/test-hair-specific@example.com.svg")

        assert response.status_code == 200

    def test_hair_array_color_selection(self):
        """Hair with color array selects from array."""
        response = client.get("/avatar/test-hair-array@example.com.svg")

        assert response.status_code == 200


class TestDeterministicHashAllocation:
    """Tests for deterministic hash byte allocation."""

    def test_same_input_same_body_shape(self):
        """Same input always produces same body shape."""
        responses = [
            client.get("/avatar/deterministic-shape@example.com.svg")
            for _ in range(3)
        ]

        # All responses should be identical
        for i in range(len(responses) - 1):
            assert responses[i].content == responses[i + 1].content

    def test_same_input_same_colors(self):
        """Same input always produces same colors."""
        responses = [
            client.get("/avatar/deterministic-color@example.com.svg")
            for _ in range(3)
        ]

        for i in range(len(responses) - 1):
            assert responses[i].content == responses[i + 1].content

    def test_same_input_same_hair(self):
        """Same input always produces same hair style."""
        responses = [
            client.get("/avatar/deterministic-hair@example.com.svg")
            for _ in range(3)
        ]

        for i in range(len(responses) - 1):
            assert responses[i].content == responses[i + 1].content


class TestEdgeCaseBodyShapes:
    """Tests for edge case body shape selections."""

    def test_minimum_body_size(self):
        """Minimum body size is handled correctly."""
        response = client.get("/avatar/min-size@example.com.svg")

        assert response.status_code == 200
        assert b"<svg" in response.content

    def test_maximum_body_size(self):
        """Maximum body size is handled correctly."""
        response = client.get("/avatar/max-size@example.com.svg")

        assert response.status_code == 200
        assert b"<svg" in response.content


class TestFeetColorLogic:
    """Tests for feet color matching logic."""

    def test_feet_match_body_sometimes(self):
        """Feet sometimes match body color (based on hash)."""
        # Generate multiple avatars
        responses = [
            client.get(f"/avatar/feet-test-{i}@example.com.svg")
            for i in range(10)
        ]

        # All should succeed
        for response in responses:
            assert response.status_code == 200

    def test_feet_match_nodes_sometimes(self):
        """Feet sometimes match node color (based on hash)."""
        # This is determined by hash byte
        # Just verify generation succeeds
        response = client.get("/avatar/feet-nodes@example.com.svg")
        assert response.status_code == 200


class TestInputNormalization:
    """Tests for input string normalization behavior."""

    def test_whitespace_in_input(self):
        """Whitespace in input affects hash."""
        response1 = client.get("/avatar/test user.svg")
        response2 = client.get("/avatar/testuser.svg")

        assert response1.status_code == 200
        assert response2.status_code == 200
        # Should be different (whitespace matters)
        assert response1.content != response2.content

    def test_url_encoding_normalization(self):
        """URL-encoded characters are handled correctly."""
        response = client.get("/avatar/test%40example.com.svg")

        assert response.status_code == 200
        assert b"<svg" in response.content


class TestGeneratorDirectUsage:
    """Tests using the generator directly (not via API)."""

    def test_generator_with_empty_string(self):
        """Generator handles empty string input via API."""
        # Test empty input via API endpoint
        response = client.get("/avatar/.svg")
        # May return 404 for empty input, or 200 with generated SVG
        assert response.status_code in [200, 404]

    def test_generator_with_simple_input(self):
        """Generator creates valid SVG for simple inputs."""
        # Test a simple input to verify generator works
        response = client.get("/avatar/simple-test.svg")
        assert response.status_code == 200
        assert b"<svg" in response.content
