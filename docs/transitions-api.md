# Avatar Animation Transitions API

## Overview

The transitions system provides smooth, opacity-based animations between neutral facial expressions and emotional states (emotes) or vowel mouth shapes (for lip-sync).

## Architecture

### Opacity Crossfade Approach

The transition system uses a simple but effective opacity-based crossfading technique:

- **0% weight**: 100% base (neutral) + 0% target (expression)
- **50% weight**: 50% base + 50% target
- **100% weight**: 0% base + 100% target

This creates smooth visual transitions without requiring complex path morphing or matching SVG structures. The approach is:

- **Simple**: No complex animation logic or SVG manipulation
- **Performant**: Fast generation with minimal overhead
- **Flexible**: Works with any combination of assets
- **Deterministic**: Same input always produces same output

### Base vs Target States

**Base State (Neutral):**
- Open eyes (resting expression)
- Closed mouth (neutral position)
- Serves as the starting point for all transitions

**Target State (Expression):**
- Emote eyes and mouth (joy, sorrow, surprised, angry, bored, fun)
- Vowel mouth shapes (A, E, I, O, U) with neutral eyes for lip-sync

## API Endpoints

### Get Transition Frame

```http
GET /avatar/{input}/transition/{emote}/{weight}
```

Generate a single transition frame at a specific weight between neutral and full expression.

**Parameters:**
- `input` (string): User identifier (email, username, hash, etc.)
- `emote` (string): Expression name
  - Emotes: `joy`, `sorrow`, `surprised`, `angry`, `bored`, `fun`
  - Vowels: `A`, `E`, `I`, `O`, `U`
- `weight` (integer): Animation progress (0-100)
  - 0 = fully neutral
  - 100 = full expression

**Response:**
- **Content-Type**: `image/svg+xml`
- **Body**: SVG image (60×60px)

**Examples:**
```bash
# Neutral face
curl http://localhost:8000/avatar/user@example.com/transition/joy/0

# Halfway to joy
curl http://localhost:8000/avatar/user@example.com/transition/joy/50

# Full joy expression
curl http://localhost:8000/avatar/user@example.com/transition/joy/100

# Vowel shape for lip-sync
curl http://localhost:8000/avatar/user@example.com/transition/A/100
```

**Error Responses:**
- `400 Bad Request`: Invalid emote name or weight out of range
- `500 Internal Server Error`: Generation failure

### Get Animation Bundle

```http
GET /avatar/{input}/bundle?animations=emotes,vowels
```

Generate ZIP bundle with multi-page PDF animations for offline use or integration.

**Parameters:**
- `input` (string): User identifier
- `animations` (query parameter): Comma-separated list
  - `emotes`: 6 emotional expressions
  - `vowels`: 5 vowel mouth shapes
  - `idle`: Breathing animation (existing feature)

**Response:**
- **Content-Type**: `application/zip`
- **Body**: ZIP file containing:
  - `emote_*.pdf` - 7-frame animations (0, 25, 50, 100, 50, 25, 0)
  - `vowel_*.pdf` - 5-frame animations (0, 50, 100, 50, 0)
  - `metadata.json` - Animation specifications and frame data

**Examples:**
```bash
# Get emote animations only
curl "http://localhost:8000/avatar/user@example.com/bundle?animations=emotes" -o animations.zip

# Get vowel animations for lip-sync
curl "http://localhost:8000/avatar/user@example.com/bundle?animations=vowels" -o vowels.zip

# Get all animations
curl "http://localhost:8000/avatar/user@example.com/bundle?animations=emotes,vowels" -o all-animations.zip
```

**Bundle Contents:**

Emotes bundle includes:
- `emote_joy.pdf` (7 pages)
- `emote_sorrow.pdf` (7 pages)
- `emote_surprised.pdf` (7 pages)
- `emote_angry.pdf` (7 pages)
- `emote_bored.pdf` (7 pages)
- `emote_fun.pdf` (7 pages)
- `metadata.json`

Vowels bundle includes:
- `vowel_A.pdf` (5 pages)
- `vowel_E.pdf` (5 pages)
- `vowel_I.pdf` (5 pages)
- `vowel_O.pdf` (5 pages)
- `vowel_U.pdf` (5 pages)
- `metadata.json`

