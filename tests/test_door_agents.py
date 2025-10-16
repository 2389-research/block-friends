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
