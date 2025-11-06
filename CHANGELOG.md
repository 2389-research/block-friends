# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Rate limiting on API endpoints (PR #10)
  - 100 requests/minute for SVG/PNG endpoints
  - 10 requests/minute for bundle endpoints
- Security headers middleware (PR #11)
  - X-Content-Type-Options: nosniff
  - X-Frame-Options: SAMEORIGIN
  - X-XSS-Protection: 1; mode=block
  - Referrer-Policy: strict-origin-when-cross-origin
- Comprehensive API integration tests (PR #12)
  - 30 tests covering all endpoints
  - Determinism validation
  - Frame parameter testing
  - Cache and security header validation
- Project documentation
  - CONTRIBUTING.md with development workflow
  - CHANGELOG.md for version tracking
  - Audit report (docs/AUDIT-2025-10-28.md)

### Changed
- Updated idle animation from 4 to 10 frames (PR #2)
  - More natural animation with varied expressions
  - Updated bundle generation and API metadata

### Security
- Added rate limiting to prevent abuse and DoS attacks
- Added security headers to all HTTP responses
- Maintained permissive CORS for public API usage

## [2.0.0] - 2025-10-01

### Added
- Universal SVG generation with 20 animation states
- Multi-frame animation system
  - 10 idle animation frames
  - 5 emote expressions (happy, sad, surprised, angry, bored)
  - 5 vowel mouth shapes for lip-sync
- PDF bundle generation endpoint
- PNG rendering support via CairoSVG
- FastAPI web service with auto-generated docs
- File-based caching for performance
- Version tracking via headers and /version endpoint
- Deterministic generation from any input string
- 1.27 billion unique variants

### Changed
- **BREAKING:** Hash byte allocation changed to support emote system
  - v1.x used 2 byte indices for eyes/mouths
  - v2.0 uses 4 byte indices (open_eye, closed_eye, open_mouth, closed_mouth)
  - Same inputs will generate **different avatars** in v2.0
- **BREAKING:** Asset structure reorganized
  - Assets moved from flat structure to open/closed subdirectories
  - v1.x: `assets/eyes/1.svg`, `assets/mouths/1.svg`
  - v2.0: `assets/eyes/open/1.svg`, `assets/eyes/closed/1.svg`, etc.
- Improved hair positioning system with data attributes
- Enhanced animation frame control

### Removed
- Backward compatibility with v1.x avatars
- No migration path from v1.x to v2.0

## [1.0.0] - 2024-09-15

### Added
- Initial release of sprite maker
- Sprite sheet generation (400 agents in 20×20 grid)
- CLI avatar generator
- Deterministic generation from input strings
- SVG output format
- Basic eye and mouth assets
- Hair style system with color variants
- Body shape variations
- Color palette system

### Features
- ~42 million unique variants
- File-based output
- CSV configuration export

---

## Version History Summary

- **v2.0.0**: Major rewrite with animation system and web API (October 2025)
- **v1.0.0**: Initial sprite maker release (September 2024)

## Migration Guides

### v1.x to v2.0

**There is no migration path.** Version 2.0 introduces breaking changes to hash allocation that affect all avatars. If you need to preserve existing avatar appearances, continue using v1.x.

If migrating:
1. Accept that avatars will look different
2. Clear all cached v1.x avatars
3. Regenerate all avatars with v2.0
4. Update any hardcoded asset paths to new structure

## Links

- [Full Documentation](./README.md)
- [API Documentation](http://localhost:8000/docs)
- [Contributing Guide](./CONTRIBUTING.md)
- [GitHub Repository](https://github.com/2389-research/block-friends)
