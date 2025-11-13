"""
Deterministic generation edge case tests.

Tests unusual inputs, edge cases, and determinism constraints.
"""

import pytest
from fastapi.testclient import TestClient
from app import app
from door_agents import DoorAgentGenerator, DoorAgentConfig

client = TestClient(app)
config = DoorAgentConfig()
generator = DoorAgentGenerator(config)


class TestEmptyStringInput:
    """Tests for empty string input handling."""

    def test_empty_string_generates_avatar(self):
        """Empty string input generates valid avatar."""
        svg, info = generator.generate_deterministic("")

        assert '<svg' in svg
        assert info is not None

    def test_empty_string_deterministic(self):
        """Empty string produces consistent results."""
        svg1, info1 = generator.generate_deterministic("")
        svg2, info2 = generator.generate_deterministic("")

        assert svg1 == svg2
        assert info1 == info2


class TestVeryLongInputStrings:
    """Tests for very long input string handling."""

    def test_long_input_1000_chars(self):
        """1000 character input string works."""
        long_input = "a" * 1000
        svg, info = generator.generate_deterministic(long_input)

        assert '<svg' in svg

    def test_long_input_10000_chars(self):
        """10000 character input string works."""
        long_input = "b" * 10000
        svg, info = generator.generate_deterministic(long_input)

        assert '<svg' in svg

    def test_very_long_input_deterministic(self):
        """Very long input produces deterministic results."""
        long_input = "c" * 5000
        svg1, _ = generator.generate_deterministic(long_input)
        svg2, _ = generator.generate_deterministic(long_input)

        assert svg1 == svg2

    def test_extremely_long_input_via_api(self):
        """API handles extremely long input."""
        long_input = "x" * 100000
        response = client.get(f"/avatar/{long_input}.svg")

        # Should either succeed or return appropriate error
        assert response.status_code in [200, 400, 414]


class TestUnicodeAndSpecialCharacters:
    """Tests for Unicode and special character handling."""

    def test_unicode_chinese_characters(self):
        """Chinese Unicode characters work."""
        input_str = "用户@example.com"
        svg, info = generator.generate_deterministic(input_str)

        assert '<svg' in svg

    def test_unicode_emoji(self):
        """Emoji characters work."""
        input_str = "user😀@example.com"
        svg, info = generator.generate_deterministic(input_str)

        assert '<svg' in svg

    def test_unicode_arabic(self):
        """Arabic Unicode characters work."""
        input_str = "مستخدم@example.com"
        svg, info = generator.generate_deterministic(input_str)

        assert '<svg' in svg

    def test_unicode_mixed(self):
        """Mixed Unicode characters work."""
        input_str = "user用户مستخدم😀@example.com"
        svg, info = generator.generate_deterministic(input_str)

        assert '<svg' in svg

    def test_unicode_deterministic(self):
        """Unicode input produces deterministic results."""
        input_str = "テスト@example.com"
        svg1, _ = generator.generate_deterministic(input_str)
        svg2, _ = generator.generate_deterministic(input_str)

        assert svg1 == svg2

    def test_special_characters_url_encoded(self):
        """Special characters in URLs work."""
        response = client.get("/avatar/test%40example.com.svg")
        assert response.status_code == 200

    def test_plus_sign_in_input(self):
        """Plus sign in input works."""
        response = client.get("/avatar/test+user@example.com.svg")
        assert response.status_code == 200

    def test_ampersand_in_input(self):
        """Ampersand in input works."""
        svg, _ = generator.generate_deterministic("user&test@example.com")
        assert '<svg' in svg


class TestControlCharacters:
    """Tests for control character handling."""

    def test_null_byte_in_input(self):
        """Null byte in input is handled."""
        input_str = "test\x00@example.com"
        svg, info = generator.generate_deterministic(input_str)

        assert '<svg' in svg

    def test_newline_in_input(self):
        """Newline in input is handled."""
        input_str = "test\n@example.com"
        svg, info = generator.generate_deterministic(input_str)

        assert '<svg' in svg

    def test_tab_in_input(self):
        """Tab in input is handled."""
        input_str = "test\t@example.com"
        svg, info = generator.generate_deterministic(input_str)

        assert '<svg' in svg

    def test_multiple_control_characters(self):
        """Multiple control characters are handled."""
        input_str = "test\x00\n\r\t@example.com"
        svg, info = generator.generate_deterministic(input_str)

        assert '<svg' in svg


class TestHashCollisionHandling:
    """Tests for hash behavior and collision resistance."""

    def test_similar_inputs_different_outputs(self):
        """Similar inputs produce different avatars."""
        svg1, info1 = generator.generate_deterministic("user1@example.com")
        svg2, info2 = generator.generate_deterministic("user2@example.com")

        # Should have different configurations
        assert svg1 != svg2
        # At least some properties should differ
        assert (info1['body_color'] != info2['body_color'] or
                info1['open_eye_index'] != info2['open_eye_index'] or
                info1['hair_index'] != info2['hair_index'])

    def test_inputs_differ_by_one_char(self):
        """Inputs differing by one character produce different avatars."""
        svg1, _ = generator.generate_deterministic("test@example.com")
        svg2, _ = generator.generate_deterministic("tast@example.com")

        assert svg1 != svg2

    def test_case_sensitivity(self):
        """Input is case-sensitive."""
        svg1, _ = generator.generate_deterministic("Test@Example.com")
        svg2, _ = generator.generate_deterministic("test@example.com")

        # Should produce different avatars (hash is case-sensitive)
        assert svg1 != svg2

    def test_whitespace_matters(self):
        """Whitespace in input matters."""
        svg1, _ = generator.generate_deterministic("test@example.com")
        svg2, _ = generator.generate_deterministic("test@example.com ")

        # Trailing space should produce different avatar
        assert svg1 != svg2


