#!/usr/bin/env python3
# ABOUTME: Tests for avatar transition generation
# ABOUTME: Covers opacity-based blending between base and emote avatars

import pytest
from door_agents import DoorAgentConfig, DoorAgentGenerator


def test_generate_transition_basic():
    """Test basic transition generation between neutral and emote."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    svg_content = generator.generate_transition("test@example.com", "happy", 50)

    # Verify SVG structure
    assert svg_content.startswith('<svg')
    assert 'xmlns="http://www.w3.org/2000/svg"' in svg_content

    # Verify both base and emote layers are present with opacity
    assert '<g id="base-layer" opacity="0.5">' in svg_content
    assert '<g id="emote-layer" opacity="0.5">' in svg_content


def test_generate_transition_weight_extremes():
    """Test transition at weight extremes (0 and 100)."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    # Weight 0 = 100% base, 0% emote
    svg_0 = generator.generate_transition("test@example.com", "happy", 0)
    assert '<g id="base-layer" opacity="1.0">' in svg_0
    assert '<g id="emote-layer" opacity="0.0">' in svg_0

    # Weight 100 = 0% base, 100% emote
    svg_100 = generator.generate_transition("test@example.com", "happy", 100)
    assert '<g id="base-layer" opacity="0.0">' in svg_100
    assert '<g id="emote-layer" opacity="1.0">' in svg_100


def test_generate_transition_all_emotes():
    """Test transition generation for all available emotes."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    emotes = ["happy", "sad", "surprised", "angry", "bored"]
    for emote in emotes:
        svg_content = generator.generate_transition("test@example.com", emote, 50)
        assert svg_content.startswith('<svg')
        assert '<g id="base-layer"' in svg_content
        assert '<g id="emote-layer"' in svg_content


def test_generate_transition_vowels():
    """Test transition generation for vowel lip-sync."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    vowels = ["vowel_a", "vowel_e", "vowel_i", "vowel_o", "vowel_u"]
    for vowel in vowels:
        svg_content = generator.generate_transition("test@example.com", vowel, 50)
        assert svg_content.startswith('<svg')
        assert '<g id="base-layer"' in svg_content
        assert '<g id="emote-layer"' in svg_content


def test_generate_transition_deterministic():
    """Test that transitions are deterministic for same input."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    svg1 = generator.generate_transition("test@example.com", "happy", 50)
    svg2 = generator.generate_transition("test@example.com", "happy", 50)

    assert svg1 == svg2


def test_generate_transition_invalid_emote():
    """Test that invalid emote raises ValueError."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    with pytest.raises(ValueError, match="Unknown emote"):
        generator.generate_transition("test@example.com", "invalid_emote", 50)


def test_generate_transition_weight_bounds():
    """Test that weight out of bounds raises ValueError."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    with pytest.raises(ValueError, match="Weight must be between 0 and 100"):
        generator.generate_transition("test@example.com", "happy", -1)

    with pytest.raises(ValueError, match="Weight must be between 0 and 100"):
        generator.generate_transition("test@example.com", "happy", 101)
