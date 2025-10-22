#!/usr/bin/env python3
# ABOUTME: FastAPI web app serving deterministic door agent avatars at /avatar/[hash].svg
# ABOUTME: Supports both hash and raw string inputs with file-based caching for performance

import hashlib
import logging
import asyncio
import json
import zipfile
import io
from pathlib import Path
from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uvicorn
import cairosvg
from PyPDF2 import PdfWriter, PdfReader

from door_agents import DoorAgentConfig, DoorAgentGenerator, AVATAR_SYSTEM_VERSION

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="2389 Agent Avatar Service",
    description="Deterministic avatar generation service with 1.27 billion unique variants",
    version="1.0.0"
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Initialize the door agent system
config = DoorAgentConfig()
generator = DoorAgentGenerator(config)

# Cache directories
CACHE_DIR = Path("out/avatar")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR_PNG = Path("out/avatar_png")
CACHE_DIR_PNG.mkdir(parents=True, exist_ok=True)

# Static files directory
STATIC_DIR = Path("static")
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Assets directory
ASSETS_DIR = Path("assets")

# Global lock for file operations to prevent race conditions
file_write_lock = asyncio.Lock()

# Mount static files and assets
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# Pydantic models for request bodies
class BundleRequest(BaseModel):
    """Request model for PDF bundle generation."""
    input: str
    animations: List[str] = ["idle", "emotes", "vowels"]

async def get_or_generate_avatar_content(input_string: str, frame: str = "neutral", universal: bool = True) -> tuple[str, str]:
    """
    Gets avatar SVG content from file cache or generates it, ensuring thread-safety.
    Returns (svg_content, hash_hex) tuple.

    Args:
        input_string: Input string for deterministic generation
        frame: Animation frame (default: "neutral")
        universal: If True, generate universal SVG with all states (default: True)
    """
    hash_hex = hashlib.sha256(input_string.encode('utf-8')).hexdigest()[:16]
    # Include frame and universal mode in cache key for frame-specific caching
    cache_suffix = f"_{frame}" if frame != "neutral" else ""
    cache_suffix += "_legacy" if not universal else ""
    cache_key = f"{hash_hex}{cache_suffix}"
    cache_path = CACHE_DIR / f"{cache_key}.svg"

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

        # Generate new avatar with frame and universal parameters
        svg_content_raw, _ = generator.generate_deterministic(input_string, frame=frame, universal=universal)

        # Only wrap in container for legacy mode
        # Universal mode has ID and CSS rules that need to be on the root <svg>
        if universal:
            full_svg = svg_content_raw
        else:
            # Legacy mode: wrap in properly sized container
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

async def get_or_generate_avatar_png(input_string: str, frame: str = "neutral", universal: bool = True) -> tuple[bytes, str]:
    """
    Gets avatar PNG content from file cache or generates it from SVG, ensuring thread-safety.
    Returns (png_bytes, hash_hex) tuple.

    Args:
        input_string: Input string for deterministic generation
        frame: Animation frame (default: "neutral")
        universal: If True, generate universal SVG with all states (default: True)
    """
    hash_hex = hashlib.sha256(input_string.encode('utf-8')).hexdigest()[:16]
    # Include frame and universal mode in cache key for frame-specific caching
    cache_suffix = f"_{frame}" if frame != "neutral" else ""
    cache_suffix += "_legacy" if not universal else ""
    cache_key = f"{hash_hex}{cache_suffix}"
    cache_path = CACHE_DIR_PNG / f"{cache_key}.png"

    # Try to read from PNG cache first
    if cache_path.exists():
        try:
            png_content = await asyncio.to_thread(cache_path.read_bytes)
            logger.info(f"PNG cache hit for {hash_hex}")
            return png_content, hash_hex
        except IOError as e:
            logger.error(f"Error reading cached PNG {cache_path}: {e}")
            # Proceed to generate if read fails

    logger.info(f"PNG cache miss for {hash_hex}, converting from SVG")

    # Get SVG content (which may be cached), passing through the frame and universal parameters
    svg_content, hash_hex = await get_or_generate_avatar_content(input_string, frame=frame, universal=universal)

    # Generate and cache PNG with lock to prevent race conditions
    async with file_write_lock:
        # Double-check if another worker generated it while waiting for lock
        if cache_path.exists():
            try:
                png_content = await asyncio.to_thread(cache_path.read_bytes)
                logger.info(f"PNG cache hit after lock for {hash_hex}")
                return png_content, hash_hex
            except IOError as e:
                logger.error(f"Error reading cached PNG after lock {cache_path}: {e}")

        # Convert SVG to PNG
        try:
            png_bytes = await asyncio.to_thread(
                cairosvg.svg2png,
                bytestring=svg_content.encode('utf-8'),
                output_width=config.CELL,
                output_height=config.CELL
            )
        except Exception as e:
            logger.error(f"Error converting SVG to PNG for {hash_hex}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to convert SVG to PNG: {e}")

        # Cache to file with error handling
        try:
            await asyncio.to_thread(cache_path.write_bytes, png_bytes)
            logger.info(f"PNG avatar cached to {cache_path}")
        except IOError as e:
            logger.error(f"Failed to write PNG to cache {cache_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to write PNG to cache: {e}")

        return png_bytes, hash_hex

