#!/usr/bin/env python3
# ABOUTME: Deterministic door agent avatar generator from email or input string  
# ABOUTME: Creates single SVG agent using SHA-256 hash for consistent avatar generation

import argparse
import sys
import json
import hashlib
from pathlib import Path
from door_agents import DoorAgentConfig, DoorAgentGenerator

def generate_avatar(input_string: str, config: DoorAgentConfig, generator: DoorAgentGenerator) -> tuple:
    """Generate a single deterministic agent from input string."""
    svg_content, agent_config = generator.generate_deterministic(input_string)
    
    # Wrap the agent SVG in a properly sized container
    cell_size = config.CELL
    full_svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{cell_size}" height="{cell_size}" '
                f'viewBox="0 0 {cell_size} {cell_size}">'
                f'<rect width="100%" height="100%" fill="none"/>'
                f'{svg_content}</svg>')
    
    return full_svg, agent_config

def get_output_path(input_string: str) -> Path:
    """Generate output path based on SHA-256 hash of input string."""
    hash_hex = hashlib.sha256(input_string.encode('utf-8')).hexdigest()[:16]  # Use first 16 chars of hash
    return Path("out") / "avatar" / f"{hash_hex}.svg"

def main():
    parser = argparse.ArgumentParser(
        description='Generate deterministic door agent avatars from email or input string',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python avatar.py "user@example.com"                    # Saves to out/avatar/[hash].svg
  python avatar.py "john.doe@company.com" --dry-run      # Outputs SVG to stdout
  python avatar.py "test@test.com" --info                # Shows config and saves file
  python avatar.py "alice@wonderland.org" --output custom.svg  # Custom output path
        '''
    )
    
    parser.add_argument('input', 
                       help='Input string (typically email address) to generate avatar from')
    parser.add_argument('-o', '--output',
                       help='Output SVG file path (default: out/avatar/[hash].svg)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Output SVG to stdout instead of saving to file')
    parser.add_argument('-i', '--info', action='store_true',
                       help='Show agent configuration details')
    parser.add_argument('-j', '--json', action='store_true',
                       help='Output configuration as JSON instead of human-readable format')
    
    args = parser.parse_args()
    
    try:
        # Initialize the door agent system
        config = DoorAgentConfig()
        generator = DoorAgentGenerator(config)
        
        # Generate the avatar
        svg_content, agent_config = generate_avatar(args.input, config, generator)
        
        # Handle output
        if args.dry_run:
            # Output to stdout
            print(svg_content)
        else:
            # Save to file
            if args.output:
                output_path = Path(args.output)
            else:
                output_path = get_output_path(args.input)
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(svg_content)
            print(f"✅ Generated avatar: {output_path}", file=sys.stderr)
        
        # Show configuration info if requested
        if args.info:
            if args.json:
                print(json.dumps(agent_config, indent=2), file=sys.stderr)
            else:
                print("\n🤖 Agent Configuration:", file=sys.stderr)
                print(f"   Input: {agent_config['input_string']}", file=sys.stderr)
                print(f"   Body Shape: {agent_config['body_shape']}", file=sys.stderr)
                print(f"   Eyes: #{agent_config['eye_index']}", file=sys.stderr)
                print(f"   Mouth: #{agent_config['mouth_index']} {'(excited)' if agent_config['excited'] else '(rest)'}", file=sys.stderr)
                if agent_config['hair_index']:
                    print(f"   Hair: #{agent_config['hair_index']}", file=sys.stderr)
                else:
                    print("   Hair: None", file=sys.stderr)
                print(f"   Body Color: {agent_config['body_color']}", file=sys.stderr)
                print(f"   Node Color: {agent_config['node_color']}", file=sys.stderr)
                print(f"   Feet: {'Match body' if agent_config['feet_match_body'] else 'Match nodes'} ({agent_config['feet_color']})", file=sys.stderr)
                
    except Exception as e:
        print(f"❌ Error generating avatar: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()