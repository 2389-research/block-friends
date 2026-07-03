#!/usr/bin/env python3
# ABOUTME: Pytest configuration for test setup
# ABOUTME: Sets Cairo library path for macOS and resets rate limiter between tests

import os
import sys

# Set Cairo library path for macOS before importing cairosvg
if sys.platform == "darwin":
    cairo_path = "/opt/homebrew/opt/cairo/lib"
    if os.path.exists(cairo_path):
        # Set DYLD_LIBRARY_PATH for macOS dynamic library loading
        os.environ["DYLD_LIBRARY_PATH"] = cairo_path
        # Also set DYLD_FALLBACK_LIBRARY_PATH as backup
        os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = cairo_path

import pytest


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    # slowapi's in-memory limiter is a module-level singleton; without this
    # reset, requests accumulate across tests and later tests spuriously
    # hit 429s.
    from app import limiter
    limiter.reset()
    yield
