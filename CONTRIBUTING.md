# Contributing to Block Friends Avatar System

Thank you for your interest in contributing to the Block Friends avatar system! This document provides guidelines for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Adding New Assets](#adding-new-assets)

## Code of Conduct

We expect all contributors to be respectful and professional. This is an open-source project built with ❤️ in Chicago.

## Getting Started

### Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/) for dependency management
- Git for version control

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/2389-research/block-friends.git
cd block-friends

# Install dependencies
uv sync

# Run the development server
uv run python app.py
```

The API will be available at `http://localhost:8000`

### Project Structure

```
block-friends/
├── app.py                  # FastAPI web service
├── door_agents.py          # Core avatar generation library
├── avatar.py               # CLI avatar generator
├── generate.py             # Sprite sheet generator
├── assets/                 # SVG assets (eyes, mouths, hair)
├── static/                 # HTML pages and demos
├── tests/                  # Test suite
├── docs/                   # Documentation
└── scripts/                # Utility scripts
```

## Development Workflow

### 1. Create a Branch

```bash
# For features
git checkout -b feat/your-feature-name

# For bug fixes
git checkout -b fix/bug-description

# For documentation
git checkout -b docs/documentation-update
```

### 2. Make Changes

- Write clean, readable code
- Follow existing code style and patterns
- Add tests for new functionality
- Update documentation as needed

### 3. Run Tests

```bash
# Run all tests
uv run python -m pytest tests/ -v

# Run specific test file
uv run python -m pytest tests/test_api_endpoints.py -v

# Run with coverage
uv run python -m pytest tests/ --cov=. --cov-report=html
```

### 4. Commit Changes

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Feature
git commit -m "feat: add new hair style asset"

# Bug fix
git commit -m "fix: correct eye positioning for happy emote"

# Documentation
git commit -m "docs: update API usage examples"

# Test
git commit -m "test: add tests for bundle generation"

# Chore
git commit -m "chore: update dependencies"
```

**Important:** Always include the Claude Code footer in your commits:

```
🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### 5. Push and Create PR

```bash
git push origin your-branch-name
gh pr create --base main --head your-branch-name
```

## Coding Standards

### Python Style

- Follow PEP 8 guidelines
- Use type hints for function parameters and return values
- Use descriptive variable and function names
- Keep functions focused and single-purpose
- Maximum line length: 100 characters

### File Headers

All Python files should start with ABOUTME comments:

```python
#!/usr/bin/env python3
# ABOUTME: Brief description of what this file does
# ABOUTME: Second line if needed for clarity
```

### Documentation

- Add docstrings to all public functions and classes
- Use clear, concise language
- Include parameter descriptions and return types
- Add usage examples for complex functions

Example:

```python
async def get_or_generate_avatar_content(input_string: str, frame: str = "neutral") -> tuple[str, str]:
    """
    Gets avatar SVG content from file cache or generates it, ensuring thread-safety.
    Returns (svg_content, hash_hex) tuple.

    Args:
        input_string: Input string for deterministic generation
        frame: Animation frame (default: "neutral")

    Returns:
        Tuple of (svg_content, hash_hex)
    """
```

## Testing

### Writing Tests

- Write tests for all new features
- Ensure existing tests pass before submitting
- Aim for high test coverage (>80%)
- Use descriptive test names

### Test Structure

```python
class TestFeatureName:
    """Tests for feature description."""

    def test_specific_behavior(self):
        """Test should verify this specific behavior."""
        # Arrange
        input_data = "test@example.com"

        # Act
        result = function_under_test(input_data)

        # Assert
        assert result.status_code == 200
```

### Running Tests

```bash
# All tests
uv run python -m pytest tests/ -v

# Specific test class
uv run python -m pytest tests/test_api_endpoints.py::TestAvatarSVGEndpoint -v

# Specific test
uv run python -m pytest tests/test_api_endpoints.py::TestAvatarSVGEndpoint::test_deterministic -v

# With coverage report
uv run python -m pytest tests/ --cov=. --cov-report=term-missing
```

## Submitting Changes

### Pull Request Guidelines

1. **Title**: Use conventional commit format
   - `feat: add feature description`
   - `fix: bug description`
   - `docs: documentation update`
   - `test: test description`

2. **Description**: Include:
   - Summary of changes
   - Motivation and context
   - Testing performed
   - Screenshots (if applicable)
   - Related issues

3. **Checklist**:
   - [ ] Tests pass locally
   - [ ] New tests added for new features
   - [ ] Documentation updated
   - [ ] CHANGELOG.md updated
   - [ ] Code follows style guidelines
   - [ ] Commit messages follow convention

### PR Template

```markdown
## Summary
Brief description of changes

## Changes
- Change 1
- Change 2
- Change 3

## Testing
- [ ] All tests pass
- [ ] New tests added
- [ ] Manual testing performed

## Checklist
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Follows coding standards
```

### Code Review Process

1. Automated checks must pass (if configured)
2. At least one maintainer review required
3. Address review comments
4. Maintain clean commit history
5. Squash commits if requested

## Adding New Assets

### SVG Asset Guidelines

#### Eyes

Place in `assets/eyes/open/` or `assets/eyes/closed/`:

```bash
# For base eyes (used in idle animation)
assets/eyes/open/5.svg
assets/eyes/closed/3.svg

# For emote-specific eyes
assets/eyes/open/emote_happy_5.svg
assets/eyes/closed/emote_sad_3.svg
```

Requirements:
- Use 0.75px stroke width
- Use `#231F20` for outlines
- Include pupils with `#2B2727` fill
- Keep viewBox consistent

#### Mouths

Place in `assets/mouths/open/` or `assets/mouths/closed/`:

```bash
# For base mouths (used in idle animation)
assets/mouths/open/4.svg
assets/mouths/closed/8.svg

# For emote-specific mouths
assets/mouths/open/emote_surprised_4.svg
assets/mouths/closed/emote_bored_8.svg
```

Requirements:
- Use 0.75px stroke width
- Use `#231F20` for outlines
- Keep viewBox consistent

#### Hair

Place in `assets/hair/`:

```bash
assets/hair/17.svg
```

Requirements:
- Include positioning data attributes
- Use `fill="currentColor"` for paths
- Use 0.75px stroke width

Example hair asset with positioning:

```xml
<svg data-z-order="front"
     data-width-percent="100"
     data-position-x="body-center"
     data-position-y="above-body"
     data-anchor="top"
     data-color='["#F34B65", "#FA709A"]'
     viewBox="0 0 10 10"
     xmlns="http://www.w3.org/2000/svg">
  <path fill="currentColor" d="..." stroke="#231F20" stroke-width="0.75"/>
</svg>
```

### Testing New Assets

After adding assets:

```bash
# Generate test avatar
uv run python avatar.py "test@example.com" --info

# Check visual output
uv run python app.py
# Visit http://localhost:8000/avatar/test@example.com.svg
```

## Questions?

- **Issues**: [GitHub Issues](https://github.com/2389-research/block-friends/issues)
- **Discussions**: [GitHub Discussions](https://github.com/2389-research/block-friends/discussions)
- **Documentation**: See [docs/](./docs/) directory

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.

---

Thank you for contributing to Block Friends! 🎨
