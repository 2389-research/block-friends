# ABOUTME: Visual regression tests for universal and legacy SVG generation modes.
# ABOUTME: Tests verify structure and consistency of generated avatars across all states.
import pytest
from door_agents import DoorAgentGenerator, DoorAgentConfig
from pathlib import Path


@pytest.fixture
def generator():
    config = DoorAgentConfig()
    return DoorAgentGenerator(config)


def test_generate_all_universal_states(generator, tmp_path):
    """Generate SVGs for all states and verify they're valid."""
    email = 'visual-test@example.com'

    # All states to test
    states = (
        ['idle_0', 'idle_1', 'idle_2', 'idle_3', 'idle_4',
         'idle_5', 'idle_6', 'idle_7', 'idle_8', 'idle_9'] +
        ['happy', 'sad', 'surprised', 'angry', 'bored'] +
        ['vowel_a', 'vowel_e', 'vowel_i', 'vowel_o', 'vowel_u']
    )

    # Generate universal SVG (should work for all states via CSS)
    svg_universal, _ = generator.generate_deterministic(email, frame='idle_0', universal=True)

    # Verify basic structure
    assert '<svg id="avatar-' in svg_universal
    assert '<style>' in svg_universal
    assert '<g class="eyes"' in svg_universal
    assert '<g class="mouths"' in svg_universal

    # Save for manual inspection
    output_file = tmp_path / 'universal.svg'
    output_file.write_text(svg_universal)
    print(f"\nUniversal SVG saved to: {output_file}")

    # Verify each state class appears in CSS
    for state in states:
        assert f'.{state} ' in svg_universal or f'.{state}}}' in svg_universal, f"State {state} not found in CSS"


def test_legacy_mode_all_frames(generator, tmp_path):
    """Generate legacy SVGs for all frames and verify structure."""
    email = 'visual-test@example.com'

    frames = (
        ['idle_0', 'idle_1', 'idle_2', 'idle_3', 'idle_4',
         'idle_5', 'idle_6', 'idle_7', 'idle_8', 'idle_9'] +
        ['happy', 'sad', 'surprised', 'angry', 'bored'] +
        ['vowel_a', 'vowel_e', 'vowel_i', 'vowel_o', 'vowel_u']
    )

    for frame in frames:
        svg_legacy, _ = generator.generate_deterministic(email, frame=frame, universal=False)

        # Verify legacy structure (no style block or nested groups)
        assert '<style>' not in svg_legacy, f"Legacy frame {frame} should not have <style> block"
        assert '<g class="eyes"' not in svg_legacy, f"Legacy frame {frame} should not have nested eyes group"

        # But should still have avatar ID
        assert '<svg id="avatar-' in svg_legacy
        assert f'class="agent {frame}"' in svg_legacy

        # Save for manual inspection
        output_file = tmp_path / f'legacy_{frame}.svg'
        output_file.write_text(svg_legacy)

    print(f"\nLegacy SVGs saved to: {tmp_path}")


def test_universal_vs_legacy_consistency(generator):
    """Verify universal SVG with class matches legacy frame output."""
    email = 'consistency-test@example.com'

    # This test verifies that setting class="happy" on universal
    # produces visually equivalent result to legacy frame='happy'
    # We can't test visual equivalence programmatically, but we can
    # verify structure consistency

    svg_universal, info_u = generator.generate_deterministic(email, frame='happy', universal=True)
    svg_legacy, info_l = generator.generate_deterministic(email, frame='happy', universal=False)

    # Both should use same underlying indices
    assert info_u['open_eye_index'] == info_l['open_eye_index']
    assert info_u['closed_eye_index'] == info_l['closed_eye_index']
    assert info_u['open_mouth_index'] == info_l['open_mouth_index']
    assert info_u['closed_mouth_index'] == info_l['closed_mouth_index']

    # Both should have same avatar ID
    import re
    id_u = re.search(r'id="(avatar-[^"]+)"', svg_universal).group(1)
    id_l = re.search(r'id="(avatar-[^"]+)"', svg_legacy).group(1)
    assert id_u == id_l
