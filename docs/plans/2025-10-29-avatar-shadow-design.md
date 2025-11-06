# Avatar Shadow Design

**Date:** 2025-10-29
**Status:** Approved for implementation

## Overview

Add a ground shadow to each avatar for depth and visual grounding. The shadow is a soft-edged ellipse positioned at the bottom of the avatar, scaling with the actual rendered content width (body + hair + nodes).

## Requirements

- Shadow scales with actual content width (not fixed viewBox size)
- Positioned to overlap feet slightly for depth effect
- Renders behind all other elements
- Strong opacity (0.4-0.5) for clear presence
- Soft edges via gaussian blur
- Light grey color with transparency

## Design Decisions

### Shadow Geometry

**Shape:** Ellipse (short, wide oval)

**Dimensions:**
- Width: `content_width * 1.2` (20% wider than actual content)
- Height: `content_width * 0.15` (short, flat ground shadow)
- Center X: `content_center_x` (horizontally centered on content)
- Center Y: `CELL - 3` (3px overlap with feet)

**Visual Properties:**
- Fill: Light grey (`#808080`)
- Opacity: `0.45`
- Gaussian blur: `stdDeviation="1.5"`

### Bounding Box Calculation

Track content boundaries as elements are generated:

```python
# Initialize bounds
min_x = float('inf')
max_x = float('-inf')

# Update as elements added:
# - Body: bx0 (left), bx1 (right)
# - Hair: position + width from data attributes
# - Nodes: x positions
# - Feet: relative to body

# Calculate final dimensions
content_width = max_x - min_x
content_center_x = (min_x + max_x) / 2
```

### SVG Filter Implementation

**Filter Definition:**
```xml
<defs>
  <filter id="{avatar_id}-shadow-blur">
    <feGaussianBlur in="SourceGraphic" stdDeviation="1.5"/>
  </filter>
</defs>
```

**Filter Application:**
```xml
<ellipse
  cx="{shadow_cx}"
  cy="{shadow_cy}"
  rx="{shadow_width/2}"
  ry="{shadow_height/2}"
  fill="#808080"
  opacity="0.45"
  filter="url(#{avatar_id}-shadow-blur)"/>
```

**Namespacing:** Filter ID includes avatar_id to prevent conflicts (matches existing clipPath pattern).

## Implementation

### Code Location

Primary changes in `door_agents.py`, `generate()` method (lines ~1067-1142).

### Integration Flow

1. **Initialize bounds tracking** at start of generation
2. **Track bounds** as each element is generated:
   - Body rectangle
   - Hair positioning
   - Node positions
3. **Calculate shadow dimensions** from final bounds
4. **Build filter definition** in `<defs>` section
5. **Insert shadow ellipse** as first element after `<defs>`

### Rendering Order

```
<svg>
  <defs>
    {existing clipPaths}
    {shadow blur filter}
  </defs>
  {shadow ellipse}      ← NEW (behind everything)
  {body rectangle}
  {vertical line}
  {nodes}
  {feet}
  {hair-behind}
  {eyes}
  {mouths}
  {hair-front}
</svg>
```

### Universal vs Legacy Mode

- Shadow appears in both modes
- Same calculation and rendering logic
- Filter namespacing works with existing avatar_id system

## Success Criteria

- Shadow scales correctly with wide hair vs narrow hair
- Shadow has soft edges (blur visible)
- Shadow renders behind all elements
- Shadow overlaps feet by ~3px
- Opacity clearly visible but not opaque
- No filter ID conflicts in multi-avatar pages
