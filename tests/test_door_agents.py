# ABOUTME: Test suite for door agent generation system
# ABOUTME: Covers config loading, deterministic generation, and emote system functionality
"""Tests for door agent generation system."""
import pytest
import re
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
    """Idle animation should use eye/mouth state overrides for 10-frame cycle."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    # Test all 10 idle frames (use legacy mode for frame-specific animation)
    for frame_num in range(10):
        frame = f"idle_{frame_num}"
        svg_content, config_info = generator.generate_deterministic("test@example.com", frame=frame, universal=False)

        # All frames should have valid output
        assert svg_content is not None
        assert len(svg_content) > 0
        assert config_info["frame"] == frame

        # Frame 0: open eyes, closed mouth
        if frame_num == 0:
            assert config_info["eye_override"] == "open"
            assert config_info["mouth_override"] == "closed"

        # Frame 1: open eyes, open mouth
        elif frame_num == 1:
            assert config_info["eye_override"] == "open"
            assert config_info["mouth_override"] == "open"

        # Frame 2: closed eyes (blink), closed mouth
        elif frame_num == 2:
            assert config_info["eye_override"] == "closed"
            assert config_info["mouth_override"] == "closed"

        # Frame 3-9: Various combinations
        else:
            assert config_info["eye_override"] is not None
            assert config_info["mouth_override"] is not None


def test_emote_frames_control_eye_and_mouth_states():
    """Emote frames should control eye/mouth open/closed states (legacy mode)."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    # Test happy emote (use legacy mode for frame-specific state overrides)
    svg_content, config_info = generator.generate_deterministic("test@example.com", frame="happy", universal=False)
    assert config_info["eye_override"] == "open"
    assert config_info["mouth_override"] == "open"

    # Test sad emote
    svg_content, config_info = generator.generate_deterministic("test@example.com", frame="sad", universal=False)
    assert config_info["eye_override"] == "open"
    assert config_info["mouth_override"] == "closed"

    # Test surprised emote
    svg_content, config_info = generator.generate_deterministic("test@example.com", frame="surprised", universal=False)
    assert config_info["eye_override"] == "open"
    assert config_info["mouth_override"] == "open"

    # Test angry emote
    svg_content, config_info = generator.generate_deterministic("test@example.com", frame="angry", universal=False)
    assert config_info["eye_override"] == "open"
    assert config_info["mouth_override"] == "closed"

    # Test bored emote (uses half-lidded/clipped open eyes)
    _, config_info = generator.generate_deterministic("test@example.com", frame="bored", universal=False)
    assert config_info["eye_override"] == "open"
    assert config_info["mouth_override"] == "closed"


# ==================== COMPREHENSIVE INTEGRATION TESTS ====================

def test_emote_variant_assets_exist():
    """Test that emote variant SVG files are properly loaded from assets directory."""
    config = DoorAgentConfig()
    assets_path = config.assets_path

    # Test that open and closed eye/mouth directories exist and have numbered assets
    assert len(config.open_eyes) > 0, "No open eye assets loaded"
    assert len(config.closed_eyes) > 0, "No closed eye assets loaded"
    assert len(config.open_mouths) > 0, "No open mouth assets loaded"
    assert len(config.closed_mouths) > 0, "No closed mouth assets loaded"

    # Verify expected emote variants exist in subdirectories
    # Emote variants are stored in open/ and closed/ subdirectories with emote_ prefix
    emote_names = ['happy', 'sad', 'surprised', 'angry', 'bored']

    for emote in emote_names:
        # Check for emote eye variants in eyes subdirectories
        open_eyes_path = assets_path / "eyes" / "open"
        closed_eyes_path = assets_path / "eyes" / "closed"

        open_eye_emotes = list(open_eyes_path.glob(f"emote_{emote}_*.svg"))
        closed_eye_emotes = list(closed_eyes_path.glob(f"emote_{emote}_*.svg"))

        assert len(open_eye_emotes) > 0 or len(closed_eye_emotes) > 0, \
            f"Missing emote eye variant files for {emote}"

        # Check for emote mouth variants in mouths subdirectories
        open_mouths_path = assets_path / "mouths" / "open"
        closed_mouths_path = assets_path / "mouths" / "closed"

        open_mouth_emotes = list(open_mouths_path.glob(f"emote_{emote}_*.svg"))
        closed_mouth_emotes = list(closed_mouths_path.glob(f"emote_{emote}_*.svg"))

        assert len(open_mouth_emotes) > 0 or len(closed_mouth_emotes) > 0, \
            f"Missing emote mouth variant files for {emote}"


