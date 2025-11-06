#!/usr/bin/env python3
# ABOUTME: Working prototype for universal SVG generation
# ABOUTME: Creates single SVG with all states controlled by CSS classes

"""
Universal Avatar SVG Builder

Generates a single SVG containing all eye and mouth states for an avatar,
with CSS class-based visibility control. Directly reads and assembles base
assets without extracting from generated SVGs.
"""

from door_agents import DoorAgentConfig, DoorAgentGenerator
import hashlib
import xml.etree.ElementTree as ET


def read_asset_content(svg_path) -> str:
    """Read SVG file and extract inner content (everything inside <svg> tag)."""
    root = ET.parse(svg_path).getroot()
    # Get all child elements as string
    content = "".join(ET.tostring(c, encoding="unicode") for c in root)
    return content


def build_universal_svg(email: str, default_class: str = "idle_0") -> str:
    """Build a universal SVG with all eye/mouth states from base assets."""

    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    # Generate avatar ID
    avatar_id = hashlib.sha256(email.encode('utf-8')).hexdigest()[:12]

    # Get deterministic indices from hash (same logic as generate_deterministic)
    hash_bytes = hashlib.sha256(email.encode('utf-8')).digest()
    open_eye_idx = hash_bytes[0] % len(config.open_eyes)
    closed_eye_idx = hash_bytes[1] % len(config.closed_eyes)
    open_mouth_idx = hash_bytes[2] % len(config.open_mouths)
    closed_mouth_idx = hash_bytes[3] % len(config.closed_mouths)

    # Build paths to specific assets for this avatar
    assets_path = config.assets_path

    # Collect eye groups - read actual asset files
    eye_groups = {}

    # Open eyes (base state)
    open_eye_file = assets_path / "eyes" / "open" / f"{open_eye_idx + 1}.svg"
    eye_groups['open'] = f'  <g class="open">{read_asset_content(open_eye_file)}</g>'

    # Closed eyes
    closed_eye_file = assets_path / "eyes" / "closed" / f"{closed_eye_idx + 1}.svg"
    eye_groups['closed'] = f'  <g class="closed">{read_asset_content(closed_eye_file)}</g>'

    # Emote eye variants (happy, sad, surprised, angry, bored)
    for emote in ['happy', 'sad', 'surprised', 'angry', 'bored']:
        # Determine if this emote uses open or closed eyes
        # Based on door_agents.py logic: happy uses open, sad/angry/bored use open base
        # surprised uses open, all use open_eye_emotes
        emote_file = assets_path / "eyes" / "open" / f"emote_{emote}_{open_eye_idx + 1}.svg"
        if emote_file.exists():
            eye_groups[emote] = f'  <g class="{emote}">{read_asset_content(emote_file)}</g>'

    # Collect mouth groups
    mouth_groups = {}

    # Open mouth (base state)
    open_mouth_file = assets_path / "mouths" / "open" / f"{open_mouth_idx + 1}.svg"
    mouth_groups['open'] = f'  <g class="open">{read_asset_content(open_mouth_file)}</g>'

    # Closed mouth
    closed_mouth_file = assets_path / "mouths" / "closed" / f"{closed_mouth_idx + 1}.svg"
    mouth_groups['closed'] = f'  <g class="closed">{read_asset_content(closed_mouth_file)}</g>'

    # Emote mouth variants - happy and surprised use open_mouth_emotes
    for emote in ['happy', 'surprised']:
        emote_file = assets_path / "mouths" / "open" / f"emote_{emote}_{open_mouth_idx + 1}.svg"
        if emote_file.exists():
            mouth_groups[emote] = f'  <g class="{emote}">{read_asset_content(emote_file)}</g>'

    # sad, angry, bored use closed_mouth_emotes
    for emote in ['sad', 'angry', 'bored']:
        emote_file = assets_path / "mouths" / "closed" / f"emote_{emote}_{closed_mouth_idx + 1}.svg"
        if emote_file.exists():
            mouth_groups[emote] = f'  <g class="{emote}">{read_asset_content(emote_file)}</g>'

    # Vowel mouth variants (all use open_mouth_emotes)
    for vowel in ['a', 'e', 'i', 'o', 'u']:
        vowel_file = assets_path / "mouths" / "open" / f"emote_vowel_{vowel}_{open_mouth_idx + 1}.svg"
        if vowel_file.exists():
            mouth_groups[f'vowel_{vowel}'] = f'  <g class="vowel_{vowel}">{read_asset_content(vowel_file)}</g>'

    # Build nested eye/mouth groups
    eyes_nested = '<g class="eyes">\n' + '\n'.join(eye_groups.values()) + '\n</g>'
    mouths_nested = '<g class="mouths">\n' + '\n'.join(mouth_groups.values()) + '\n</g>'

    # Build CSS rules
    css_rules = [f'#avatar-{avatar_id} .eyes > g, #avatar-{avatar_id} .mouths > g {{ display: none; }}']

    # Idle frame rules (10 frames with independent eye/mouth states)
    idle_frames = [
        ('idle_0', 'open', 'closed'),
        ('idle_1', 'open', 'open'),
        ('idle_2', 'closed', 'closed'),
        ('idle_3', 'happy', 'closed'),
        ('idle_4', 'open', 'closed'),
        ('idle_5', 'sad', 'closed'),
        ('idle_6', 'open', 'bored'),
        ('idle_7', 'bored', 'bored'),
        ('idle_8', 'open', 'open'),
        ('idle_9', 'open', 'closed'),
    ]

    for frame, eye_class, mouth_class in idle_frames:
        css_rules.append(
            f'#avatar-{avatar_id}.{frame} .eyes > .{eye_class}, '
            f'#avatar-{avatar_id}.{frame} .mouths > .{mouth_class} {{ display: block; }}'
        )

    # Emote rules (matching pairs)
    for emote in ['happy', 'sad', 'surprised', 'angry', 'bored']:
        css_rules.append(
            f'#avatar-{avatar_id}.{emote} .eyes > .{emote}, '
            f'#avatar-{avatar_id}.{emote} .mouths > .{emote} {{ display: block; }}'
        )

    # Vowel rules (open eyes + vowel mouths)
    for vowel in ['a', 'e', 'i', 'o', 'u']:
        css_rules.append(
            f'#avatar-{avatar_id}.vowel_{vowel} .eyes > .open, '
            f'#avatar-{avatar_id}.vowel_{vowel} .mouths > .vowel_{vowel} {{ display: block; }}'
        )

    # Build style block
    style_block = '<style>\n' + '\n'.join(css_rules) + '\n</style>'

    # Generate base SVG structure (body, hair, nodes, feet) using neutral frame
    base_svg, agent_info = generator.generate_deterministic(email, frame='neutral')

    # For prototype, we'll need to extract the base structure and replace eye/mouth sections
    # This is a simplified approach - in production we'd reconstruct the full structure
    # For now, let's just build a minimal test structure

    CELL = config.CELL

    universal = f'''<svg id="avatar-{avatar_id}" class="{default_class}" width="{CELL}" height="{CELL}" viewBox="0 0 {CELL} {CELL}" xmlns="http://www.w3.org/2000/svg">
{style_block}
<!-- Body, hair, nodes, feet would go here - for prototype we're testing structure -->
<!-- Universal eye states -->
{eyes_nested}
<!-- Universal mouth states -->
{mouths_nested}
</svg>'''

    return universal


