#!/usr/bin/env python3
"""
Generate a 20×20 sprite sheet of 'door agents'.

Folder layout expected:
  assets/
    eyes/1.svg ... eyes/6.svg
    mouths/1.svg ... mouths/8.svg   (1-6 = rest, 7-8 = excited)

Outputs to ./out/
  agents_sheet.svg   (vector, 1200×1200)

Install deps:
  uv sync
"""
import os, random, re, xml.etree.ElementTree as ET, csv, json
from pathlib import Path

# ───────────────────────── LOAD CONFIG ──────────────────────────
ASSETS = Path("assets")

# Load configuration files
with open(ASSETS/"config.json") as f:
    config = json.load(f)
with open(ASSETS/"colors.json") as f:
    colors = json.load(f)
with open(ASSETS/"body_shapes.json") as f:
    body_shapes = json.load(f)
with open(ASSETS/"probabilities.json") as f:
    probabilities = json.load(f)

# Extract configuration values
CELL = config["grid"]["cell_size"]
PAD = config["grid"]["padding"]
BOX = CELL - 2*PAD
STROKE = config["styling"]["stroke_width"]
OUTLINE = config["styling"]["outline_color"]

BODY_SHAPES = [(shape["width"], shape["height"]) for shape in body_shapes["shapes"]]

NODE_R_FRAC = config["sizing"]["node_radius_fraction"]
FOOT_H_FRAC = config["sizing"]["foot_height_fraction"]

EYE_Y_FRAC = config["positioning"]["eye_y_fraction"]
MOUTH_Y_FRAC = config["positioning"]["mouth_y_fraction"]
NODE_Y_FRAC = config["positioning"]["node_y_fraction"]

EYES_W_FRAC = config["sizing"]["eyes_width_fraction"]
MOUTH_W_REST = config["sizing"]["mouth_width_rest"]
MOUTH_W_EXC = config["sizing"]["mouth_width_excited"]

PALETTE = colors["palette"]

ROWS = config["grid"]["rows"]
COLS = config["grid"]["cols"]

# Probability settings
EXCITED_CHANCE = probabilities["excited_chance"]
FEET_MATCH_BODY_CHANCE = probabilities["feet_match_body_chance"]
REST_RANGE = probabilities["mouth_indices"]["rest_range"]
EXC_RANGE = probabilities["mouth_indices"]["excited_range"]

# Constraint settings from config
EYE_MAX_HEIGHT_FRAC = config["positioning"]["eye_max_height_fraction"]
MOUTH_MAX_HEIGHT_FRAC = config["positioning"]["mouth_max_height_fraction"]

OUT = Path("out"); OUT.mkdir(exist_ok=True)

# ───────────────────── SVG PART UTILITIES ───────────────────
def parse_defs(folder):
    """return [(x0,y0,w,h,svg_text,z_order,width_percent,position_x,position_y,anchor,color_spec), …] sorted numerically by filename"""
    defs = []
    for f in sorted(folder.glob("*.svg"), key=lambda p: int(p.stem)):
        root = ET.parse(f).getroot()
        x0,y0,w,h = map(float, root.get("viewBox").split())
        content = "".join(ET.tostring(c, encoding="unicode") for c in root)
        z_order = root.get("data-z-order", "behind")  # default to "behind" if not specified
        width_percent = float(root.get("data-width-percent", 100))  # default to 100% if not specified
        position_x = root.get("data-position-x", "body-center")  # default to "body-center" if not specified
        position_y = root.get("data-position-y", "above-body")  # default to "above-body" if not specified
        anchor = root.get("data-anchor", "top")  # default to "top" if not specified
        color_spec = root.get("data-color", "currentColor")  # default to "currentColor" if not specified
        defs.append((x0,y0,w,h,content,z_order,width_percent,position_x,position_y,anchor,color_spec))
    return defs

EYES   = parse_defs(ASSETS/"eyes")
MOUTHS = parse_defs(ASSETS/"mouths")
HAIRS  = parse_defs(ASSETS/"hair")

