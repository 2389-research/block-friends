#!/usr/bin/env python3
# ABOUTME: FastAPI web app serving deterministic door agent avatars at /avatar/[hash].svg
# ABOUTME: Supports both hash and raw string inputs with file-based caching for performance

import hashlib
from pathlib import Path
from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import FileResponse
import uvicorn

from door_agents import DoorAgentConfig, DoorAgentGenerator

app = FastAPI(
    title="Door Agent Avatar Service",
    description="Deterministic avatar generation service with 1.27 billion unique variants",
    version="1.0.0"
)

# Initialize the door agent system
config = DoorAgentConfig()
generator = DoorAgentGenerator(config)

# Cache directory
CACHE_DIR = Path("out/avatar")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def get_cache_path(input_string: str) -> Path:
    """Generate cache file path based on input string."""
    hash_hex = hashlib.sha256(input_string.encode('utf-8')).hexdigest()[:16]
    return CACHE_DIR / f"{hash_hex}.svg"

def is_likely_hash(input_string: str) -> bool:
    """Check if input string looks like a hex hash (16+ hex chars)."""
    return len(input_string) >= 16 and all(c in '0123456789abcdefABCDEF' for c in input_string)

def generate_and_cache_avatar(input_string: str) -> Path:
    """Generate avatar and cache it, returning the cache file path."""
    cache_path = get_cache_path(input_string)
    
    # Return cached version if it exists
    if cache_path.exists():
        return cache_path
    
    # Generate new avatar
    svg_content, _ = generator.generate_deterministic(input_string)
    
    # Wrap in properly sized container
    cell_size = config.CELL
    full_svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{cell_size}" height="{cell_size}" '
                f'viewBox="0 0 {cell_size} {cell_size}">'
                f'<rect width="100%" height="100%" fill="none"/>'
                f'{svg_content}</svg>')
    
    # Cache the result
    cache_path.write_text(full_svg)
    return cache_path

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Door Agent Avatar Service",
        "version": "1.0.0",
        "description": "Deterministic avatar generation with 1.27B unique variants",
        "usage": {
            "avatar_by_hash": "/avatar/{hash}.svg",
            "avatar_by_email": "/avatar/{email}.svg",
            "examples": [
                "/avatar/test@example.com.svg",
                "/avatar/973dfe463ec85785.svg"
            ]
        },
        "features": [
            "Deterministic generation from any input string",
            "File-based caching for performance", 
            "1.27 billion unique variants",
            "Collision-resistant for ~1M users"
        ]
    }

@app.get("/avatar/{input_param}.svg")
async def get_avatar(input_param: str):
    """
    Generate and serve avatar SVG for given input.
    
    - **input_param**: Either a hex hash or raw string (like email address)
    - Returns SVG image with proper content-type headers
    - Cached results are served immediately for performance
    """
    try:
        # Handle both hash and raw input
        if is_likely_hash(input_param):
            # If it looks like a hash, try to find existing file first
            potential_cache = CACHE_DIR / f"{input_param}.svg"
            if potential_cache.exists():
                return FileResponse(
                    potential_cache,
                    media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=31536000"}  # 1 year cache
                )
            
            # If no cached file found, treat as raw input for generation
            input_string = input_param
        else:
            # Raw string input (like email)
            input_string = input_param
        
        # Generate and cache avatar
        cache_path = generate_and_cache_avatar(input_string)
        
        # Serve the cached file
        return FileResponse(
            cache_path,
            media_type="image/svg+xml", 
            headers={"Cache-Control": "public, max-age=31536000"}  # 1 year cache
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating avatar: {str(e)}")

@app.get("/avatar/{input_param}.svg/info")
async def get_avatar_info(input_param: str):
    """
    Get configuration information for an avatar without generating the image.
    
    - **input_param**: Either a hex hash or raw string (like email address)
    - Returns JSON with avatar configuration details
    """
    try:
        # Use the same input handling logic as avatar generation
        input_string = input_param
        
        # Generate avatar config (but don't cache the SVG)
        _, agent_config = generator.generate_deterministic(input_string)
        
        # Add cache info
        cache_path = get_cache_path(input_string) 
        agent_config["cache_info"] = {
            "cache_path": str(cache_path),
            "cached": cache_path.exists(),
            "hash": hashlib.sha256(input_string.encode('utf-8')).hexdigest()[:16]
        }
        
        return agent_config
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting avatar info: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "door-agent-avatars"}

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )