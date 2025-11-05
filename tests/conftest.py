#!/usr/bin/env python3
# ABOUTME: Pytest configuration for test setup
# ABOUTME: Sets Cairo library path for macOS before any imports

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