## Animation Sequences

### Emote Animations (7 frames each)

**Frame Sequence:** `0% → 25% → 50% → 100% → 50% → 25% → 0%`

**Duration:** 7 frames at 12 FPS = ~583ms per loop

**Available Emotes:**

- **joy**: Happy eyes + wide smile
  - Use for: happiness, success, positive feedback
- **sorrow**: Sad eyes + frown
  - Use for: sadness, failure, negative feedback
- **surprised**: Wide eyes + open mouth
  - Use for: surprise, shock, alerts
- **angry**: Angry eyes + angry mouth
  - Use for: frustration, errors, warnings
- **bored**: Half-closed eyes + flat mouth
  - Use for: waiting states, idle periods
- **fun**: Winking eye + playful smirk
  - Use for: playful interactions, jokes, celebrations

### Vowel Animations (5 frames each)

**Frame Sequence:** `0% → 50% → 100% → 50% → 0%`

**Duration:** 5 frames at 10 FPS = ~500ms per shape

**Available Vowels:**

- **A**: Open mouth (ah)
  - IPA: /ɑ/ or /æ/
  - Words: "father", "cat", "start"
- **E**: Neutral/closed mouth (eh)
  - IPA: /ɛ/ or /e/
  - Words: "bed", "say", "end"
- **I**: Neutral/closed mouth (ee)
  - IPA: /i/ or /ɪ/
  - Words: "see", "sit", "beat"
- **O**: Round mouth (oh)
  - IPA: /o/ or /ɔ/
  - Words: "go", "thought", "boat"
- **U**: Small round mouth (oo)
  - IPA: /u/ or /ʊ/
  - Words: "food", "book", "moon"

**Lip-Sync Usage:**

For speech animation, sequence vowel shapes to match spoken words:
- "Hello" → H(neutral) → E → L(neutral) → O
- "Good" → G(neutral) → U → D(neutral)
- "Yes" → Y(neutral) → E → S(neutral)

## Usage Examples

### JavaScript

**Basic Transition Loading:**
```javascript
// Load transition frame
const img = document.createElement('img');
img.src = '/avatar/user@example.com/transition/joy/50';
document.body.appendChild(img);
```

**Manual Animation:**
```javascript
// Animate transition manually
const img = document.getElementById('avatar');
let weight = 0;

const interval = setInterval(() => {
  img.src = `/avatar/user@example.com/transition/joy/${weight}`;
  weight += 5;
  if (weight > 100) clearInterval(interval);
}, 50); // 20 FPS
```

**Loop Animation:**
```javascript
// Create looping animation
const sequence = [0, 25, 50, 75, 100, 75, 50, 25, 0];
let currentFrame = 0;

setInterval(() => {
  const weight = sequence[currentFrame];
  img.src = `/avatar/user@example.com/transition/joy/${weight}`;
  currentFrame = (currentFrame + 1) % sequence.length;
}, 100); // 10 FPS
```

**Interactive Slider:**
```javascript
// Control transition with slider
const slider = document.getElementById('weight-slider');
const img = document.getElementById('avatar');

slider.addEventListener('input', (e) => {
  const weight = e.target.value;
  img.src = `/avatar/user@example.com/transition/joy/${weight}`;
});
```

**React Component:**
```jsx
import { useState, useEffect } from 'react';

function AnimatedAvatar({ user, emote }) {
  const [weight, setWeight] = useState(0);

  useEffect(() => {
    const sequence = [0, 25, 50, 75, 100, 75, 50, 25, 0];
    let frame = 0;

    const interval = setInterval(() => {
      setWeight(sequence[frame]);
      frame = (frame + 1) % sequence.length;
    }, 100);

    return () => clearInterval(interval);
  }, [emote]);

  return (
    <img
      src={`/avatar/${user}/transition/${emote}/${weight}`}
      alt={`${user} avatar`}
    />
  );
}
```

### Python

**Get Single Transition Frame:**
```python
import requests

# Get transition frame
response = requests.get(
    'http://localhost:8000/avatar/user@example.com/transition/joy/50'
)

# Save to file
with open('avatar_joy_50.svg', 'wb') as f:
    f.write(response.content)
```

