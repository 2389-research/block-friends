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
  hair/1.svg ... hair/n.svg       (with positioning data attributes)
```

## Code Architecture

The single `generate.py` file contains several key functional areas:

### Configuration (lines 21-52)
- `CELL`, `PAD`, `BOX` - Grid and spacing constants
- `BODY_SHAPES` - Available width×height combinations for agent bodies
- `PALETTE` - Color choices for body and node fills
- Placement fractions for eyes, mouth, and nodes within body shapes

### SVG Asset Processing (lines 55-67)
- `parse_defs()` - Extracts viewBox, content, and positioning data attributes from SVG files
- Loads eyes, mouths, and hair assets, sorts numerically by filename
- Parses hair positioning attributes: offset-y, z-order, width-percent, position-x, position-y

### Agent Generation (lines 70-138)
- `agent_svg()` - Core function that generates individual agent SVG
- Handles body scaling, eye/mouth/hair positioning, node placement, and feet
- Randomizes colors while avoiding body/node color conflicts
- Applies proper SVG transforms for asset placement
- Supports hair z-order rendering (behind/front) and flexible positioning

### Sheet Assembly (lines 141-162)
- Creates 400 agents (20×20 grid) with randomized properties
- 20% chance for "excited" state (uses different mouth asset)
- Outputs SVG format for scalable sprite sheets

## Key Design Patterns

- **Fractional positioning**: All element placement uses fractions of body dimensions for consistent scaling
- **Asset reuse**: Eyes, mouths, and hair are loaded once and transformed per agent
- **Data-driven positioning**: Hair assets use SVG data attributes for self-contained positioning logic
- **Randomization with constraints**: Colors are randomized but body/node colors are kept different
- **Scalable grid system**: Uses CELL/PAD constants for easy grid size adjustments

## Hair Asset System

The hair system uses SVG data attributes for flexible positioning:

### Supported Data Attributes

- `data-z-order`: Render order - "behind" (default) or "front"
- `data-width-percent`: Width as percentage of body width (default: 100)
- `data-position-x`: Unified positioning - special cases ("body-center", "cell-center") or percentages ("25%") for % across cell width (default: "body-center")
- `data-position-y`: Unified positioning - special cases ("above-body", "between-body-eyes") or percentages ("25%") for % down from body top (default: "above-body")
- `data-anchor`: Which part of hair aligns with position - "top", "center", or "bottom" (default: "top")
- `data-color`: Color strategy - "currentColor", "contrast", hex colors like "#FF0000", or JSON arrays like ["#FF0000", "#00FF00"] (default: "currentColor")

### Example Hair Asset

```xml
<svg data-z-order="front" 
     data-width-percent="112" 
     data-position-x="cell-center" 
     data-position-y="between-body-eyes"
     data-anchor="center"
     data-color='["#F7C0A9", "#FFC2E2", "#F7CF47"]'>
  <path fill="currentColor" d="..." stroke="#231F20" stroke-width="0.75"/>
</svg>
```

### Color System

- `"currentColor"`: Inherits agent's body color
- `"contrast"`: Uses random color different from body color  
- `"#RRGGBB"`: Specific hex color
- `["#color1", "#color2", ...]`: JSON array for random color selection

All paths should use `fill="currentColor"` and `stroke-width="0.75"` for consistency.

## Development Workflow

### Testing Individual Hair Styles

To test a specific hair asset during development:

1. Edit `generate.py` line ~277: `hi = X  # Only hair #(X+1) for testing`
2. Run `uv run generate.py` to regenerate with only that hair
3. Adjust positioning attributes in the hair SVG file
4. Repeat until positioning is correct

### Current Hair Assets

- **Hair #1**: Cat ears (behind, 7% position-y, body colors)
- **Hair #2**: Emo hair (front, between-body-eyes, colored array)
- **Hair #3**: Short hair (front, -6% position-y, dark colors)
- **Hair #4**: Curly hair (front, 50% position-y, light colors)
- **Hair #5**: Bunny ears (behind, 22% position-y, body colors)
- **Hair #6**: Baby hair stroke (behind, 7% position-y, 30% width, body colors)
- **Hair #7**: Ghost hair (front, -80% position-y, combined color palette)
- **Hair #8**: Leaves (front, 8% position-y, green colors only)
- **Hair #9**: Bow (front, -10% position-y, bright colors)
- **Hair #10+**: Additional styles with various positioning