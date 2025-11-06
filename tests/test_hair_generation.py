# ABOUTME: Tests for hair generation extraction
# ABOUTME: Verifies _generate_hair method produces correct SVG with positioning and z-order

import pytest
from door_agents import DoorAgentGenerator, DoorAgentConfig


def test_hair_generation_with_front_hair():
    """Hair generation should return SVG for front z-order hair."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    # Hair #2 (index 1) has z-order="front"
    hair_svg = generator._generate_hair(
        hair_index=1,
        hair_color_hash_byte=123,
        body_color="#F7AB39",
        shape=(6, 7),
        cell_size=60,
        pad=1.5,
        z_order='front'
    )

    assert '<g' in hair_svg
    assert 'transform=' in hair_svg
    assert 'color=' in hair_svg


def test_hair_generation_with_behind_hair():
    """Hair generation should return SVG for behind z-order hair."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    # Hair #1 (index 0) has z-order="behind"
    hair_svg = generator._generate_hair(
        hair_index=0,
        hair_color_hash_byte=123,
        body_color="#F7AB39",
        shape=(6, 7),
        cell_size=60,
        pad=1.5,
        z_order='behind'
    )

    assert '<g' in hair_svg
    assert 'transform=' in hair_svg
    assert 'color=' in hair_svg


def test_hair_generation_wrong_z_order():
    """Hair generation should return empty string when z-order doesn't match."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    # Hair #1 (index 0) has z-order="behind", asking for "front" should return empty
    hair_svg = generator._generate_hair(
        hair_index=0,
        hair_color_hash_byte=123,
        body_color="#F7AB39",
        shape=(6, 7),
        cell_size=60,
        pad=1.5,
        z_order='front'
    )

    assert hair_svg == ""


def test_hair_generation_without_hair():
    """Hair generation should return empty string when no hair."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    hair_svg = generator._generate_hair(
        hair_index=None,
        hair_color_hash_byte=0,
        body_color="#F7AB39",
        shape=(6, 7),
        cell_size=60,
        pad=1.5,
        z_order='front'
    )

    assert hair_svg == ""
