# tests/test_nodes_generation.py
from door_agents import DoorAgentConfig, DoorAgentGenerator


def test_nodes_generation_includes_circles():
    """Nodes should include two circles."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    nodes_svg = generator._generate_nodes(shape=(6, 7), node_color="#6EDCD9", cell_size=60, pad=1.5)

    assert nodes_svg.count("<circle") == 2
    assert 'fill="#6EDCD9"' in nodes_svg