def test_asset_naming_conventions():
    """Test that asset files follow the expected naming conventions."""
    config = DoorAgentConfig()
    assets_path = config.assets_path

    # Check open eyes have numbered files
    open_eyes_path = assets_path / "eyes" / "open"
    open_eye_files = list(open_eyes_path.glob("*.svg"))
    numbered_open_eyes = [f for f in open_eye_files if f.stem.isdigit()]
    assert len(numbered_open_eyes) > 0, "No numbered open eye assets found"

    # Check closed eyes have numbered files
    closed_eyes_path = assets_path / "eyes" / "closed"
    closed_eye_files = list(closed_eyes_path.glob("*.svg"))
    numbered_closed_eyes = [f for f in closed_eye_files if f.stem.isdigit()]
    assert len(numbered_closed_eyes) > 0, "No numbered closed eye assets found"

    # Check emote eye naming (emote_<name>_<number>.svg)
    emote_eye_pattern = re.compile(r'emote_\w+_\d+\.svg')
    emote_eyes = [f.name for f in open_eye_files if emote_eye_pattern.match(f.name)]
    assert len(emote_eyes) > 0, "No emote eye variants found with correct naming"

    # Check emote mouth naming
    open_mouths_path = assets_path / "mouths" / "open"
    open_mouth_files = list(open_mouths_path.glob("*.svg"))
    emote_mouths = [f.name for f in open_mouth_files if emote_eye_pattern.match(f.name)]
    assert len(emote_mouths) > 0, "No emote mouth variants found with correct naming"


def test_all_emotes_generate_correct_state_overrides():
    """Test that all 5 emotes produce the expected eye/mouth state overrides (legacy mode)."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    test_input = "test@example.com"

    # Define expected states for each emote
    expected_states = {
        'happy': {'eye': 'open', 'mouth': 'open'},
        'sad': {'eye': 'open', 'mouth': 'closed'},
        'surprised': {'eye': 'open', 'mouth': 'open'},
        'angry': {'eye': 'open', 'mouth': 'closed'},
        'bored': {'eye': 'open', 'mouth': 'closed'}  # Uses half-lidded/clipped open eyes
    }

    for emote, expected in expected_states.items():
        svg_content, config_info = generator.generate_deterministic(test_input, frame=emote, universal=False)

        # Verify state overrides
        assert config_info['eye_override'] == expected['eye'], \
            f"Emote '{emote}' has incorrect eye override: expected {expected['eye']}, got {config_info['eye_override']}"
        assert config_info['mouth_override'] == expected['mouth'], \
            f"Emote '{emote}' has incorrect mouth override: expected {expected['mouth']}, got {config_info['mouth_override']}"

        # Verify SVG content is generated
        assert svg_content is not None and len(svg_content) > 0, \
            f"Emote '{emote}' generated empty SVG"


def test_idle_animation_produces_10_frames():
    """Test that idle animation has exactly 10 frames with correct states."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    test_input = "test@example.com"

    # Idle animation should have frames 0-9
    for frame_num in range(10):
        frame = f"idle_{frame_num}"
        svg_content, config_info = generator.generate_deterministic(test_input, frame=frame)

        # All frames should generate valid SVG
        assert svg_content is not None, f"Frame {frame} generated None"
        assert len(svg_content) > 0, f"Frame {frame} generated empty SVG"
        assert config_info['frame'] == frame, f"Config info frame mismatch for {frame}"


def test_idle_animation_blink_on_frame_2():
    """Test that idle animation blinks (closes eyes) on frame 2."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    test_input = "test@example.com"

    # Frame 2 should have closed eyes (blink)
    svg_content, config_info = generator.generate_deterministic(test_input, frame="idle_2")
    assert config_info['eye_override'] == 'closed', \
        "Idle frame 2 should have closed eyes for blink"

    # Other frames should have open eyes
    for frame_num in [0, 1, 3]:
        frame = f"idle_{frame_num}"
        svg_content, config_info = generator.generate_deterministic(test_input, frame=frame)
        assert config_info['eye_override'] == 'open', \
            f"Idle frame {frame_num} should have open eyes"


def test_idle_animation_uses_overrides_not_transforms():
    """Test that idle animation uses eye/mouth overrides instead of body transforms."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    test_input = "test@example.com"

    # Current implementation doesn't use body_transform for idle frames
    # Animation is done via eye/mouth state changes instead
    for frame_num in range(10):
        frame = f"idle_{frame_num}"
        _, config_info = generator.generate_deterministic(test_input, frame=frame, universal=False)

        # Body transform should be empty for all idle frames in current system
        assert config_info['body_transform'] == '', \
            f"Frame {frame_num} has unexpected body_transform: '{config_info['body_transform']}'"

        # Verify eye and mouth overrides are present instead
        assert config_info['eye_override'] is not None, \
            f"Frame {frame_num} missing eye_override"
        assert config_info['mouth_override'] is not None, \
            f"Frame {frame_num} missing mouth_override"


