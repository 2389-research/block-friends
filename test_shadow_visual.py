#!/usr/bin/env python3
"""Visual test script for shadow feature across different avatar types."""
import sys
sys.path.insert(0, '.')
from door_agents import DoorAgentGenerator, DoorAgentConfig

def generate_test_avatars():
    config = DoorAgentConfig()
    generator = DoorAgentGenerator(config)

    test_cases = [
        ("narrow-body@test.com", "Narrow body"),
        ("wide-body@test.com", "Wide body"),
        ("wide-hair@test.com", "Wide hair (cat ears likely)"),
        ("minimal@test.com", "Minimal styling"),
    ]

    for email, description in test_cases:
        svg, _ = generator.generate_deterministic(input_string=email, universal=True)
        filename = f"test_{email.split('@')[0]}.svg"
        with open(filename, 'w') as f:
            f.write(svg)
        print(f"✓ Generated {filename} - {description}")

        # Quick validation
        assert '<ellipse' in svg, f"Missing shadow in {email}"
        assert 'shadow-blur' in svg, f"Missing filter in {email}"
        print("  Shadow present and filtered")

if __name__ == '__main__':
    generate_test_avatars()
    print("\n✓ All test avatars generated successfully")
    print("Open the generated test_*.svg files to visually verify shadows")
