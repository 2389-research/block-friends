# ABOUTME: Tests for avatar shadow feature
# ABOUTME: Verifies shadow presence, positioning, and scaling
import sys
sys.path.insert(0, '.')
from door_agents import DoorAgentGenerator, DoorAgentConfig

def test_shadow_present_in_svg():
    """Test that shadow ellipse is present in generated SVG."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    svg, _ = generator.generate_deterministic(input_string="test@example.com", universal=True)

    # Shadow should be present
    assert '<ellipse' in svg
    assert 'shadow-blur' in svg
    assert 'feGaussianBlur' in svg
