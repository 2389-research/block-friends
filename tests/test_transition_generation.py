#!/usr/bin/env python3
import pytest
from door_agents import DoorAgentConfig, DoorAgentGenerator
import xml.etree.ElementTree as ET


def test_transition_neutral_weight():
    """Test that 0% weight returns neutral face."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    svg, metadata = generator.generate_transition("test@example.com", "joy", 0)

    # Parse SVG to verify structure
    root = ET.fromstring(svg)
    assert root.tag.endswith('svg')

    # Should have metadata indicating neutral state
    assert metadata['emote'] == 'joy'
    assert metadata['weight'] == 0
    assert metadata['is_neutral'] is True


def test_transition_full_weight():
    """Test that 100% weight returns full expression."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    svg, metadata = generator.generate_transition("test@example.com", "joy", 100)

    root = ET.fromstring(svg)
    assert root.tag.endswith('svg')

    # Should have metadata indicating full emote
    assert metadata['emote'] == 'joy'
    assert metadata['weight'] == 100
    assert metadata['is_neutral'] is False


def test_transition_mid_weight():
    """Test that 50% weight creates blended opacity."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    svg, metadata = generator.generate_transition("test@example.com", "joy", 50)

    # Check that SVG contains opacity attributes
    assert 'opacity' in svg
    assert metadata['weight'] == 50


def test_all_emotes_valid():
    """Test that all emote types generate without errors."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    emotes = ['joy', 'sorrow', 'surprised', 'angry', 'bored', 'fun']
    weights = [0, 25, 50, 75, 100]

    for emote in emotes:
        for weight in weights:
            svg, metadata = generator.generate_transition("test@example.com", emote, weight)
            assert len(svg) > 0
            assert metadata['emote'] == emote
            assert metadata['weight'] == weight


def test_all_vowels_valid():
    """Test that all vowel shapes generate without errors."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    vowels = ['A', 'E', 'I', 'O', 'U']
    weights = [0, 50, 100]

    for vowel in vowels:
        for weight in weights:
            svg, metadata = generator.generate_transition("test@example.com", vowel, weight)
            assert len(svg) > 0
            assert metadata['emote'] == vowel
            assert metadata['weight'] == weight


def test_deterministic_generation():
    """Test that same input produces same output."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    svg1, _ = generator.generate_transition("same@input.com", "joy", 50)
    svg2, _ = generator.generate_transition("same@input.com", "joy", 50)

    assert svg1 == svg2


def test_different_inputs_different_outputs():
    """Test that different inputs produce different avatars."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    svg1, _ = generator.generate_transition("input1@example.com", "joy", 50)
    svg2, _ = generator.generate_transition("input2@example.com", "joy", 50)

    # Should differ because base avatar differs
    assert svg1 != svg2
