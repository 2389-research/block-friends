# Security Policy

## Supported Versions

Only the latest `main` branch and the most recent tagged release receive
security updates.

| Version | Supported |
| ------- | --------- |
| 2.x     | ✅        |
| 1.x     | ❌        |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, email **security@2389.ai** with:

- A description of the vulnerability
- Steps to reproduce
- The impact you believe it has
- Any suggested mitigation, if you have one

You should receive a response within **5 business days**. If the issue is
confirmed, we will work on a fix and coordinate a disclosure timeline with
you. We appreciate responsible disclosure and will credit reporters in the
release notes for the fix, unless you prefer to remain anonymous.

## Scope

This project ships a public HTTP API. In particular, we care about:

- Authentication / authorization bypasses
- Server-side request forgery or path traversal in the avatar endpoints
- SVG or PNG rendering issues that could execute untrusted content in a
  browser (XSS via generated assets, etc.)
- Rate limiting or DoS-vector regressions
- Dependency vulnerabilities that affect the running service

Out of scope:

- Findings that require compromising the host or CI environment
- Social engineering of maintainers
- Attacks on infrastructure we don't operate (upstream registries, GitHub, etc.)
