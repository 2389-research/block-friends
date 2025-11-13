# ABOUTME: Tests for avatar shadow feature
# ABOUTME: Verifies shadow presence, positioning, and scaling
import sys

sys.path.insert(0, ".")
from door_agents import DoorAgentConfig, DoorAgentGenerator


def test_shadow_present_in_svg():
    """Test that shadow ellipse is present in generated SVG."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    svg, _ = generator.generate_deterministic(input_string="test@example.com", universal=True)

    # Shadow should be present
    assert "<ellipse" in svg
    assert "shadow-blur" in svg
    assert "feGaussianBlur" in svg


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
    assert shadow_rx > 15, "Shadow should scale with content width (body + hair + nodes)"


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
    # Shadow below feet: body_bottom + foot_height + 1, typically around 53 for standard avatar
    assert 51 <= shadow_cy <= 54, f"Shadow cy should be below feet, got {shadow_cy}"


def test_shadow_renders_behind_body():
    """Test that shadow appears before body in SVG (renders behind)."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    svg, _ = generator.generate_deterministic(input_string="test@example.com", universal=True)

    # Find positions in SVG
    shadow_pos = svg.find("<ellipse")
    body_pos = svg.find("<rect")
    defs_close = svg.find("</defs>")

    assert shadow_pos > 0, "Shadow should be present"
    assert body_pos > 0, "Body should be present"
    assert defs_close > 0, "Defs should be present"

    # Shadow should come after defs but before body
    assert defs_close < shadow_pos < body_pos, "Shadow should render between defs and body"
