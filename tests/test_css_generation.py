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

    # CSS uses compact format without spaces and opacity instead of display
    assert f'#{avatar_id} .eyes>g,#{avatar_id} .mouths>g{{opacity:0}}' in css

def test_css_rules_for_neutral():
    """CSS should include rule for neutral/default state."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    avatar_id = "avatar-test123"
    css = generator._generate_css_rules(avatar_id)

    # Check default rule (open eyes, closed mouth) - no class modifier for default
    assert f'#{avatar_id} .eyes>.open,#{avatar_id} .mouths>.closed{{opacity:1}}' in css

def test_css_rules_for_idle_frames():
    """CSS should include rules for all 10 idle frames."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    avatar_id = "avatar-test123"
    css = generator._generate_css_rules(avatar_id)

    # Check idle_0 rule (uses compact format)
    assert f'#{avatar_id}.idle_0 .eyes>.open,#{avatar_id}.idle_0 .mouths>.closed{{opacity:1}}' in css

    # Check idle_2 rule (closed eyes, bored mouth)
    assert f'#{avatar_id}.idle_2 .eyes>.closed,#{avatar_id}.idle_2 .mouths>.bored{{opacity:1}}' in css

def test_css_rules_for_emotes():
    """CSS should include rules for all 5 emotes."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    avatar_id = "avatar-test123"
    css = generator._generate_css_rules(avatar_id)

    for emote in ['happy', 'sad', 'surprised', 'angry', 'bored']:
        # Uses compact format: #id.emote .eyes>.emote,#id.emote .mouths>.emote{opacity:1}
        assert f'#{avatar_id}.{emote} .eyes>.{emote},#{avatar_id}.{emote} .mouths>.{emote}{{opacity:1}}' in css

def test_css_rules_for_vowels():
    """CSS should include rules for all 5 vowels."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    avatar_id = "avatar-test123"
    css = generator._generate_css_rules(avatar_id)

    for vowel in ['a', 'e', 'i', 'o', 'u']:
        # Vowels use open eyes + vowel mouth
        assert f'#{avatar_id}.vowel_{vowel} .eyes>.open,#{avatar_id}.vowel_{vowel} .mouths>.vowel_{vowel}{{opacity:1}}' in css
