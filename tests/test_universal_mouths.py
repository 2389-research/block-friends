# ABOUTME: Tests for universal mouths generation functionality
# ABOUTME: Verifies that _generate_universal_mouths creates nested SVG groups for all 12 mouth states

from door_agents import DoorAgentGenerator, DoorAgentConfig

def test_universal_mouths_has_nested_groups():
    """Universal mouths should have nested <g> structure."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    mouths_svg = generator._generate_universal_mouths(
        open_mouth_idx=0,
        closed_mouth_idx=0,
        email='test@example.com',
        shape=(6, 7),
        cell_size=60,
        pad=1.5,
        open_eye_idx=0,
        closed_eye_idx=0
    )

    assert '<g class="mouths"' in mouths_svg
    assert '<g class="open"' in mouths_svg
    assert '<g class="closed"' in mouths_svg

def test_universal_mouths_includes_all_states():
    """Universal mouths should include all 12 states."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    mouths_svg = generator._generate_universal_mouths(
        open_mouth_idx=0,
        closed_mouth_idx=0,
        email='test@example.com',
        shape=(6, 7),
        cell_size=60,
        pad=1.5,
        open_eye_idx=0,
        closed_eye_idx=0
    )

    states = ['open', 'closed', 'happy', 'surprised', 'sad', 'angry', 'bored',
              'vowel_a', 'vowel_e', 'vowel_i', 'vowel_o', 'vowel_u']
    for state in states:
        assert f'<g class="{state}"' in mouths_svg
