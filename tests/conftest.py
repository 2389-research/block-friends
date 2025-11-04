#!/usr/bin/env python3
import os

# Set up Cairo library path for macOS before any imports
os.environ.setdefault('DYLD_FALLBACK_LIBRARY_PATH', '/opt/homebrew/opt/cairo/lib')
