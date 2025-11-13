# Scripts

Utility scripts for generating and managing avatar assets.

## generate_emote_variants.py

Generates emote-specific variants of eye and mouth SVGs through SVG transformations.

### Usage

Generate all emote variants:

```bash
uv run python scripts/generate_emote_variants.py
```

Generate specific emotes:

```bash
uv run python scripts/generate_emote_variants.py happy sad
```

### Emote Transformations

The script applies the following transformations for each emote:

#### Happy

- **Eyes (open)**: Pupils translated up by 0.5px (cheerful upward gaze)
- **Eyes (closed)**: No transformation
- **Mouths**: No transformation (already smiling)

#### Sad

- **Eyes (open)**: Pupils translated down by 0.8px (downward gaze)
- **Eyes (closed)**: No transformation
- **Mouths**: No transformation

#### Surprised

- **Eyes (open)**: Scaled up 15% from center (wider eyes)
- **Eyes (closed)**: No transformation
- **Mouths**: No transformation (already O-shaped)

#### Angry

- **Eyes (open)**: Pupils centered (no transformation)
- **Eyes (closed)**: No transformation
- **Mouths**: No transformation (tight/small mouths)

#### Bored

- **Eyes**: No transformation (uses closed eyes as-is)
- **Mouths**: No transformation

### Output Structure

Generated files are placed alongside base assets with `emote_` prefix:

```
assets/
  eyes/
    open/
      1.svg              # Base file
      emote_happy_1.svg  # Happy variant
      emote_sad_1.svg    # Sad variant
      ...
    closed/
      1.svg
      emote_happy_1.svg
      ...
  mouths/
    open/
      1.svg
      emote_happy_1.svg
      ...
    closed/
      1.svg
      emote_happy_1.svg
      ...
```

### Implementation Details

- Uses Python's `xml.etree.ElementTree` for SVG parsing and manipulation
- Applies SVG transforms (translate, scale) to elements
- Identifies pupils by fill color (#2B2727, #231F20)
- Preserves original viewBox and structure
- Skips files that already start with `emote_` to avoid double-processing

### Adding New Emotes

To add a new emote type:

1. Add transformation definition to `EMOTE_TRANSFORMS` dictionary
2. Specify transform type: `pupil_translate`, `eye_scale`, or `none`
3. Provide transformation parameters (dx/dy for translate, scale for scale)
4. Run script with new emote name

Example:

```python
EMOTE_TRANSFORMS["excited"] = {
    "eyes_open": {
        "transform_type": "eye_scale",
        "params": {"scale": 1.2}
    },
    # ... other configurations
}
```
