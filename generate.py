#!/usr/bin/env python3
"""
Generate a 20×20 sprite sheet of 'door agents'.

Folder layout expected:
  assets/
    eyes/
      open/1.svg ... 6.svg
      closed/1.svg ... 6.svg
    mouths/
      open/1.svg ... 8.svg
      closed/1.svg ... 8.svg

Outputs to ./out/
  agents_sheet.svg   (vector, 1200×1200)

Install deps:
  uv sync
"""
import csv
from pathlib import Path
from door_agents import DoorAgentConfig, DoorAgentGenerator

# ───────────────────────── LOAD CONFIG ──────────────────────────
config = DoorAgentConfig()
generator = DoorAgentGenerator(config)

OUT = Path("out"); OUT.mkdir(exist_ok=True)

# ────────────────────── AGENT GENERATOR ─────────────────────
# (Now handled by DoorAgentGenerator class in door_agents.py)

# ─────────────────────  BUILD SHEET  ────────────────────────
cells = []
agent_configs = []
agent_id = 0

for r in range(config.ROWS):
    for c in range(config.COLS):
        svg_content, agent_config = generator.generate_random()
        agent_config['agent_id'] = agent_id
        agent_config['row'] = r
        agent_config['col'] = c
        agent_config['x'] = c * config.CELL
        agent_config['y'] = r * config.CELL
        
        cells.append(f'<g transform="translate({c*config.CELL},{r*config.CELL})">{svg_content}</g>')
        agent_configs.append(agent_config)
        agent_id += 1

W, H = config.COLS*config.CELL, config.ROWS*config.CELL
sheet_svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
             f'viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="none"/>'
             + "".join(cells) + '</svg>')

# Load output config from JSON
import json
with open(config.assets_path/"config.json") as f:
    output_config = json.load(f)
    
svg_path = OUT/output_config["output"]["svg_filename"]
csv_path = OUT/output_config["output"]["csv_filename"]
css_path = OUT/output_config["output"]["css_filename"]

svg_path.write_text(sheet_svg)

# Write agent configuration CSV
with open(csv_path, 'w', newline='') as csvfile:
    fieldnames = ['agent_id', 'row', 'col', 'x', 'y', 'body_shape', 'open_eye_index',
                  'closed_eye_index', 'open_mouth_index', 'closed_mouth_index', 'hair_index',
                  'excited', 'body_color', 'node_color', 'feet_color', 'feet_match_body']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(agent_configs)

# Write CSS sprite file
css_content = f"""/* Door Agent Sprite Sheet CSS */
/* Generated sprite sheet: {W}×{H} pixels, {config.CELL}×{config.CELL}px cells */

.sprite {{
    display: inline-block;
    width: {config.CELL}px;
    height: {config.CELL}px;
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
