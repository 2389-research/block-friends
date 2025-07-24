# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ABOUTME: Sprite Maker generates 20×20 sprite sheets of customizable 'door agent' characters
ABOUTME: Single Python script that creates SVG and PNG outputs from configurable SVG assets

This is a Python sprite generation tool that creates procedurally generated "door agent" characters in a 20×20 grid. The project generates both SVG (vector) and PNG (raster) sprite sheets at 1200×1200 pixels.

## Dependencies and Setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management. Install dependencies:

```bash
uv sync
```

Dependencies are managed in `pyproject.toml` and include:
- `pillow` - For image processing (currently unused but available)

## Running the Generator

Execute the main generation script using uv:

```bash
uv run generate.py
```

This creates output files in `./out/`:
- `agents_sheet.svg` - Vector version (1200×1200)

## Expected Asset Structure

The generator expects SVG assets in specific directories:
```
assets/
  eyes/1.svg ... eyes/6.svg
  mouths/1.svg ... mouths/8.svg   (1-6 = rest, 7-8 = excited)
```

## Code Architecture

The single `generate.py` file contains several key functional areas:

### Configuration (lines 21-52)
- `CELL`, `PAD`, `BOX` - Grid and spacing constants
- `BODY_SHAPES` - Available width×height combinations for agent bodies
- `PALETTE` - Color choices for body and node fills
- Placement fractions for eyes, mouth, and nodes within body shapes

### SVG Asset Processing (lines 55-67)
- `parse_defs()` - Extracts viewBox and content from SVG files
- Loads eyes and mouths assets, sorts numerically by filename

### Agent Generation (lines 70-138)
- `agent_svg()` - Core function that generates individual agent SVG
- Handles body scaling, eye/mouth positioning, node placement, and feet
- Randomizes colors while avoiding body/node color conflicts
- Applies proper SVG transforms for asset placement

### Sheet Assembly (lines 141-162)
- Creates 400 agents (20×20 grid) with randomized properties
- 20% chance for "excited" state (uses different mouth asset)
- Outputs SVG format for scalable sprite sheets

## Key Design Patterns

- **Fractional positioning**: All element placement uses fractions of body dimensions for consistent scaling
- **Asset reuse**: Eyes and mouths are loaded once and transformed per agent
- **Randomization with constraints**: Colors are randomized but body/node colors are kept different
- **Scalable grid system**: Uses CELL/PAD constants for easy grid size adjustments