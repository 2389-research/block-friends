# ABOUTME: Tests for CSS rules generation in universal SVG mode
# ABOUTME: Validates scoped CSS for state visibility control across all animation frames

import pytest
from door_agents import DoorAgentGenerator, DoorAgentConfig

def test_css_rules_hide_all_by_default():
    """CSS should hide all eyes/mouths by default."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    avatar_id = "avatar-test123"
    css = generator._generate_css_rules(avatar_id)

    assert f'#{avatar_id} .eyes > g, #{avatar_id} .mouths > g {{ display: none; }}' in css

def test_css_rules_for_neutral():
    """CSS should include rule for neutral/default state."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    avatar_id = "avatar-test123"
    css = generator._generate_css_rules(avatar_id)

    # Check neutral rule (open eyes, closed mouth)
    assert f'#{avatar_id}.neutral .eyes > .open' in css
    assert f'#{avatar_id}.neutral .mouths > .closed' in css

def test_css_rules_for_idle_frames():
    """CSS should include rules for all 10 idle frames."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    avatar_id = "avatar-test123"
    css = generator._generate_css_rules(avatar_id)

    # Check idle_0 rule
    assert f'#{avatar_id}.idle_0 .eyes > .open' in css
    assert f'#{avatar_id}.idle_0 .mouths > .closed' in css

    # Check idle_2 rule (closed eyes)
    assert f'#{avatar_id}.idle_2 .eyes > .closed' in css

def test_css_rules_for_emotes():
    """CSS should include rules for all 5 emotes."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    avatar_id = "avatar-test123"
    css = generator._generate_css_rules(avatar_id)

    for emote in ['happy', 'sad', 'surprised', 'angry', 'bored']:
        assert f'#{avatar_id}.{emote} .eyes > .{emote}' in css
        assert f'#{avatar_id}.{emote} .mouths > .{emote}' in css

def test_css_rules_for_vowels():
    """CSS should include rules for all 5 vowels."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    avatar_id = "avatar-test123"
    css = generator._generate_css_rules(avatar_id)

    for vowel in ['a', 'e', 'i', 'o', 'u']:
        assert f'#{avatar_id}.vowel_{vowel} .eyes > .open' in css
        assert f'#{avatar_id}.vowel_{vowel} .mouths > .vowel_{vowel}' in css