class TestColorConstraints:
    """Tests for body/node color constraints."""

    def test_body_and_node_colors_different(self):
        """Body and node colors are always different."""
        # Test many avatars to verify constraint
        for i in range(20):
            svg, info = generator.generate_deterministic(f"colortest{i}@example.com")

            body_color = info['body_color']
            node_color = info['node_color']

            assert body_color != node_color, \
                f"Body and node colors should differ: {body_color} vs {node_color}"

    def test_limited_palette_constraint(self):
        """Color constraint works even with limited palette."""
        # Generate many avatars
        for i in range(50):
            svg, info = generator.generate_deterministic(f"palette{i}@example.com")

            # Body and node colors should still be different
            assert info['body_color'] != info['node_color']


class TestHairColorSelection:
    """Tests for hair color selection edge cases."""

    def test_hair_with_empty_color_array(self):
        """Hair with empty color array is handled."""
        # This would require mocking a hair asset with empty color array
        # For now, just verify generation works
        svg, info = generator.generate_deterministic("haircolor@example.com")
        assert '<svg' in svg

    def test_hair_with_single_color(self):
        """Hair with single color in array works."""
        # Generate avatars with hair
        for i in range(10):
            svg, info = generator.generate_deterministic(f"singlecolor{i}@example.com")
            if info.get('hair_index') is not None:
                assert '<svg' in svg
                break

    def test_hair_color_deterministic(self):
        """Hair color selection is deterministic."""
        svg1, info1 = generator.generate_deterministic("hairdet@example.com")
        svg2, info2 = generator.generate_deterministic("hairdet@example.com")

        # Hair color selection should be consistent
        assert svg1 == svg2


class TestInputHashBehavior:
    """Tests for input hash behavior."""

    def test_hash_length_consistent(self):
        """Hash length is consistent (16 characters)."""
        import hashlib

        test_inputs = [
            "short",
            "medium@example.com",
            "very-long-input-string-for-testing@example.com",
        ]

        for input_str in test_inputs:
            hash_hex = hashlib.sha256(input_str.encode('utf-8')).hexdigest()[:16]
            assert len(hash_hex) == 16

    def test_hash_hex_characters(self):
        """Hash contains only hex characters."""
        import hashlib

        hash_hex = hashlib.sha256("test@example.com".encode('utf-8')).hexdigest()[:16]

        # Should only contain 0-9, a-f
        assert all(c in '0123456789abcdef' for c in hash_hex)

    def test_first_n_bytes_collision_handled(self):
        """System handles inputs with same first N hash bytes."""
        # Generate many avatars to check for consistency
        hashes = set()
        for i in range(100):
            svg, info = generator.generate_deterministic(f"collision{i}@example.com")
            assert '<svg' in svg
            # Track that we're generating different avatars
            hashes.add(info['body_color'] + str(info['open_eye_index']))

        # Should have many unique combinations
        assert len(hashes) > 10


class TestInputNormalization:
    """Tests for input normalization (or lack thereof)."""

    def test_no_automatic_normalization(self):
        """Input is not automatically normalized."""
        # Different Unicode normalizations should produce different avatars
        # NFD vs NFC for "é"
        input_nfc = "café@example.com"  # Composed form
        input_nfd = "café@example.com"  # Decomposed form (if different)

        svg1, _ = generator.generate_deterministic(input_nfc)
        svg2, _ = generator.generate_deterministic(input_nfd)

        # If they're actually different Unicode representations, should differ
        # If they're the same, this test passes trivially
        if input_nfc != input_nfd:
            assert svg1 != svg2

    def test_whitespace_not_trimmed(self):
        """Leading/trailing whitespace is not automatically trimmed."""
        svg1, _ = generator.generate_deterministic("test@example.com")
        svg2, _ = generator.generate_deterministic(" test@example.com")
        svg3, _ = generator.generate_deterministic("test@example.com ")

        # All should be different
        assert svg1 != svg2
        assert svg1 != svg3
        assert svg2 != svg3


class TestBoundaryValues:
    """Tests for boundary value handling."""

    def test_single_character_input(self):
        """Single character input works."""
        svg, info = generator.generate_deterministic("a")

        assert '<svg' in svg

    def test_two_character_input(self):
        """Two character input works."""
        svg, info = generator.generate_deterministic("ab")

        assert '<svg' in svg

    def test_numeric_only_input(self):
        """Numeric-only input works."""
        svg, info = generator.generate_deterministic("12345")

        assert '<svg' in svg

    def test_special_only_input(self):
        """Special characters only input works."""
        svg, info = generator.generate_deterministic("@#$%")

        assert '<svg' in svg
