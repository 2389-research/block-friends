#!/usr/bin/env python3
import pytest
from fastapi.testclient import TestClient
from app import app
import xml.etree.ElementTree as ET


client = TestClient(app)


def test_transition_endpoint_exists():
    """Test that transition endpoint is accessible."""
    response = client.get("/avatar/test@example.com/transition/joy/0")
    assert response.status_code == 200
    assert response.headers['content-type'] == 'image/svg+xml'


def test_transition_neutral_weight():
    """Test 0% weight returns valid SVG."""
    response = client.get("/avatar/test@example.com/transition/joy/0")
    assert response.status_code == 200

    # Parse SVG
    root = ET.fromstring(response.content)
    assert root.tag.endswith('svg')


def test_transition_full_weight():
    """Test 100% weight returns valid SVG."""
    response = client.get("/avatar/test@example.com/transition/joy/100")
    assert response.status_code == 200

    root = ET.fromstring(response.content)
    assert root.tag.endswith('svg')


def test_transition_mid_weights():
    """Test that intermediate weights work."""
    for weight in [25, 50, 75]:
        response = client.get(f"/avatar/test@example.com/transition/joy/{weight}")
        assert response.status_code == 200
        root = ET.fromstring(response.content)
        assert root.tag.endswith('svg')


def test_all_emotes_accessible():
    """Test that all emote endpoints work."""
    emotes = ['joy', 'sorrow', 'surprised', 'angry', 'bored', 'fun']

    for emote in emotes:
        response = client.get(f"/avatar/test@example.com/transition/{emote}/50")
        assert response.status_code == 200, f"Failed for emote: {emote}"


def test_all_vowels_accessible():
    """Test that all vowel endpoints work."""
    vowels = ['A', 'E', 'I', 'O', 'U']

    for vowel in vowels:
        response = client.get(f"/avatar/test@example.com/transition/{vowel}/50")
        assert response.status_code == 200, f"Failed for vowel: {vowel}"


def test_invalid_emote_returns_400():
    """Test that invalid emote name returns 400 error."""
    response = client.get("/avatar/test@example.com/transition/invalid/50")
    assert response.status_code == 400
    assert 'Invalid emote' in response.json()['detail']


def test_invalid_weight_returns_400():
    """Test that out-of-range weight returns 400 error."""
    response = client.get("/avatar/test@example.com/transition/joy/150")
    assert response.status_code == 400


def test_deterministic_output():
    """Test that same input produces same output."""
    response1 = client.get("/avatar/same@input.com/transition/joy/50")
    response2 = client.get("/avatar/same@input.com/transition/joy/50")

    assert response1.content == response2.content


def test_different_inputs_different_outputs():
    """Test that different inputs produce different avatars."""
    response1 = client.get("/avatar/input1@example.com/transition/joy/50")
    response2 = client.get("/avatar/input2@example.com/transition/joy/50")

    assert response1.content != response2.content


def test_caching_works():
    """Test that subsequent requests use cache."""
    # First request (cache miss)
    response1 = client.get("/avatar/cache-test@example.com/transition/joy/50")

    # Second request (cache hit)
    response2 = client.get("/avatar/cache-test@example.com/transition/joy/50")

    assert response1.content == response2.content
    assert response1.status_code == 200
    assert response2.status_code == 200
