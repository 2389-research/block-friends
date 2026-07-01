# ABOUTME: Tests for feet generation extraction
# ABOUTME: Validates _generate_feet method produces correct SVG output

from door_agents import DoorAgentGenerator, DoorAgentConfig

def test_feet_generation_includes_rectangles():
    """Feet should include two rectangles."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    feet_svg = generator._generate_feet(
        shape=(6, 7),
        body_color="#F7AB39",
        node_color="#6EDCD9",
        feet_match_body=False,
        cell_size=60,
        pad=1.5
    )

    assert feet_svg.count('<rect') == 2
    assert 'fill="#6EDCD9"' in feet_svg

def test_feet_match_body_color():
    """Feet should use body color when feet_match_body is True."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    feet_svg = generator._generate_feet(
        shape=(6, 7),
        body_color="#F7AB39",
        node_color="#6EDCD9",
        feet_match_body=True,
        cell_size=60,
        pad=1.5
    )

    assert 'fill="#F7AB39"' in feet_svg
