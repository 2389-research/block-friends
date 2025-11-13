# Door Agent Avatar System v2.0

> **⚠️ BREAKING CHANGES:** This is version 2.0 of the avatar system. Avatars generated from the same input will look different from v1.x due to hash byte allocation changes. See [Breaking Changes](#breaking-changes) section below.

A comprehensive avatar generation system that creates procedurally generated "door agent" characters with animated emotes and expressions. Features both bulk sprite sheet generation and a deterministic web API service for individual avatars.

## 🚀 Features

### **Dual Generation Modes**

- **🎨 Sprite Sheets**: Generate 400 randomized agents in 20×20 grids for game development
- **🔗 Deterministic Avatars**: Generate consistent avatars from any input (emails, usernames, etc.)
- **🌐 Web API**: FastAPI service for HTTP avatar generation (`/avatar/{input}.svg`)

### **Animation System (v2.0)**

- **🎭 5 Emotes**: happy, sad, surprised, angry, bored with unique expressions
- **👁️ Open/Closed States**: Independent control of eye and mouth states
- **💫 Idle Animation**: 10-frame idle animation with varied expressions
- **📦 Animation Bundles**: GET bundled frame data for all animations

### **Massive Variety**

- **1.27 billion unique variants** from current asset collection
- **100x more variety than traditional Gravatar systems**
- **Collision-resistant** for platforms up to ~1 million users

### **Production Ready**

- **File-based caching** for instant repeat requests
- **Proper HTTP headers** with long-term caching and version tracking
- **Multiple output formats**: SVG, PNG, CSS sprites, animation bundles
- **Auto-generated API documentation**
- **Ground Shadows**: Soft-edged shadows that scale with avatar content width for depth and visual grounding

## 🎯 Quick Start

### **Installation**

This project uses [uv](https://docs.astral.sh/uv/) for dependency management:

```bash
# Install dependencies
uv sync
```

### **Generate Sprite Sheet**

```bash
# Create 400-agent sprite sheet
uv run generate.py
```

### **Generate Individual Avatars**

```bash
# Deterministic avatar from email
uv run avatar.py "user@example.com"

# Output to stdout instead of file
uv run avatar.py "alice@wonderland.org" --dry-run

# Get configuration info
uv run avatar.py "test@test.com" --info --json
```

### **Run Web API Service**

```bash
# Start FastAPI server
uv run python app.py

# Test endpoints
curl http://localhost:8000/avatar/user@example.com.svg > avatar.svg
curl http://localhost:8000/avatar/973dfe463ec85785.svg > cached.svg
```

## ⚠️ Breaking Changes

### **v2.0 Migration Notice**

Version 2.0 introduces significant breaking changes to support the emote system. **There is no migration path** - avatars from v1.x will look different when generated with v2.0.

#### **What Changed:**

1. **Hash Byte Allocation Changed**
   - v1.x used 2 byte indices for eyes and mouths
   - v2.0 uses 4 byte indices: `open_eye_index`, `closed_eye_index`, `open_mouth_index`, `closed_mouth_index`
   - This reallocation affects ALL avatars, even in default state

2. **Asset Structure Reorganized**
   - Assets moved from flat structure to hierarchical open/closed subdirectories
   - v1.x: `assets/eyes/1.svg`, `assets/mouths/1.svg`
   - v2.0: `assets/eyes/open/1.svg`, `assets/eyes/closed/1.svg`, `assets/mouths/open/1.svg`, `assets/mouths/closed/1.svg`

3. **Emote Variants Added**
   - New emote-specific assets: `emote_happy_1.svg`, `emote_sad_1.svg`, etc.
   - Base assets (1.svg, 2.svg, etc.) used for idle animation
   - Emote assets used for expressive states

4. **No Backward Compatibility**
   - Same input strings will generate different avatars in v2.0
   - If you cached v1.x avatars, they will not match v2.0 outputs
   - Consider this when upgrading production systems

#### **Version Detection:**

Check the system version before generating avatars:

```bash
# Query version endpoint
curl http://localhost:8000/version
# Returns: {"avatar_system_version": "2.0"}

# Check response headers
curl -I http://localhost:8000/avatar/test@example.com.svg
# Returns: X-Avatar-System-Version: 2.0
```

## 🌐 Web API

### **Avatar Generation Endpoint**

```http
GET /avatar/{input}.svg?frame={frame}
```

**Examples:**

- `GET /avatar/user@example.com.svg` - Generate default avatar
- `GET /avatar/user@example.com.svg?frame=idle_0` - Idle animation frame 0
- `GET /avatar/user@example.com.svg?frame=happy` - Happy emote
- `GET /avatar/973dfe463ec85785.svg` - Serve cached avatar by hash

**Frame Options:**

- `idle_0` through `idle_9` - 10-frame idle animation with varied expressions
- `happy`, `sad`, `surprised`, `angry`, `bored` - 5 emote expressions
- No frame parameter = default state (open eyes, closed mouth)

**Response:**

- **Content-Type**: `image/svg+xml`
- **Cache-Control**: `public, max-age=31536000` (1 year)
- **X-Avatar-System-Version**: `2.0`
- **Body**: SVG image (60×60px)

### **Avatar Configuration Endpoint**

```http
GET /avatar/{input}.svg/info
```

**Response Example:**

```json
{
  "input_string": "user@example.com",
  "body_shape": "6x7",
  "eye_index": 2,
  "mouth_index": 2,
  "hair_index": null,
  "excited": false,
  "body_color": "#E99987",
  "node_color": "#A47E69",
  "cache_info": {
    "cached": true,
    "hash": "973dfe463ec85785"
  }
}
```

### **Animation Bundle Endpoint**

```http
GET /avatar/{input}/bundle?animations=idle,happy,sad
```

**Examples:**

- `GET /avatar/user@example.com/bundle?animations=idle` - Get all 4 idle frames
- `GET /avatar/user@example.com/bundle?animations=idle,happy,sad,surprised,angry,bored` - Get all frames

**Response:** JSON with frame data

```json
{
  "input_string": "user@example.com",
  "frames": {
    "idle_0": "data:image/svg+xml;base64,...",
    "idle_1": "data:image/svg+xml;base64,...",
    "happy": "data:image/svg+xml;base64,...",
    ...
  }
}
```

### **Service Information**

```http
GET /           # Service overview and usage
GET /version    # Get avatar system version (returns {"avatar_system_version": "2.0"})
GET /health     # Health check
GET /docs       # Auto-generated API documentation
```

## 🏗️ Architecture

### **Project Structure**

```
sprite-maker/
├── generate.py                    # Bulk sprite sheet generator
├── avatar.py                      # CLI single avatar generator
├── app.py                         # FastAPI web service
├── door_agents.py                 # Shared generation library
├── generate_emote_variants.py     # Script to generate emote variant assets
├── test-grid.html                 # Visual testing page for animations
├── assets/                        # SVG asset files (v2.0 structure)
│   ├── eyes/
│   │   ├── open/                  # Open eye states
│   │   │   ├── 1.svg ... 4.svg    # Base open eyes (idle animation)
│   │   │   ├── emote_happy_1.svg  # Happy emote open eyes
│   │   │   ├── emote_sad_1.svg    # Sad emote open eyes
│   │   │   └── ...                # Other emote variants
│   │   └── closed/                # Closed eye states
│   │       ├── 1.svg ... 2.svg    # Base closed eyes (blink)
│   │       ├── emote_angry_1.svg  # Angry emote closed eyes
│   │       └── ...                # Other emote variants
│   ├── mouths/
│   │   ├── open/                  # Open mouth states
│   │   │   ├── 1.svg ... 3.svg    # Base open mouths
│   │   │   ├── emote_happy_1.svg  # Happy emote open mouths
│   │   │   └── ...                # Other emote variants
│   │   └── closed/                # Closed mouth states
│   │       ├── 1.svg ... 7.svg    # Base closed mouths (idle)
│   │       ├── emote_sad_1.svg    # Sad emote closed mouths
│   │       └── ...                # Other emote variants
│   └── hair/1.svg ... 16.svg      # Hair styles (unchanged)
└── out/                           # Generated outputs
    ├── agents_sheet.svg           # Sprite sheet
    ├── agents_config.csv          # Agent configurations
    └── avatar/                    # Cached individual avatars
```

### **Core Components**

**`door_agents.py`** - Shared Library

- `DoorAgentConfig`: Loads JSON configuration and SVG assets
- `DoorAgentGenerator`: Handles both random and deterministic generation
- Unified asset parsing and rendering logic

**`generate.py`** - Sprite Sheet Generator

- Creates 400-agent grids using random generation
- Outputs SVG sheet, CSV data, and CSS sprite classes
- Uses shared library for consistency

**`avatar.py`** - CLI Avatar Generator

- Deterministic generation from any input string
- Hash-based filename output (`out/avatar/[hash].svg`)
- Support for custom output paths and dry-run mode

**`app.py`** - Web API Service

- FastAPI service with `/avatar/{input}.svg` endpoints  
- File-based caching for performance
- Proper HTTP headers and error handling

## 🎭 Emote System (v2.0)

### **Overview**

The v2.0 emote system provides rich animation support with 5 distinct emotes and a 4-frame idle animation. Each avatar has independent control over eye and mouth states to create expressive animations.

### **5 Emote Expressions**

| Emote | Eyes | Mouth | Use Case |
|-------|------|-------|----------|
| **happy** | Open, upturned | Open, smiling | Positive reactions, success states |
| **sad** | Closed, downturned | Closed, frowning | Negative feedback, failure states |
| **surprised** | Wide open | Open, circular | Alerts, notifications, unexpected events |
| **angry** | Narrow, angled | Open, frowning | Errors, conflicts, warnings |
| **bored** | Half-closed | Closed, flat | Waiting states, idle timeouts |

### **Idle Animation**

The idle animation provides varied expressions with 10 frames:

```
Frame 0: Eyes open,  Mouth closed (neutral)
Frame 1: Eyes open,  Mouth open
Frame 2: Eyes closed, Mouth closed (blink)
Frame 3: Eyes happy, Mouth closed (subtle smile)
Frame 4: Eyes open,  Mouth closed
Frame 5: Eyes sad,   Mouth closed (subtle sadness)
Frame 6: Eyes open,  Mouth bored
Frame 7: Eyes bored, Mouth bored (full boredom)
Frame 8: Eyes open,  Mouth open
Frame 9: Eyes open,  Mouth closed
```

**Recommended cycle:** 4 FPS (250ms per frame) for smooth idle animation

### **Frame State System**

Each frame is defined by two independent states:

- **Eye State**: `open` or `closed`
- **Mouth State**: `open` or `closed`

This allows the system to deterministically select appropriate assets:

```python
# Example: "happy" emote
eye_state = "open"    # Happy uses open eyes
mouth_state = "open"  # Happy uses open mouth
eye_index = open_eye_index    # Deterministic from hash
mouth_index = open_mouth_index  # Deterministic from hash

# System loads: assets/eyes/open/emote_happy_{eye_index}.svg
#               assets/mouths/open/emote_happy_{mouth_index}.svg
```

### **Asset Selection Logic**

1. **Base Assets** (idle animation): Use numbered files (1.svg, 2.svg, etc.)
2. **Emote Assets**: Use emote-prefixed files (emote_happy_1.svg, etc.)
3. **Deterministic Indices**: Hash determines which variant within each category
4. **Independent States**: Eyes and mouths selected independently based on frame requirements

### **Usage Examples**

```bash
# Get specific animation frame
curl http://localhost:8000/avatar/user@example.com.svg?frame=idle_2

# Get emote expression
curl http://localhost:8000/avatar/user@example.com.svg?frame=angry

# Get all frames as bundle
curl "http://localhost:8000/avatar/user@example.com/bundle?animations=idle,happy,sad,surprised,angry,bored"
```

## 🎨 Avatar Variants

### **Asset Combinations**

- **24 open eye variants** (4 base + 20 emote variants)
- **12 closed eye variants** (2 base + 10 emote variants)
- **18 open mouth variants** (3 base + 15 emote variants)
- **42 closed mouth variants** (7 base + 35 emote variants)
- **16 hair styles** with 99 total color combinations
- **10 body shapes** (5×3 to 6×7 tile dimensions)
- **20 body colors** × **19 node colors** (always different)
- **2 feet color strategies** (match body vs match nodes)

### **Total Variants**

**1,267,200,000 unique combinations** possible with current assets

### **Collision Analysis**

- **50% collision probability** at ~34,600 users (birthday paradox)
- **Suitable for platforms** up to ~1 million users
- **100x more variety** than traditional Gravatar systems

## 🔧 Asset System

### **Current Assets**

```
Eyes: 36 variants (24 open + 12 closed, including base and emote assets)
Mouths: 60 variants (18 open + 42 closed, including base and emote assets)
Hair: 16 variants with sophisticated color/positioning systems
Body Shapes: 10 variants (width×height combinations)
Colors: 20-color carefully curated palette
```

### **Hair Asset Configuration**

Hair assets use SVG data attributes for flexible positioning and coloring:

```xml
<svg data-z-order="front"
     data-width-percent="112"
     data-position-x="cell-center"
     data-position-y="between-body-eyes"
     data-anchor="center"
     data-color='["#F34B65", "#FA709A", "#F7AB39"]'>
  <path fill="currentColor" d="..." stroke="#231F20" stroke-width="0.75"/>
</svg>
```

**Available Data Attributes:**

- `data-z-order`: "behind" or "front" rendering
- `data-width-percent`: Width as % of body width  
- `data-position-x`: "body-center", "cell-center", or percentages
- `data-position-y`: "above-body", "between-body-eyes", or percentages  
- `data-anchor`: "top", "center", or "bottom" alignment
- `data-color`: "currentColor", "contrast", hex colors, or JSON arrays

## 🚀 Deployment

### **Development Server**

```bash
# Start with auto-reload
uv run python app.py
```

### **Production Deployment**

```bash
# Install production ASGI server
uv add gunicorn

# Run with Gunicorn
uv run gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### **Docker Deployment**

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
EXPOSE 8000
CMD ["uv", "run", "python", "app.py"]
```

### **Environment Variables**

```bash
# Optional configuration
HOST=0.0.0.0
PORT=8000
CACHE_DIR=out/avatar
```

## 📊 Performance

### **Caching Strategy**

- **File-based cache** in `out/avatar/` directory
- **Hash-based filenames** for collision resistance
- **Immediate serving** of cached avatars
- **1-year HTTP cache headers** for client-side caching

### **Generation Performance**

- **Cold generation**: ~50-100ms per avatar
- **Cached serving**: ~1-5ms per avatar  
- **Concurrent requests**: Supported via FastAPI async
- **Memory usage**: Minimal (stateless generation)

## 🎮 Use Cases

### **Gravatar Replacement**

Replace Gravatar URLs with your service:

```html
<!-- Before -->
<img src="https://www.gravatar.com/avatar/hash?s=60">

<!-- After -->
<img src="https://your-service.com/avatar/user@example.com.svg">
```

### **Gaming & Applications**

```javascript
// Generate consistent user avatars
const avatarUrl = `https://your-service.com/avatar/${userId}.svg`;

// Use in chat applications
<img src={`/avatar/${username}.svg`} alt={`${username}'s avatar`} />
```

### **Bulk Asset Generation**

```bash
# Generate sprite sheets for games
uv run generate.py

# Use CSS sprites in web applications
.user-avatar { background-image: url('agents_sheet.svg'); }
.user-42 { background-position: -420px -180px; }
```

## 🛠️ Development

### **Visual Testing**

Use the included `test-grid.html` page to visually verify animations and emotes:

```bash
# Start the development server
uv run python app.py

# Open test-grid.html in your browser
open test-grid.html
# Or visit: file:///path/to/test-grid.html
```

**Features:**

- View all 4 idle frames and 5 emotes for multiple avatars
- Add custom test avatars with any input string
- Toggle idle animation to see frame cycling
- Visual feedback for current frame during animation
- Server status checking

**Test Coverage:**

Run the comprehensive test suite:

```bash
# Run all tests
uv run pytest tests/

# Run with coverage
uv run pytest tests/ --cov=. --cov-report=html

# Run specific test modules
uv run pytest tests/test_emote_system.py
uv run pytest tests/test_animation_frames.py
```

### **Generating Emote Variants**

The `generate_emote_variants.py` script creates emote-specific variants from base assets:

```bash
# Generate emote variants from base assets
uv run python generate_emote_variants.py

# This creates files like:
# - assets/eyes/open/emote_happy_1.svg (from assets/eyes/open/1.svg)
# - assets/mouths/closed/emote_sad_2.svg (from assets/mouths/closed/2.svg)
# etc.
```

**When to run this script:**

- After adding new base eye or mouth assets
- After modifying base assets and wanting to propagate changes
- When setting up the project initially

**How it works:**

1. Reads all base assets (numbered files) from eyes/open, eyes/closed, mouths/open, mouths/closed
2. For each emote (happy, sad, surprised, angry, bored), creates a copy with emote prefix
3. Preserves all SVG attributes and styling
4. Creates deterministic variants based on base asset count

### **Adding New Assets**

1. Add numbered SVG files to appropriate directories
2. Use data attributes for hair positioning/coloring
3. Generator automatically detects new assets
4. Test with `uv run avatar.py "test" --info`

### **Modifying Configuration**

Edit JSON files in `assets/`:

- `config.json` - Grid size, positioning, styling
- `colors.json` - Color palette and schemes
- `body_shapes.json` - Available body dimensions
- `probabilities.json` - Generation probabilities

### **API Development**

```bash
# Run with auto-reload
uv run python app.py

# Access API docs
open http://localhost:8000/docs

# Test endpoints
curl http://localhost:8000/avatar/test.svg
curl http://localhost:8000/avatar/test.svg/info
```

## 📈 Scaling Considerations

### **For High Traffic**

- Use **CDN** for cached avatar serving
- **Horizontal scaling** with load balancer
- **Pre-generation** for known users
- **Database integration** for user-avatar mapping

### **For Large User Bases**

- **Monitor collision rates** using hash analytics
- **Add more assets** to increase variant count
- **Implement user preferences** for customization
- **Consider PNG rendering** for better compression

## 📋 Dependencies

**Core:**

- Python 3.13+
- FastAPI 0.115+ (web service)
- uvicorn 0.32+ (ASGI server)

**Optional:**

- Pillow 11.3+ (future raster rendering)
- Gunicorn (production deployment)

## 📄 License

MIT License - Feel free to use in your projects!

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your improvements (assets, features, optimizations)
4. Submit a pull request

**Areas for Contribution:**

- New hair/eye/mouth assets
- Performance optimizations  
- Additional output formats
- Mobile-optimized variants
- Integration examples