async def svg_to_pdf(svg_content: str) -> bytes:
    """Convert SVG content to PDF bytes using CairoSVG."""
    try:
        pdf_bytes = await asyncio.to_thread(
            cairosvg.svg2pdf,
            bytestring=svg_content.encode('utf-8')
        )
        return pdf_bytes
    except Exception as e:
        logger.error(f"Error converting SVG to PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to convert SVG to PDF: {e}")

async def generate_pdf_bundle(input_string: str, animations: List[str]) -> bytes:
    """
    Generate a ZIP bundle containing PDF animations and metadata.

    Args:
        input_string: Input string for deterministic generation
        animations: List of animation types to include ("idle", "emotes", "vowels")

    Returns:
        ZIP file bytes containing PDFs and metadata.json
    """
    hash_hex = hashlib.sha256(input_string.encode('utf-8')).hexdigest()[:16]

    # Define frame sequences for each animation type
    frame_sequences = {
        "idle": {
            "frames": ["idle_0", "idle_1", "idle_2", "idle_3"],
            "fps": 4,
            "loop": True
        },
        "emotes": {
            "happy": ["happy"],
            "sad": ["sad"],
            "surprised": ["surprised"],
            "angry": ["angry"],
            "bored": ["bored"]
        },
        "vowels": {
            "A": ["vowel_A"],
            "E": ["vowel_E"],
            "I": ["vowel_I"],
            "O": ["vowel_O"],
            "U": ["vowel_U"]
        }
    }

    # Create ZIP in memory
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Metadata for the bundle
        metadata = {
            "input": input_string,
            "hash": hash_hex,
            "animations": {}
        }

        # Generate idle animation if requested
        if "idle" in animations:
            idle_writer = PdfWriter()

            for frame in frame_sequences["idle"]["frames"]:
                # Get SVG content
                svg_content, _ = await get_or_generate_avatar_content(input_string, frame=frame)

                # Convert to PDF
                pdf_bytes = await svg_to_pdf(svg_content)

                # Add page to PDF
                pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
                idle_writer.add_page(pdf_reader.pages[0])

            # Write idle PDF to ZIP
            idle_pdf_buffer = io.BytesIO()
            idle_writer.write(idle_pdf_buffer)
            idle_pdf_buffer.seek(0)
            zip_file.writestr("idle.pdf", idle_pdf_buffer.read())

            metadata["animations"]["idle"] = {
                "file": "idle.pdf",
                "frame_count": len(frame_sequences["idle"]["frames"]),
                "fps": frame_sequences["idle"]["fps"],
                "loop": frame_sequences["idle"]["loop"]
            }

        # Generate emotes if requested
        if "emotes" in animations:
            for emote_name, frames in frame_sequences["emotes"].items():
                emote_writer = PdfWriter()

                for frame in frames:
                    svg_content, _ = await get_or_generate_avatar_content(input_string, frame=frame)
                    pdf_bytes = await svg_to_pdf(svg_content)
                    pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
                    emote_writer.add_page(pdf_reader.pages[0])

                emote_pdf_buffer = io.BytesIO()
                emote_writer.write(emote_pdf_buffer)
                emote_pdf_buffer.seek(0)
                zip_file.writestr(f"emote_{emote_name}.pdf", emote_pdf_buffer.read())

            metadata["animations"]["emotes"] = {
                "files": {name: f"emote_{name}.pdf" for name in frame_sequences["emotes"].keys()},
                "count": len(frame_sequences["emotes"])
            }

        # Generate vowels if requested
        if "vowels" in animations:
            for vowel, frames in frame_sequences["vowels"].items():
                vowel_writer = PdfWriter()

                for frame in frames:
                    svg_content, _ = await get_or_generate_avatar_content(input_string, frame=frame)
                    pdf_bytes = await svg_to_pdf(svg_content)
                    pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
                    vowel_writer.add_page(pdf_reader.pages[0])

                vowel_pdf_buffer = io.BytesIO()
                vowel_writer.write(vowel_pdf_buffer)
                vowel_pdf_buffer.seek(0)
                zip_file.writestr(f"vowel_{vowel}.pdf", vowel_pdf_buffer.read())

            metadata["animations"]["vowels"] = {
                "files": {vowel: f"vowel_{vowel}.pdf" for vowel in frame_sequences["vowels"].keys()},
                "count": len(frame_sequences["vowels"])
            }

        # Write metadata JSON
        zip_file.writestr("metadata.json", json.dumps(metadata, indent=2))

    zip_buffer.seek(0)
    return zip_buffer.read()

