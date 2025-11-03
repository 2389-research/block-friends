# tests/test_universal_parameter.py
import pytest
from door_agents import DoorAgentGenerator, DoorAgentConfig

def test_universal_mode_includes_style_block():
    """Universal mode should include CSS style block."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    svg, _ = generator.generate_deterministic('test@example.com', frame='idle_0', universal=True)

    assert '<style>' in svg
    assert '.eyes > g' in svg
    assert '.mouths > g' in svg

def test_universal_mode_includes_nested_groups():
    """Universal mode should include nested eye/mouth groups."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    svg, _ = generator.generate_deterministic('test@example.com', frame='idle_0', universal=True)

    assert '<g class="eyes"' in svg
    assert '<g class="mouths"' in svg
    assert '<g class="open">' in svg
    assert '<g class="closed">' in svg

def test_legacy_mode_single_state():
    """Legacy mode should only include single eye/mouth state."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    svg, _ = generator.generate_deterministic('test@example.com', frame='idle_0', universal=False)

    # Should NOT have style block or nested groups
    assert '<style>' not in svg
    assert '<g class="eyes">' not in svg
    assert '<g class="mouths">' not in svg

def test_universal_mode_default():
    """Universal mode should be the default."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    # Call without universal parameter - should default to True
    svg, _ = generator.generate_deterministic('test@example.com', frame='idle_0')

    # Should have universal mode features
    assert '<style>' in svg
    assert '<g class="eyes"' in svg
    assert '<g class="mouths"' in svg