# ────────────────────── AGENT GENERATOR ─────────────────────
def agent_svg(shape, ei, excited, hi=None, return_config=False):
    w_tiles, h_tiles = shape
    # body size scaled so tallest shape (tile 7) exactly fills BOX-foot_h
    scale = (BOX - BOX*FOOT_H_FRAC) / 7
    body_w = int(w_tiles * scale)
    body_h = int(h_tiles * scale)
    foot_h = int(BOX * FOOT_H_FRAC)

    bx0 = PAD + (BOX - body_w)//2
    by0 = PAD + BOX - foot_h - body_h  # position body directly above feet
    bx1 = bx0 + body_w
    by1 = by0 + body_h
    cx  = (bx0 + bx1)/2

    body_fill = random.choice(PALETTE)
    node_fill = random.choice([c for c in PALETTE if c != body_fill])
    # sometimes make feet match body color instead of nodes
    feet_fill = body_fill if random.random() < FEET_MATCH_BODY_CHANCE else node_fill

    # ---- eyes ----
    ex0,ey0,ew,eh,eyes_svg,_,_,_,_,_,_ = EYES[ei]
    eyes_w = body_w * EYES_W_FRAC
    se     = eyes_w / ew
    eyes_h = eh * se
    # constrain eyes to fit within body bounds
    max_eyes_h = body_h * EYE_MAX_HEIGHT_FRAC
    if eyes_h > max_eyes_h:
        eyes_h = max_eyes_h
        se = eyes_h / eh
        eyes_w = ew * se
    eyes_x = cx - eyes_w/2
    # position based on eye center, then convert to top-left for SVG
    target_eye_center_y = by0 + body_h*EYE_Y_FRAC
    clamped_eye_center_y = max(by0 + eyes_h/2, min(by1 - eyes_h/2, target_eye_center_y))
    eyes_y = clamped_eye_center_y - eyes_h/2

    # ---- mouth ----
    if excited:
        mi = random.randint(EXC_RANGE[0], EXC_RANGE[1])
    else:
        mi = random.randint(REST_RANGE[0], REST_RANGE[1])
    mx0,my0,mw,mh,mouth_svg,_,_,_,_,_,_ = MOUTHS[mi]
    mw_ratio = MOUTH_W_EXC if excited else MOUTH_W_REST
    mouth_w  = body_w * mw_ratio
    sm       = mouth_w / mw
    mouth_h  = mh * sm
    # constrain mouth to fit within body bounds
    max_mouth_h = body_h * MOUTH_MAX_HEIGHT_FRAC
    if mouth_h > max_mouth_h:
        mouth_h = max_mouth_h
        sm = mouth_h / mh
        mouth_w = mw * sm
    mouth_x  = cx - mouth_w/2
    # position mouth halfway between bottom of eyes and body baseline
    eyes_bottom = clamped_eye_center_y + eyes_h/2
    target_mouth_center = (eyes_bottom + by1) / 2
    clamped_mouth_center_y = max(by0 + mouth_h/2, min(by1 - mouth_h/2, target_mouth_center))
    mouth_y  = clamped_mouth_center_y - mouth_h/2

    # ---- nodes ----
    node_r = int(body_w * NODE_R_FRAC)
    node_y = by0 + body_h*NODE_Y_FRAC
    # position so only node stroke overlaps body, not the fill
    left_node  = bx0 - node_r
    right_node = bx1 + node_r

    # ---- feet ----
    foot_w = int(body_w*0.26)
    left_foot  = cx - body_w/4  - foot_w/2
    right_foot = cx + body_w/4  - foot_w/2
    fy = PAD + BOX - foot_h     # bottom-aligned in 50×50 box

    g = []
    
    # Prepare hair rendering info if present
    hair_element = None
    if hi is not None:
        hx0,hy0,hw,hh,hair_svg,hair_z_order,hair_width_percent,hair_position_x,hair_position_y,hair_anchor,hair_color_spec = HAIRS[hi]
        
        # Calculate hair width based on SVG attribute
        hair_w = body_w * (hair_width_percent / 100)
        sh = hair_w / hw
        hair_h = hh * sh
        
        # Calculate hair X position based on SVG attribute - now unified with percentage support
        if hair_position_x == "cell-center":
            hair_x = PAD + BOX/2 - hair_w / 2  # center on cell center
        elif hair_position_x.endswith("%"):
            # Percentage positioning: "50%" means 50% of hair width from body center
            percent = float(hair_position_x[:-1]) / 100
            hair_x = cx + (hair_w * percent) - hair_w / 2
        else:  # default to "body-center"
            hair_x = cx - hair_w / 2  # center on body center
            
        # Calculate hair Y position based on SVG attribute - now unified with percentage support and anchoring
        if hair_position_y == "between-body-eyes":
            base_y = (by0 + eyes_y) / 2
        elif hair_position_y.endswith("%"):
            # Percentage positioning: "0%" means anchor point aligns with top of body, percentage is relative to hair height
            percent = float(hair_position_y[:-1]) / 100
            base_y = by0 + (hair_h * percent)
        else:  # default to "above-body"
            base_y = by0
            
        # Apply anchor offset to base position
        if hair_anchor == "bottom":
            hair_y = base_y - hair_h  # bottom of hair at base position
        elif hair_anchor == "center":
            hair_y = base_y - hair_h / 2  # center of hair at base position
        else:  # default to "top"
            hair_y = base_y  # top of hair at base position
            
        # Determine hair color based on data-color attribute
        if hair_color_spec == "currentColor":
            hair_color = body_fill
        elif hair_color_spec == "contrast":
            # Choose a contrasting color (different from body color)
            hair_color = random.choice([c for c in PALETTE if c != body_fill])
        elif hair_color_spec.startswith('[') and hair_color_spec.endswith(']'):
            # Parse JSON array of colors and choose randomly
            try:
                color_array = json.loads(hair_color_spec)
                hair_color = random.choice(color_array)
            except (json.JSONDecodeError, ValueError):
                hair_color = body_fill  # fallback to body color
        else:
            # Single hex color specified
            hair_color = hair_color_spec
            
        hair_element = f'<g color="{hair_color}" transform="translate({hair_x},{hair_y}) scale({sh}) translate({-hx0}, {-hy0})">{hair_svg}</g>'
        
        # Render hair behind body if specified
        if hair_z_order == "behind":
            g.append(hair_element)
    
    # body + divider
    g.append(f'<rect x="{bx0}" y="{by0}" width="{body_w}" height="{body_h}" '
             f'fill="{body_fill}" stroke="{OUTLINE}" stroke-width="{STROKE}"/>')
    g.append(f'<line x1="{cx}" y1="{by0}" x2="{cx}" y2="{by1}" '
             f'stroke="{OUTLINE}" stroke-width="{STROKE}"/>')
    # nodes
    for nx in (left_node,right_node):
        g.append(f'<circle cx="{nx}" cy="{node_y}" r="{node_r}" '
                 f'fill="{node_fill}" stroke="{OUTLINE}" stroke-width="{STROKE}"/>')
    # feet
    for fx in (left_foot,right_foot):
        g.append(f'<rect x="{fx}" y="{fy}" width="{foot_w}" height="{foot_h}" '
                 f'fill="{feet_fill}" stroke="{OUTLINE}" stroke-width="{STROKE}"/>')
    # eyes
    g.append(f'<g transform="translate({eyes_x},{eyes_y}) scale({se}) '
             f'translate({-ex0}, {-ey0})">{eyes_svg}</g>')
    # mouth
    g.append(f'<g transform="translate({mouth_x},{mouth_y}) scale({sm}) '
             f'translate({-mx0}, {-my0})">{mouth_svg}</g>')
    
    # Render hair in front of body if specified
    if hair_element and hi is not None:
        _,_,_,_,_,hair_z_order,_,_,_,_,_ = HAIRS[hi]
        if hair_z_order == "front":
            g.append(hair_element)
    
    if return_config:
        config = {
            'body_shape': f"{w_tiles}x{h_tiles}",
            'eye_index': ei + 1,  # 1-indexed for user friendliness
            'mouth_index': mi + 1,  # 1-indexed for user friendliness
            'hair_index': hi + 1 if hi is not None else None,  # 1-indexed for user friendliness
            'excited': excited,
            'body_color': body_fill,
            'node_color': node_fill,
            'feet_color': feet_fill,
            'feet_match_body': feet_fill == body_fill
        }
        return "".join(g), config
    return "".join(g)