def test_deterministic_generation_same_input():
    """Test that same input string produces identical avatar."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    test_input = "deterministic@test.com"

    # Generate same avatar twice
    svg1, config1 = generator.generate_deterministic(test_input)
    svg2, config2 = generator.generate_deterministic(test_input)

    # SVG content should be identical
    assert svg1 == svg2, "Same input produced different SVG content"

    # All configuration values should match
    assert config1['body_shape'] == config2['body_shape']
    assert config1['open_eye_index'] == config2['open_eye_index']
    assert config1['closed_eye_index'] == config2['closed_eye_index']
    assert config1['open_mouth_index'] == config2['open_mouth_index']
    assert config1['closed_mouth_index'] == config2['closed_mouth_index']
    assert config1['hair_index'] == config2['hair_index']
    assert config1['body_color'] == config2['body_color']
    assert config1['node_color'] == config2['node_color']
    assert config1['feet_match_body'] == config2['feet_match_body']


def test_deterministic_generation_different_inputs():
    """Test that different input strings produce different avatars."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    # Generate avatars with different inputs
    svg1, config1 = generator.generate_deterministic("user1@example.com")
    svg2, config2 = generator.generate_deterministic("user2@example.com")
    svg3, config3 = generator.generate_deterministic("user3@example.com")

    # SVG content should be different (high probability)
    assert svg1 != svg2 or svg1 != svg3 or svg2 != svg3, \
        "Different inputs produced identical avatars"

    # At least some configuration values should differ
    configs_differ = (
        config1['body_shape'] != config2['body_shape'] or
        config1['open_eye_index'] != config2['open_eye_index'] or
        config1['body_color'] != config2['body_color'] or
        config1['hair_index'] != config2['hair_index']
    )
    assert configs_differ, "Different inputs produced identical configurations"


def test_deterministic_four_indices_assigned():
    """Test that deterministic generation assigns all 4 eye/mouth indices."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    test_input = "four_indices@test.com"
    svg_content, config_info = generator.generate_deterministic(test_input)

    # Verify all 4 indices are present and valid
    assert 'open_eye_index' in config_info, "Missing open_eye_index"
    assert 'closed_eye_index' in config_info, "Missing closed_eye_index"
    assert 'open_mouth_index' in config_info, "Missing open_mouth_index"
    assert 'closed_mouth_index' in config_info, "Missing closed_mouth_index"

    # Verify indices are within valid ranges (1-indexed in config_info)
    assert 1 <= config_info['open_eye_index'] <= len(config.open_eyes), \
        f"Invalid open_eye_index: {config_info['open_eye_index']}"
    assert 1 <= config_info['closed_eye_index'] <= len(config.closed_eyes), \
        f"Invalid closed_eye_index: {config_info['closed_eye_index']}"
    assert 1 <= config_info['open_mouth_index'] <= len(config.open_mouths), \
        f"Invalid open_mouth_index: {config_info['open_mouth_index']}"
    assert 1 <= config_info['closed_mouth_index'] <= len(config.closed_mouths), \
        f"Invalid closed_mouth_index: {config_info['closed_mouth_index']}"


def test_asset_counts_match_expectations():
    """Test that asset counts match expected directory structure."""
    config = DoorAgentConfig()
    assets_path = config.assets_path

    # Open/closed variants should exist
    assert len(config.open_eyes) >= 2, "Expected at least 2 open eye variants"
    assert len(config.closed_eyes) >= 2, "Expected at least 2 closed eye variants"
    assert len(config.open_mouths) >= 2, "Expected at least 2 open mouth variants"
    assert len(config.closed_mouths) >= 2, "Expected at least 2 closed mouth variants"

    # Legacy combined lists should have correct counts
    assert len(config.EYES) == len(config.open_eyes) + len(config.closed_eyes), \
        "Combined EYES list doesn't match open + closed counts"
    assert len(config.MOUTHS) == len(config.open_mouths) + len(config.closed_mouths), \
        "Combined MOUTHS list doesn't match open + closed counts"

    # Emote variant files should exist in subdirectories (at least 5 different emotions)
    # Count unique emote names (excluding numbered variants)
    open_eyes_path = assets_path / "eyes" / "open"
    emote_eye_files = list(open_eyes_path.glob("emote_*.svg"))
    emote_eye_names = set()
    for f in emote_eye_files:
        # Extract emote name from pattern emote_<name>_<number>.svg
        match = re.match(r'emote_(\w+)_\d+', f.stem)
        if match:
            emote_eye_names.add(match.group(1))

    open_mouths_path = assets_path / "mouths" / "open"
    emote_mouth_files = list(open_mouths_path.glob("emote_*.svg"))
    emote_mouth_names = set()
    for f in emote_mouth_files:
        match = re.match(r'emote_(\w+)_\d+', f.stem)
        if match:
            emote_mouth_names.add(match.group(1))

    assert len(emote_eye_names) >= 5, f"Expected at least 5 emote eye types, found {len(emote_eye_names)}: {emote_eye_names}"
    assert len(emote_mouth_names) >= 5, f"Expected at least 5 emote mouth types, found {len(emote_mouth_names)}: {emote_mouth_names}"

    # Hair assets should exist
    assert len(config.HAIRS) > 0, "Expected at least some hair assets"


def test_version_tracking_in_config():
    """Test that config_info includes avatar_system_version."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    # Test random generation
    svg_random, config_random = generator.generate_random()
    assert 'avatar_system_version' in config_random, \
        "Random generation missing avatar_system_version"
    assert config_random['avatar_system_version'] == "2.0", \
        f"Expected version 2.0, got {config_random['avatar_system_version']}"

    # Test deterministic generation
    svg_det, config_det = generator.generate_deterministic("test@example.com")
    assert 'avatar_system_version' in config_det, \
        "Deterministic generation missing avatar_system_version"
    assert config_det['avatar_system_version'] == "2.0", \
        f"Expected version 2.0, got {config_det['avatar_system_version']}"


