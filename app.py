#!/usr/bin/env python3
# ABOUTME: FastAPI web app serving deterministic door agent avatars at /avatar/[hash].svg
# ABOUTME: Supports both hash and raw string inputs with file-based caching for performance

import hashlib
import logging
import asyncio
from pathlib import Path
from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from door_agents import DoorAgentConfig, DoorAgentGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="2389 Agent Avatar Service",
    description="Deterministic avatar generation service with 1.27 billion unique variants",
    version="1.0.0"
)

# Initialize the door agent system
config = DoorAgentConfig()
generator = DoorAgentGenerator(config)

# Cache directory
CACHE_DIR = Path("out/avatar")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Static files directory
STATIC_DIR = Path("static")
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Global lock for file operations to prevent race conditions
file_write_lock = asyncio.Lock()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

async def get_or_generate_avatar_content(input_string: str) -> tuple[str, str]:
    """
    Gets avatar SVG content from file cache or generates it, ensuring thread-safety.
    Returns (svg_content, hash_hex) tuple.
    """
    hash_hex = hashlib.sha256(input_string.encode('utf-8')).hexdigest()[:16]
    cache_path = CACHE_DIR / f"{hash_hex}.svg"

    # Try to read from file cache first
    if cache_path.exists():
        try:
            svg_content = await asyncio.to_thread(cache_path.read_text)
            logger.info(f"Cache hit for {hash_hex}")
            return svg_content, hash_hex
        except IOError as e:
            logger.error(f"Error reading cached avatar {cache_path}: {e}")
            # Proceed to generate if read fails

    logger.info(f"Cache miss for {hash_hex}, generating avatar")

    # Generate and cache with lock to prevent race conditions
    async with file_write_lock:
        # Double-check if another worker generated it while waiting for lock
        if cache_path.exists():
            try:
                svg_content = await asyncio.to_thread(cache_path.read_text)
                logger.info(f"Cache hit after lock for {hash_hex}")
                return svg_content, hash_hex
            except IOError as e:
                logger.error(f"Error reading cached avatar after lock {cache_path}: {e}")

        # Generate new avatar
        svg_content_raw, _ = generator.generate_deterministic(input_string)

        # Wrap in properly sized container
        cell_size = config.CELL
        full_svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{cell_size}" height="{cell_size}" '
                    f'viewBox="0 0 {cell_size} {cell_size}">'
                    f'<rect width="100%" height="100%" fill="none"/>'
                    f'{svg_content_raw}</svg>')

        # Cache to file with error handling
        try:
            await asyncio.to_thread(cache_path.write_text, full_svg)
            logger.info(f"Avatar cached to {cache_path}")
        except IOError as e:
            logger.error(f"Failed to write avatar to cache {cache_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to write avatar to cache: {e}")

        return full_svg, hash_hex

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the landing page."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text())

    # Fallback to JSON if HTML doesn't exist
    return {
        "service": "2389 Agent Avatar Service",
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

    - **input_param**: Any string (email, username, hash, etc.)
    - Returns SVG image with proper content-type headers
    - Cached results are served immediately for performance
    """
    try:
        # Get or generate avatar content with consistent hash
        svg_content, hash_hex = await get_or_generate_avatar_content(input_param)

        # Consistent ETag generation from canonical hash
        etag = f'"{hash_hex}"'

        return Response(
            content=svg_content,
            media_type="image/svg+xml",
            headers={
                "Cache-Control": "public, max-age=31536000, immutable",
                "ETag": etag
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unhandled error in get_avatar for {input_param}")
        raise HTTPException(status_code=500, detail=f"Error generating avatar: {str(e)}")

@app.get("/avatar/{input_param}.svg/info")
async def get_avatar_info(input_param: str):
    """
    Get configuration information for an avatar without generating the image.

    - **input_param**: Any string (email, username, hash, etc.)
    - Returns JSON with avatar configuration details
    """
    try:
        # Calculate hash once
        hash_hex = hashlib.sha256(input_param.encode('utf-8')).hexdigest()[:16]

        # Generate avatar config (but don't cache the SVG)
        _, agent_config = generator.generate_deterministic(input_param)

        # Add cache info
        cache_path = CACHE_DIR / f"{hash_hex}.svg"
        agent_config["cache_info"] = {
            "cache_path": str(cache_path),
            "cached": cache_path.exists(),
            "hash": hash_hex
        }

        return agent_config

    except Exception as e:
        logger.exception(f"Unhandled error in get_avatar_info for {input_param}")
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