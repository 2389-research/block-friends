#!/usr/bin/env python3
# ABOUTME: API tests for transition endpoints
# ABOUTME: Tests single-frame transition endpoint with caching

import hashlib

from fastapi.testclient import TestClient

from app import CACHE_DIR, app

client = TestClient(app)


def test_transition_endpoint_basic():
    """Test basic transition endpoint returns SVG."""
    response = client.get("/avatar/test@example.com/transition/happy/50")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
    assert b"<svg" in response.content
    assert b"base-layer" in response.content
    assert b"emote-layer" in response.content


def test_transition_endpoint_all_emotes():
    """Test transition endpoint for all emotes."""
    emotes = ["happy", "sad", "surprised", "angry", "bored"]

    for emote in emotes:
        response = client.get(f"/avatar/test@example.com/transition/{emote}/50")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/svg+xml"


def test_transition_endpoint_vowels():
    """Test transition endpoint for vowels."""
    vowels = ["a", "e", "i", "o", "u"]

    for vowel in vowels:
        response = client.get(f"/avatar/test@example.com/transition/vowel_{vowel}/50")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/svg+xml"


def test_transition_endpoint_weight_extremes():
    """Test transition at weight boundaries."""
    # Weight 0
    response = client.get("/avatar/test@example.com/transition/happy/0")
    assert response.status_code == 200
    assert b'opacity="1.0"' in response.content

    # Weight 100
    response = client.get("/avatar/test@example.com/transition/happy/100")
    assert response.status_code == 200
    assert b'opacity="1.0"' in response.content


def test_transition_endpoint_invalid_emote():
    """Test that invalid emote returns 400."""
    response = client.get("/avatar/test@example.com/transition/invalid/50")
    assert response.status_code == 400
    assert "Unknown emote" in response.json()["detail"]


def test_transition_endpoint_invalid_weight():
    """Test that invalid weight returns 400."""
    response = client.get("/avatar/test@example.com/transition/happy/150")
    assert response.status_code == 400
    assert "Weight must be between 0 and 100" in response.json()["detail"]


def test_transition_endpoint_caching():
    """Test that transitions are cached to filesystem."""
    input_str = "cache-test@example.com"
    hash_hex = hashlib.sha256(input_str.encode("utf-8")).hexdigest()[:16]
    cache_path = CACHE_DIR / f"{hash_hex}_transition_happy_50.svg"

    # Remove cache if exists
    if cache_path.exists():
        cache_path.unlink()

    # First request should generate and cache
    response1 = client.get(f"/avatar/{input_str}/transition/happy/50")
    assert response1.status_code == 200
    assert cache_path.exists()

    # Second request should use cache
    response2 = client.get(f"/avatar/{input_str}/transition/happy/50")
    assert response2.status_code == 200
    assert response1.content == response2.content


def test_transition_endpoint_url_encoded():
    """Test that URL-encoded input strings work correctly."""
    response = client.get("/avatar/test%40example.com/transition/happy/50")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
