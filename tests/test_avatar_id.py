# ABOUTME: Tests for avatar ID generation and SVG root element attributes
# ABOUTME: Validates deterministic ID generation and agent class application

from door_agents import DoorAgentGenerator, DoorAgentConfig

def test_avatar_id_is_deterministic():
    """Avatar ID should be consistent for same email."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    svg1, _ = generator.generate_deterministic('test@example.com')
    svg2, _ = generator.generate_deterministic('test@example.com')

    # Both should have same ID
    assert 'id="avatar-973dfe463ec8"' in svg1
    assert 'id="avatar-973dfe463ec8"' in svg2

def test_avatar_id_differs_by_email():
    """Different emails should get different avatar IDs."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    svg1, _ = generator.generate_deterministic('alice@example.com')
    svg2, _ = generator.generate_deterministic('bob@example.com')

    # Extract IDs - they should differ
    import re
    id1 = re.search(r'id="(avatar-[^"]+)"', svg1).group(1)
    id2 = re.search(r'id="(avatar-[^"]+)"', svg2).group(1)

    assert id1 != id2

def test_avatar_has_agent_class():
    """All avatars should have 'agent' class."""
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    svg, _ = generator.generate_deterministic('test@example.com')

    assert 'class="agent' in svg