@app.get("/")
async def root():
    """Serve the landing page."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text())

    # Fallback to JSON if HTML doesn't exist
    return {
        "service": "2389 Agent Avatar Service",
        "version": "1.0.0",
        "avatar_system_version": AVATAR_SYSTEM_VERSION,
        "description": "Deterministic avatar generation with 1.27B unique variants",
        "endpoints": {
            "version": "/version",
            "avatar_svg": "/avatar/{input}.svg",
            "avatar_png": "/avatar/{input}.png",
            "bundle": "/avatar/{input}/bundle"
        },
        "usage": {
            "examples": [
                "/avatar/test@example.com.svg",
                "/avatar/test@example.com.png",
                "/avatar/973dfe463ec85785.svg",
                "/avatar/973dfe463ec85785.png"
            ]
        },
        "features": [
            "Deterministic generation from any input string",
            "SVG and PNG format support",
            "File-based caching for performance",
            "1.27 billion unique variants",
            "Collision-resistant for ~1M users",
            "Version tracking via /version endpoint and X-Avatar-System-Version header"
        ]
    }

@app.get("/animations.html")
async def animations():
    """Serve the animations documentation page."""
    animations_path = STATIC_DIR / "animations.html"
    if animations_path.exists():
        return HTMLResponse(content=animations_path.read_text())
    raise HTTPException(status_code=404, detail="Animations page not found")

@app.get("/sitemap.html")
async def sitemap():
    """Serve the sitemap page."""
    sitemap_path = STATIC_DIR / "sitemap.html"
    if sitemap_path.exists():
        return HTMLResponse(content=sitemap_path.read_text())
    raise HTTPException(status_code=404, detail="Sitemap page not found")

@app.get("/avatar/{input_param}.svg")
async def get_avatar(input_param: str, frame: str = "neutral", legacy: bool = False):
    """
    Generate and serve avatar SVG for given input.

    - **input_param**: Any string (email, username, hash, etc.)
    - **frame**: Animation frame (default: "neutral")
        - Options: "neutral", "idle_0" through "idle_3",
                  "happy", "sad", "surprised", "angry", "bored",
                  "vowel_A", "vowel_E", "vowel_I", "vowel_O", "vowel_U"
    - **legacy**: If true, use legacy single-frame mode (default: false for universal mode)
    - Returns SVG image with proper content-type headers
    - Cached results are served immediately for performance
    """
    try:
        # Convert legacy parameter to universal (universal = not legacy)
        universal = not legacy

        # Get or generate avatar content with consistent hash, frame, and universal mode
        svg_content, hash_hex = await get_or_generate_avatar_content(input_param, frame=frame, universal=universal)

        # Consistent ETag generation from canonical hash
        etag = f'"{hash_hex}"'

        return Response(
            content=svg_content,
            media_type="image/svg+xml",
            headers={
                "Cache-Control": "public, max-age=31536000, immutable",
                "ETag": etag,
                "X-Avatar-System-Version": AVATAR_SYSTEM_VERSION
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unhandled error in get_avatar for {input_param}")
        raise HTTPException(status_code=500, detail=f"Error generating avatar: {str(e)}")

@app.get("/avatar/{input_param}.png")
async def get_avatar_png(input_param: str, frame: str = "neutral", legacy: bool = False):
    """
    Generate and serve avatar PNG for given input.

    - **input_param**: Any string (email, username, hash, etc.)
    - **frame**: Animation frame (default: "neutral")
        - Options: "neutral", "idle_0" through "idle_3",
                  "happy", "sad", "surprised", "angry", "bored",
                  "vowel_A", "vowel_E", "vowel_I", "vowel_O", "vowel_U"
    - **legacy**: If true, use legacy single-frame mode (default: false for universal mode)
    - Returns PNG image with proper content-type headers
    - Cached results are served immediately for performance
    """
    try:
        # Convert legacy parameter to universal (universal = not legacy)
        universal = not legacy

        # Get or generate PNG content with consistent hash, frame, and universal mode
        png_content, hash_hex = await get_or_generate_avatar_png(input_param, frame=frame, universal=universal)

        # Consistent ETag generation from canonical hash
        etag = f'"{hash_hex}"'

        return Response(
            content=png_content,
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=31536000, immutable",
                "ETag": etag,
                "X-Avatar-System-Version": AVATAR_SYSTEM_VERSION
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unhandled error in get_avatar_png for {input_param}")
        raise HTTPException(status_code=500, detail=f"Error generating PNG avatar: {str(e)}")

@app.get("/avatar/{input_param}.svg/info")
async def get_avatar_info(input_param: str, frame: str = "neutral"):
    """
    Get configuration information for an avatar without generating the image.

    - **input_param**: Any string (email, username, hash, etc.)
    - **frame**: Animation frame (default: "neutral")
    - Returns JSON with avatar configuration details
    """
    try:
        # Calculate hash once
        hash_hex = hashlib.sha256(input_param.encode('utf-8')).hexdigest()[:16]

        # Generate avatar config with frame parameter (but don't cache the SVG)
        _, agent_config = generator.generate_deterministic(input_param, frame=frame)

        # Add cache info
        cache_key = f"{hash_hex}_{frame}" if frame != "neutral" else hash_hex
        cache_path = CACHE_DIR / f"{cache_key}.svg"
        agent_config["cache_info"] = {
            "cache_path": str(cache_path),
            "cached": cache_path.exists(),
            "hash": hash_hex,
            "cache_key": cache_key
        }

        return agent_config

    except Exception as e:
        logger.exception(f"Unhandled error in get_avatar_info for {input_param}")
        raise HTTPException(status_code=500, detail=f"Error getting avatar info: {str(e)}")

@app.get("/avatar/{input_param}.svg/frames")
async def get_avatar_frames(input_param: str):
    """
    Get available animation frames for an avatar.

    - **input_param**: Any string (email, username, hash, etc.)
    - Returns JSON with frame definitions and URLs for all available animations
    """
    try:
        hash_hex = hashlib.sha256(input_param.encode('utf-8')).hexdigest()[:16]

        frames_info = {
            "input": input_param,
            "hash": hash_hex,
            "frames": {
                "neutral": {
                    "description": "Default neutral state",
                    "frame_count": 1,
                    "frames": ["neutral"],
                    "urls": {
                        "svg": f"/avatar/{input_param}.svg",
                        "png": f"/avatar/{input_param}.png"
                    }
                },
                "idle": {
                    "description": "Breathing animation loop",
                    "frame_count": 4,
                    "frames": ["idle_0", "idle_1", "idle_2", "idle_3"],
                    "fps": 4,
                    "urls": {
                        "svg": [f"/avatar/{input_param}.svg?frame=idle_{i}" for i in range(4)],
                        "png": [f"/avatar/{input_param}.png?frame=idle_{i}" for i in range(4)]
                    }
                },
                "emotes": {
                    "description": "Emotional expressions",
                    "frame_count": 5,
                    "frames": ["happy", "sad", "surprised", "angry", "bored"],
                    "urls": {
                        "svg": {emote: f"/avatar/{input_param}.svg?frame={emote}"
                               for emote in ["happy", "sad", "surprised", "angry", "bored"]},
                        "png": {emote: f"/avatar/{input_param}.png?frame={emote}"
                               for emote in ["happy", "sad", "surprised", "angry", "bored"]}
                    }
                },
                "vowels": {
                    "description": "Mouth shapes for lip-sync (A, E, I, O, U)",
                    "frame_count": 5,
                    "frames": ["vowel_A", "vowel_E", "vowel_I", "vowel_O", "vowel_U"],
                    "urls": {
                        "svg": {vowel: f"/avatar/{input_param}.svg?frame=vowel_{vowel}"
                               for vowel in ["A", "E", "I", "O", "U"]},
                        "png": {vowel: f"/avatar/{input_param}.png?frame=vowel_{vowel}"
                               for vowel in ["A", "E", "I", "O", "U"]}
                    }
                }
            },
            "total_frames": 15
        }

        return frames_info

    except Exception as e:
        logger.exception(f"Unhandled error in get_avatar_frames for {input_param}")
        raise HTTPException(status_code=500, detail=f"Error getting avatar frames: {str(e)}")

@app.get("/avatar/{input_param}/bundle")
async def get_avatar_bundle(input_param: str, animations: str = "idle,emotes,vowels"):
    """
    Generate a ZIP bundle containing PDF animations for an avatar via GET request.

    - **input_param**: Any string (email, username, hash, etc.)
    - **animations**: Comma-separated list of animation types (default: "idle,emotes,vowels")

    Returns a ZIP file containing:
    - idle.pdf (4-frame breathing animation)
    - emote_[name].pdf (5 emotional expressions)
    - vowel_[letter].pdf (5 vowel mouth shapes)
    - metadata.json (animation specifications)
    """
    try:
        # Parse comma-separated animations
        animation_list = [a.strip() for a in animations.split(",")]
        logger.info(f"Generating PDF bundle for {input_param} with animations: {animation_list}")

        # Generate the bundle
        zip_bytes = await generate_pdf_bundle(input_param, animation_list)

        # Calculate hash for filename
        hash_hex = hashlib.sha256(input_param.encode('utf-8')).hexdigest()[:16]
        filename = f"avatar_{hash_hex}_animations.zip"

        return StreamingResponse(
            io.BytesIO(zip_bytes),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Avatar-System-Version": AVATAR_SYSTEM_VERSION
            }
        )

    except Exception as e:
        logger.exception(f"Error generating PDF bundle for {input_param}")
        raise HTTPException(status_code=500, detail=f"Error generating PDF bundle: {str(e)}")

@app.post("/avatar/bundle")
async def create_avatar_bundle(request: BundleRequest):
    """
    Generate a ZIP bundle containing PDF animations for an avatar via POST request.

    - **input**: Any string (email, username, hash, etc.)
    - **animations**: List of animation types to include (default: ["idle", "emotes", "vowels"])

    Returns a ZIP file containing:
    - idle.pdf (4-frame breathing animation)
    - emote_[name].pdf (5 emotional expressions)
    - vowel_[letter].pdf (5 vowel mouth shapes)
    - metadata.json (animation specifications)
    """
    try:
        logger.info(f"Generating PDF bundle for {request.input} with animations: {request.animations}")

        # Generate the bundle
        zip_bytes = await generate_pdf_bundle(request.input, request.animations)

        # Calculate hash for filename
        hash_hex = hashlib.sha256(request.input.encode('utf-8')).hexdigest()[:16]
        filename = f"avatar_{hash_hex}_animations.zip"

        return StreamingResponse(
            io.BytesIO(zip_bytes),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Avatar-System-Version": AVATAR_SYSTEM_VERSION
            }
        )

    except Exception as e:
        logger.exception(f"Error generating PDF bundle for {request.input}")
        raise HTTPException(status_code=500, detail=f"Error generating PDF bundle: {str(e)}")

@app.get("/version")
async def get_version():
    """Return the avatar system version."""
    return {"avatar_system_version": AVATAR_SYSTEM_VERSION}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "door-agent-avatars"}

@app.get("/debug/avatar/{input_param}")
async def debug_avatar(input_param: str):
    """Debug endpoint showing which assets are assigned to an avatar."""
    svg, info = generator.generate_deterministic(input_param, frame='neutral')

    return {
        "input": input_param,
        "assets": {
            "open_eye": f"assets/eyes/open/{info['open_eye_index']}.svg",
            "closed_eye": f"assets/eyes/closed/{info['closed_eye_index']}.svg",
            "open_mouth": f"assets/mouths/open/{info['open_mouth_index']}.svg",
            "closed_mouth": f"assets/mouths/closed/{info['closed_mouth_index']}.svg",
            "hair": f"assets/hair/{info['hair_index']}.svg" if info['hair_index'] else None
        },
        "full_config": info
    }

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )