# ABOUTME: Tests for body generation extraction
# ABOUTME: Validates _generate_body method produces correct SVG elements

import pytest
from door_agents import DoorAgentGenerator, DoorAgentConfig


def test_body_generation_includes_rectangle():
    """Body should include main rectangle."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    body_svg = generator._generate_body(
        shape=(6, 7),
        body_color="#F7AB39",
        cell_size=60,
        pad=1.5
    )

    assert '<rect' in body_svg
    assert 'fill="#F7AB39"' in body_svg


def test_body_generation_includes_vertical_line():
    """Body should include vertical center line."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    body_svg = generator._generate_body(
        shape=(6, 7),
        body_color="#F7AB39",
        cell_size=60,
        pad=1.5
    )

    assert '<line' in body_svg