def test_version_constant_accessible():
    """Test that AVATAR_SYSTEM_VERSION constant is accessible from module."""
    from door_agents import AVATAR_SYSTEM_VERSION

    assert AVATAR_SYSTEM_VERSION is not None, "AVATAR_SYSTEM_VERSION not defined"
    assert AVATAR_SYSTEM_VERSION == "2.0", \
        f"Expected version '2.0', got '{AVATAR_SYSTEM_VERSION}'"


def test_neutral_frame_no_overrides():
    """Test that neutral frame doesn't apply any state overrides."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    test_input = "neutral@test.com"
    svg_content, config_info = generator.generate_deterministic(test_input, frame="neutral")

    # Neutral frame should have None for overrides
    assert config_info['eye_override'] is None, \
        "Neutral frame should not override eye state"
    assert config_info['mouth_override'] is None, \
        "Neutral frame should not override mouth state"
    assert config_info['body_transform'] == '', \
        "Neutral frame should not have body transform"


def test_emote_animation_complete_workflow():
    """Integration test: Generate complete animation sequence for an emote."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    test_input = "animation@test.com"

    # Generate neutral base
    svg_neutral, config_neutral = generator.generate_deterministic(test_input, frame="neutral")
    assert svg_neutral is not None

    # Generate all 10 idle frames
    idle_svgs = []
    for i in range(10):
        svg, conf = generator.generate_deterministic(test_input, frame=f"idle_{i}")
        assert svg is not None
        idle_svgs.append(svg)

    # All idle frames should be different (due to eye/mouth overrides)
    assert len(set(idle_svgs)) > 1, "Idle animation frames should differ"

    # Generate all emote frames
    emotes = ['happy', 'sad', 'surprised', 'angry', 'bored']
    for emote in emotes:
        svg, conf = generator.generate_deterministic(test_input, frame=emote)
        assert svg is not None
        assert conf['frame'] == emote


def test_hash_byte_allocation_consistency():
    """Test that hash bytes consistently map to the same features."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    # Use a specific input to get deterministic results
    test_input = "hash_test@example.com"

    # Generate multiple times and verify indices remain consistent
    results = []
    for _ in range(5):
        svg, conf = generator.generate_deterministic(test_input)
        results.append({
            'open_eye': conf['open_eye_index'],
            'closed_eye': conf['closed_eye_index'],
            'open_mouth': conf['open_mouth_index'],
            'closed_mouth': conf['closed_mouth_index'],
            'body_shape': conf['body_shape'],
            'body_color': conf['body_color'],
            'node_color': conf['node_color']
        })

    # All results should be identical
    first = results[0]
    for result in results[1:]:
        assert result == first, "Hash byte allocation is not consistent"


def test_body_color_node_color_constraint():
    """Test that body color and node color are always different."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    # Test with multiple different inputs
    test_inputs = [
        "color_test1@example.com",
        "color_test2@example.com",
        "color_test3@example.com",
        "color_test4@example.com",
        "color_test5@example.com"
    ]

    for test_input in test_inputs:
        svg, conf = generator.generate_deterministic(test_input)
        assert conf['body_color'] != conf['node_color'], \
            f"Body and node colors should differ for input '{test_input}': " \
            f"both are {conf['body_color']}"
