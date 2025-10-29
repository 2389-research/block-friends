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

def test_shadow_scales_with_hair():
    """Test that shadow width accounts for hair extent."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    # Generate avatar with known wide hair
    svg, _ = generator.generate_deterministic(input_string="wide-hair@example.com", universal=True)

    # Extract ellipse rx (width radius)
    import re
    match = re.search(r'<ellipse[^>]*rx="([^"]+)"', svg)
    assert match, "Shadow ellipse should have rx attribute"

    shadow_rx = float(match.group(1))
    assert shadow_rx > 30, "Shadow should be wider than minimal body"

def test_shadow_positioned_at_bottom():
    """Test that shadow is positioned at bottom with overlap."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    svg, _ = generator.generate_deterministic(input_string="test@example.com", universal=True)

    # Extract ellipse cy (center y)
    import re
    match = re.search(r'<ellipse[^>]*cy="([^"]+)"', svg)
    assert match, "Shadow ellipse should have cy attribute"

    shadow_cy = float(match.group(1))
    # Should be near bottom (CELL=60, overlap=3, so cy should be ~57)
    assert 55 <= shadow_cy <= 58, f"Shadow cy should be near bottom, got {shadow_cy}"