**Generate All Frames:**
```python
import requests

user = 'user@example.com'
emote = 'joy'
weights = [0, 25, 50, 75, 100]

for weight in weights:
    response = requests.get(
        f'http://localhost:8000/avatar/{user}/transition/{emote}/{weight}'
    )

    with open(f'avatar_{emote}_{weight}.svg', 'wb') as f:
        f.write(response.content)

    print(f'Generated {emote} at {weight}%')
```

**Get Animation Bundle:**
```python
import requests
import zipfile
import io

# Get animation bundle
response = requests.get(
    'http://localhost:8000/avatar/user@example.com/bundle',
    params={'animations': 'emotes,vowels'}
)

# Save ZIP file
with open('animations.zip', 'wb') as f:
    f.write(response.content)

# Or extract directly
zip_file = zipfile.ZipFile(io.BytesIO(response.content))
zip_file.extractall('animations/')
```

**Process Bundle Metadata:**
```python
import requests
import zipfile
import io
import json

response = requests.get(
    'http://localhost:8000/avatar/user@example.com/bundle',
    params={'animations': 'emotes'}
)

zip_file = zipfile.ZipFile(io.BytesIO(response.content))

# Read metadata
metadata = json.loads(zip_file.read('metadata.json'))

print(f"Avatar hash: {metadata['avatar_hash']}")
print(f"Animations: {list(metadata['animations'].keys())}")

# Print emote specs
emotes_spec = metadata['animations']['emotes']
print(f"Frame count: {emotes_spec['frame_count']}")
print(f"FPS: {emotes_spec['fps']}")
print(f"Frame sequence: {emotes_spec['frames']}")
```

**Lip-Sync Example:**
```python
import requests
import time

def speak_word(user, word):
    """Animate avatar speaking a word."""
    vowels_in_word = [c for c in word.upper() if c in 'AEIOU']

    for vowel in vowels_in_word:
        # Transition to vowel shape
        for weight in [0, 50, 100]:
            response = requests.get(
                f'http://localhost:8000/avatar/{user}/transition/{vowel}/{weight}'
            )
            display_frame(response.content)
            time.sleep(0.05)  # 20 FPS

        # Return to neutral
        for weight in [50, 0]:
            response = requests.get(
                f'http://localhost:8000/avatar/{user}/transition/{vowel}/{weight}'
            )
            display_frame(response.content)
            time.sleep(0.05)

# Usage
speak_word('user@example.com', 'Hello')
```

## Performance

### Response Times

- **Single transition frame**: < 100ms (cold)
- **Cached transition frame**: < 5ms (warm)
- **Full emotes bundle**: < 5 seconds (6 PDFs × 7 frames)
- **Full vowels bundle**: < 3 seconds (5 PDFs × 5 frames)
- **Combined bundle**: < 8 seconds (11 PDFs total)

### Caching

All transition frames are cached for improved performance:

- **Cache key**: `{input_hash}_transition_{emote}_{weight}.svg`
- **Cache location**: `out/avatar/`
- **Cache behavior**: Check cache first, generate on miss
- **Cache invalidation**: Manual cache clearing after generation changes

### Optimization Tips

1. **Preload common frames**: Cache 0, 50, and 100 weight frames
2. **Use bundles for offline**: Download once, play multiple times
3. **Limit frame rates**: 10-12 FPS is sufficient for smooth animation
4. **Batch requests**: Request multiple frames in parallel
5. **CDN caching**: Use CDN for cached frame serving in production

### Memory Usage

- **Per-frame SVG size**: ~2-4 KB
- **Per-emote PDF size**: ~50-100 KB (7 pages)
- **Per-vowel PDF size**: ~35-70 KB (5 pages)
- **Full bundle size**: ~800 KB - 1.2 MB (all animations)

## Interactive Demo

An interactive HTML demo is available at:

```
http://localhost:8000/static/transitions-demo.html
```

**Demo Features:**
- Live preview of transition frames
- Interactive slider for manual weight control
- Play/stop animation controls
- Dropdown to switch between all emotes and vowels
- Custom input string testing
- Real-time updates

**Usage:**
1. Start the server: `uv run python app.py`
2. Open browser: `http://localhost:8000/static/transitions-demo.html`
3. Adjust slider to see smooth transitions
4. Click "Play Animation" to see looping sequence
5. Change expression or input string to test different avatars

