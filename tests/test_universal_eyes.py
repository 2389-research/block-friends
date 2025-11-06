# ABOUTME: Tests for universal eyes generation with nested groups
# ABOUTME: Verifies all 7 eye states are included and properly structured

import pytest
from door_agents import DoorAgentGenerator, DoorAgentConfig


def test_universal_eyes_has_nested_groups():
    """Universal eyes should have nested <g> structure."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    # _generate_universal_eyes returns (clipPaths, eyes_svg)
    clipPaths, eyes_svg = generator._generate_universal_eyes(
        open_eye_idx=0,
        closed_eye_idx=0,
        email='test@example.com',
        shape=(6, 7),
        cell_size=60,
        pad=1.5,
        avatar_id='test-avatar'
    )

    assert 'class="eyes"' in eyes_svg
    assert '<g class="open"' in eyes_svg
    assert '<g class="closed"' in eyes_svg
    assert '<g class="happy"' in eyes_svg


def test_universal_eyes_includes_all_emotes():
    """Universal eyes should include all 7 states."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    # _generate_universal_eyes returns (clipPaths, eyes_svg)
    clipPaths, eyes_svg = generator._generate_universal_eyes(
        open_eye_idx=0,
        closed_eye_idx=0,
        email='test@example.com',
        shape=(6, 7),
        cell_size=60,
        pad=1.5,
        avatar_id='test-avatar'
    )

    emotes = ['open', 'closed', 'happy', 'sad', 'surprised', 'angry', 'bored']
    for emote in emotes:
        assert f'<g class="{emote}"' in eyes_svg


def test_universal_eyes_has_transform():
    """Universal eyes should have transform attribute for positioning."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    # _generate_universal_eyes returns (clipPaths, eyes_svg)
    clipPaths, eyes_svg = generator._generate_universal_eyes(
        open_eye_idx=0,
        closed_eye_idx=0,
        email='test@example.com',
        shape=(6, 7),
        cell_size=60,
        pad=1.5,
        avatar_id='test-avatar'
    )

    assert 'transform=' in eyes_svg
    assert 'translate' in eyes_svg
    assert 'scale' in eyes_svg
