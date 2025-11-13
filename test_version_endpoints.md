# Version Tracking Implementation Test Plan

## Overview

Added version tracking to the FastAPI web service to expose AVATAR_SYSTEM_VERSION = "2.0" from door_agents.py.

## Changes Made

### 1. Import Version Constant (Line 21)

```python
from door_agents import DoorAgentConfig, DoorAgentGenerator, AVATAR_SYSTEM_VERSION
```

### 2. New /version Endpoint (Lines 594-597)

```python
@app.get("/version")
async def get_version():
    """Return the avatar system version."""
    return {"avatar_system_version": AVATAR_SYSTEM_VERSION}
```

### 3. Version Headers Added to All Avatar Endpoints

#### SVG Endpoint (Line 378)

Added `"X-Avatar-System-Version": AVATAR_SYSTEM_VERSION` to response headers

#### PNG Endpoint (Line 414)

Added `"X-Avatar-System-Version": AVATAR_SYSTEM_VERSION` to response headers

#### Bundle GET Endpoint (Line 553)

Added `"X-Avatar-System-Version": AVATAR_SYSTEM_VERSION` to response headers

#### Bundle POST Endpoint (Line 590)

Added `"X-Avatar-System-Version": AVATAR_SYSTEM_VERSION` to response headers

### 4. Updated Root Endpoint Documentation (Lines 324, 326-330, 346)

- Added `"avatar_system_version": AVATAR_SYSTEM_VERSION` to root response
- Added "endpoints" section with /version link
- Added feature note about version tracking

## Manual Testing Instructions

Once cairo library is installed, test with:

```bash
# Start server
uv run uvicorn app:app --host 0.0.0.0 --port 8000

# Test /version endpoint
curl http://localhost:8000/version
# Expected: {"avatar_system_version": "2.0"}

# Test SVG endpoint version header
curl -I http://localhost:8000/avatar/test@example.com.svg
# Expected: X-Avatar-System-Version: 2.0 in headers

# Test PNG endpoint version header
curl -I http://localhost:8000/avatar/test@example.com.png
# Expected: X-Avatar-System-Version: 2.0 in headers

# Test bundle endpoint version header
curl -I "http://localhost:8000/avatar/test@example.com/bundle?animations=idle"
# Expected: X-Avatar-System-Version: 2.0 in headers

# Test root endpoint includes version
curl http://localhost:8000/ | python3 -m json.tool
# Expected: "avatar_system_version": "2.0" in response
```

## Summary

All avatar-related endpoints now expose version information in two ways:

1. **Dedicated /version endpoint**: Returns JSON with avatar_system_version
2. **X-Avatar-System-Version header**: All avatar endpoints (SVG, PNG, bundle) include this header

This allows clients to:

- Query the version explicitly via /version
- Detect version from any avatar response headers
- Understand breaking changes between v1.x and v2.0 systems