## Technical Details

### SVG Structure

Generated SVG contains layered groups for crossfading:

```xml
<svg viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg">
  <!-- Hair behind layer (if present) -->

  <!-- Body and static elements -->
  <rect .../>
  <circle .../> <!-- Left node -->
  <circle .../> <!-- Right node -->
  <rect .../> <!-- Left foot -->
  <rect .../> <!-- Right foot -->

  <!-- Base layer: Original eyes/mouth at base_opacity -->
  <g opacity="0.500">
    <g transform="..."><!-- eyes --></g>
    <g transform="..."><!-- mouth --></g>
  </g>

  <!-- Target layer: Emote eyes/mouth at target_opacity -->
  <g opacity="0.500">
    <g transform="..."><!-- emote eyes --></g>
    <g transform="..."><!-- emote mouth --></g>
  </g>

  <!-- Hair front layer (if present) -->
</svg>
```

### Deterministic Generation

All transitions are deterministic:

- Same `input` + `emote` + `weight` = identical SVG output
- Uses SHA-256 hash of input string for asset selection
- Avatar body/colors/hair remain consistent across all expressions
- Only eyes and mouth change between neutral and target states

### Asset Requirements

Required assets in `assets/` directory:

**Eyes:**
- `eyes/emote_happy.svg`
- `eyes/emote_sad.svg`
- `eyes/emote_surprised.svg`
- `eyes/emote_angry.svg`
- `eyes/emote_bored.svg`
- `eyes/emote_fun.svg`

**Mouths:**
- `mouths/emote_joy.svg`
- `mouths/emote_sorrow.svg`
- `mouths/emote_surprised.svg`
- `mouths/emote_angry.svg`
- `mouths/emote_bored.svg`
- `mouths/emote_fun.svg`
- `mouths/vowel_A.svg`
- `mouths/vowel_E.svg`
- `mouths/vowel_I.svg`
- `mouths/vowel_O.svg`
- `mouths/vowel_U.svg`

## Error Handling

### Invalid Emote

```bash
curl http://localhost:8000/avatar/user/transition/invalid/50
```

Response:
```json
{
  "detail": "Invalid emote 'invalid'. Must be one of: joy, sorrow, surprised, angry, bored, fun, A, E, I, O, U"
}
```

### Invalid Weight

```bash
curl http://localhost:8000/avatar/user/transition/joy/150
```

Response:
```json
{
  "detail": "Weight must be between 0 and 100, got 150"
}
```

### Generation Error

If SVG generation fails, returns 500 with error details in logs.

## Best Practices

### For Web Applications

1. **Preload key frames**: Load 0%, 50%, and 100% frames on page load
2. **Use CSS for sizing**: Let browser scale SVGs with CSS
3. **Limit concurrent animations**: Animate one avatar at a time
4. **Debounce interactions**: Avoid rapid emote changes

### For Games

1. **Use bundles**: Download all animations once at game start
2. **Extract PDFs**: Convert PDF pages to sprite sheets
3. **Cache locally**: Store animations in game assets
4. **Optimize frame rates**: 10-12 FPS is sufficient for character emotions

### For Chat Applications

1. **React to messages**: Map message sentiment to emotes
2. **Use vowels for speech**: Animate mouth for voice chat
3. **Idle state**: Return to neutral after 2-3 seconds
4. **Preload user avatars**: Cache common users' transition frames

### For Accessibility

1. **Provide alt text**: Describe current expression
2. **Respect prefers-reduced-motion**: Disable animations if requested
3. **Keyboard control**: Allow emote selection via keyboard
4. **Screen reader support**: Announce expression changes

## Future Enhancements

Potential improvements to the transition system:

- **Custom frame sequences**: Define animation timing per use case
- **Easing functions**: Non-linear interpolation for more natural movement
- **Multiple expressions**: Blend more than 2 states simultaneously
- **PNG output**: Raster format for better compression
- **WebP/AVIF bundles**: Modern image formats for smaller sizes
- **Real-time streaming**: WebSocket-based frame delivery
- **Expression mixing**: Combine emotes (e.g., 50% joy + 50% surprise)
- **Physics-based animation**: Add bounce/spring effects to transitions