if __name__ == '__main__':
    print("Building universal SVG for test@example.com...")

    universal_svg = build_universal_svg('test@example.com')

    # Write to file
    output_path = 'out/universal_working.svg'
    with open(output_path, 'w') as f:
        f.write(universal_svg)

    size = len(universal_svg)

    print(f"\n✓ Generated: {output_path}")
    print(f"\nUniversal SVG Stats:")
    print(f"  Size: {size:,} bytes ({size/1024:.2f} KB)")

    # Compare to current approach
    from prototype_simple import measure_current_approach
    print("\n" + "="*50)
    print("Measuring current approach for comparison...")
    print("="*50 + "\n")

    current_total, _ = measure_current_approach()

    print("\n" + "="*50)
    print("COMPARISON")
    print("="*50)
    print(f"Current (20 SVGs):  {current_total:>8,} bytes ({current_total/1024:>6.2f} KB)")
    print(f"Universal (1 SVG):  {size:>8,} bytes ({size/1024:>6.2f} KB)")
    print(f"Difference:         {current_total-size:>8,} bytes ({(current_total-size)/1024:>6.2f} KB)")
    print(f"Reduction:          {100*(1 - size/current_total):>7.1f}%")

    # Test gzip compression
    import gzip

    # Compress universal SVG
    universal_gzipped = gzip.compress(universal_svg.encode('utf-8'))
    universal_gzip_size = len(universal_gzipped)

    print(f"\nWith gzip compression:")
    print(f"Universal gzipped:  {universal_gzip_size:>8,} bytes ({universal_gzip_size/1024:>6.2f} KB)")
    print(f"Compression ratio:  {100*(1 - universal_gzip_size/size):>7.1f}%")
    print(f"vs Current total:   {100*(1 - universal_gzip_size/current_total):>7.1f}% smaller")
