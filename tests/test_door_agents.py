# ABOUTME: Test suite for door agent generation system
# ABOUTME: Covers config loading, deterministic generation, and emote system functionality
"""Tests for door agent generation system."""
import pytest
from pathlib import Path
from door_agents import DoorAgentConfig, DoorAgentGenerator


def test_config_loads_successfully():
    """Smoke test: config should load without errors."""
    config = DoorAgentConfig()
    assert config is not None
    assert config.CELL > 0
    assert len(config.PALETTE) > 0


def test_generator_creates_deterministic_avatar():
    """Smoke test: generator should create SVG from input string."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    svg_content, config_info = generator.generate_deterministic("test@example.com")

    assert svg_content is not None
    assert len(svg_content) > 0
    assert config_info["input_string"] == "test@example.com"


def test_idle_animation_frames_have_blink_and_sway():
    """Idle animation should use eye state overrides and horizontal body transforms."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    # Test all 4 idle frames
    for frame_num in range(4):
        frame = f"idle_{frame_num}"
        svg_content, config_info = generator.generate_deterministic("test@example.com", frame=frame)

        # All frames should have valid output
        assert svg_content is not None
        assert len(svg_content) > 0
        assert config_info["frame"] == frame

        # Frame 0: open eyes, body left
        if frame_num == 0:
            assert config_info["eye_override"] == "open"
            assert config_info["body_transform"] == "translate(-1.5, 0)"
            assert "translate(-1.5, 0)" in svg_content

        # Frame 1: open eyes, body center
        elif frame_num == 1:
            assert config_info["eye_override"] == "open"
            assert config_info["body_transform"] == ""

        # Frame 2: closed eyes (blink), body right
        elif frame_num == 2:
            assert config_info["eye_override"] == "closed"
            assert config_info["body_transform"] == "translate(1.5, 0)"
            assert "translate(1.5, 0)" in svg_content

        # Frame 3: open eyes, body center
        elif frame_num == 3:
            assert config_info["eye_override"] == "open"
            assert config_info["body_transform"] == ""


def test_emote_frames_control_eye_and_mouth_states():
    """Emote frames should control eye/mouth open/closed states."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    # Test happy emote
    svg_content, config_info = generator.generate_deterministic("test@example.com", frame="happy")
    assert config_info["eye_override"] == "open"
    assert config_info["mouth_override"] == "open"

    # Test sad emote
    svg_content, config_info = generator.generate_deterministic("test@example.com", frame="sad")
    assert config_info["eye_override"] == "open"
    assert config_info["mouth_override"] == "closed"

    # Test surprised emote
    svg_content, config_info = generator.generate_deterministic("test@example.com", frame="surprised")
    assert config_info["eye_override"] == "open"
    assert config_info["mouth_override"] == "open"

    # Test angry emote
    svg_content, config_info = generator.generate_deterministic("test@example.com", frame="angry")
    assert config_info["eye_override"] == "open"
    assert config_info["mouth_override"] == "closed"

    # Test bored emote
    svg_content, config_info = generator.generate_deterministic("test@example.com", frame="bored")
    assert config_info["eye_override"] == "closed"
    assert config_info["mouth_override"] == "closed"