# ─────────────────────  BUILD SHEET  ────────────────────────
cells = []
agent_configs = []
agent_id = 0

for r in range(ROWS):
    for c in range(COLS):
        shape   = random.choice(BODY_SHAPES)
        ei      = random.randrange(len(EYES))
        excited = random.random() < EXCITED_CHANCE
        hi      = 11  # Only hair #12 for testing
        
        svg_content, agent_config = agent_svg(shape, ei, excited, hi, return_config=True)
        agent_config['agent_id'] = agent_id
        agent_config['row'] = r
        agent_config['col'] = c
        agent_config['x'] = c * CELL
        agent_config['y'] = r * CELL
        
        cells.append(f'<g transform="translate({c*CELL},{r*CELL})">{svg_content}</g>')
        agent_configs.append(agent_config)
        agent_id += 1

W, H = COLS*CELL, ROWS*CELL
sheet_svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
             f'viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="none"/>'
             + "".join(cells) + '</svg>')

svg_path = OUT/config["output"]["svg_filename"]
csv_path = OUT/config["output"]["csv_filename"]
css_path = OUT/config["output"]["css_filename"]

svg_path.write_text(sheet_svg)

# Write agent configuration CSV
with open(csv_path, 'w', newline='') as csvfile:
    fieldnames = ['agent_id', 'row', 'col', 'x', 'y', 'body_shape', 'eye_index', 
                  'mouth_index', 'hair_index', 'excited', 'body_color', 'node_color', 'feet_color', 
                  'feet_match_body']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(agent_configs)

# Write CSS sprite file
css_content = f"""/* Door Agent Sprite Sheet CSS */
/* Generated sprite sheet: {W}×{H} pixels, {CELL}×{CELL}px cells */

.sprite {{
    display: inline-block;
    width: {CELL}px;
    height: {CELL}px;
    background-image: url('agents_sheet.svg');
    background-repeat: no-repeat;
    background-size: {W}px {H}px;
}}

/* Individual agent positions */
"""

for agent_config in agent_configs:
    css_content += f".agent-{agent_config['agent_id']} {{ background-position: -{agent_config['x']}px -{agent_config['y']}px; }}\n"

css_path.write_text(css_content)

print("✅  Generated:")
print("   •", svg_path)
print("   •", csv_path)
print("   •", css_path)
