"""
Security and input sanitization tests.

Tests for XSS, injection attacks, and input validation security.
"""

import pytest
from fastapi.testclient import TestClient
from app import app
from door_agents import DoorAgentGenerator, DoorAgentConfig

client = TestClient(app)
config = DoorAgentConfig()
generator = DoorAgentGenerator(config)


class TestXSSPrevention:
    """Tests for XSS attack prevention in SVG generation."""

    def test_script_tag_injection_in_input(self):
        """Input with <script> tags doesn't execute in SVG."""
        malicious_input = "<script>alert('XSS')</script>@example.com"
        response = client.get(f"/avatar/{malicious_input}.svg")

        assert response.status_code == 200
        svg_content = response.content.decode('utf-8')

        # Check that script tags are not directly included in dangerous way
        # SVG should be safe - either escaped or not included
        # The input goes through hash, so it won't directly appear as script
        assert '<svg' in svg_content

        # If the malicious input somehow appears, it should be escaped
        if '<script>' in svg_content:
            # This would be a security issue
            pytest.fail("Unescaped script tag found in SVG output")

    def test_javascript_protocol_injection(self):
        """Input with javascript: protocol doesn't execute."""
        malicious_input = "javascript:alert('XSS')@example.com"
        response = client.get(f"/avatar/{malicious_input}.svg")

        assert response.status_code == 200
        svg_content = response.content.decode('utf-8')

        # Check that javascript: protocol is not included in href or xlink:href
        if 'javascript:' in svg_content.lower():
            # Check if it's in a dangerous context (href attributes)
            if 'href' in svg_content.lower():
                # This could be a security issue
                assert 'href="javascript:' not in svg_content.lower(), \
                    "JavaScript protocol found in href attribute"

    def test_svg_injection_attempt(self):
        """Input attempting to inject SVG elements is safe."""
        malicious_input = "<svg><circle onload='alert(1)'/></svg>@example.com"
        response = client.get(f"/avatar/{malicious_input}.svg")

        assert response.status_code == 200
        svg_content = response.content.decode('utf-8')

        # The malicious input goes through hash, so shouldn't directly appear
        # Check for event handlers that could execute JavaScript
        assert 'onload=' not in svg_content.lower() or \
               'onload="alert' not in svg_content.lower(), \
               "Potentially dangerous onload handler found"

    def test_html_entity_injection(self):
        """HTML entities in input don't cause XSS."""
        malicious_input = "&lt;script&gt;alert('XSS')&lt;/script&gt;@example.com"
        response = client.get(f"/avatar/{malicious_input}.svg")

        assert response.status_code == 200
        # Should generate valid avatar regardless of input
        assert response.headers["content-type"] == "image/svg+xml"

    def test_svg_event_handler_injection(self):
        """SVG event handlers in input don't execute."""
        malicious_input = "test' onclick='alert(1)'@example.com"
        response = client.get(f"/avatar/{malicious_input}.svg")

        assert response.status_code == 200
        svg_content = response.content.decode('utf-8')

        # Check that onclick or other event handlers aren't present in output
        # (input goes through hash, so shouldn't directly appear)
        assert 'onclick=' not in svg_content.lower() or \
               "onclick='alert" not in svg_content.lower(), \
               "Potentially dangerous onclick handler found"


class TestPathTraversalPrevention:
    """Tests for path traversal attack prevention."""

    def test_directory_traversal_in_input(self):
        """Input with ../ doesn't cause path traversal."""
        malicious_input = "../../etc/passwd"
        response = client.get(f"/avatar/{malicious_input}.svg")

        assert response.status_code == 200
        # Should generate avatar based on hash, not access file system with input directly
        svg_content = response.content.decode('utf-8')
        assert '<svg' in svg_content

        # Should not contain file system content
        assert 'root:' not in svg_content  # Common in /etc/passwd

    def test_absolute_path_in_input(self):
        """Input with absolute paths is safe."""
        malicious_input = "/etc/passwd@example.com"
        response = client.get(f"/avatar/{malicious_input}.svg")

        assert response.status_code == 200
        # Should safely generate avatar
        assert response.headers["content-type"] == "image/svg+xml"

    def test_windows_path_traversal(self):
        """Windows-style path traversal is prevented."""
        malicious_input = "..\\..\\windows\\system32\\config\\sam"
        response = client.get(f"/avatar/{malicious_input}.svg")

        assert response.status_code == 200
        # Should safely generate avatar
        assert response.headers["content-type"] == "image/svg+xml"

    def test_null_byte_injection(self):
        """Null bytes in input don't cause path traversal."""
        malicious_input = "test@example.com\\x00.txt"
        response = client.get(f"/avatar/{malicious_input}.svg")

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]


class TestSQLInjectionPrevention:
    """Tests for SQL injection prevention (defense in depth)."""

    def test_sql_injection_in_input(self):
        """SQL injection patterns in input are safe."""
        malicious_input = "' OR '1'='1@example.com"
        response = client.get(f"/avatar/{malicious_input}.svg")

        assert response.status_code == 200
        # Should safely generate avatar (no SQL used, but testing defense in depth)
        assert response.headers["content-type"] == "image/svg+xml"

    def test_sql_union_injection(self):
        """SQL UNION injection patterns are safe."""
        malicious_input = "test' UNION SELECT * FROM users--@example.com"
        response = client.get(f"/avatar/{malicious_input}.svg")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/svg+xml"

    def test_sql_drop_table(self):
        """SQL DROP TABLE patterns are safe."""
        malicious_input = "'; DROP TABLE users;--@example.com"
        response = client.get(f"/avatar/{malicious_input}.svg")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/svg+xml"


class TestCommandInjectionPrevention:
    """Tests for command injection prevention."""

    def test_shell_command_injection(self):
        """Shell command injection patterns are safe."""
        malicious_input = "test@example.com; ls -la"
        response = client.get(f"/avatar/{malicious_input}.svg")

        assert response.status_code == 200
        svg_content = response.content.decode('utf-8')

        # Should not execute commands or contain command output
        assert '<svg' in svg_content
        # Command output indicators should not be present
        assert 'total ' not in svg_content  # Common ls -la output

    def test_pipe_command_injection(self):
        """Pipe command injection is prevented."""
        malicious_input = "test@example.com | cat /etc/passwd"
        response = client.get(f"/avatar/{malicious_input}.svg")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/svg+xml"

    def test_backtick_command_injection(self):
        """Backtick command execution is prevented."""
        malicious_input = "test@example.com`whoami`"
        response = client.get(f"/avatar/{malicious_input}.svg")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/svg+xml"


class TestDOSPrevention:
    """Tests for DOS attack prevention."""

    def test_extremely_long_input_string(self):
        """Extremely long input strings are handled safely."""
        # 100KB input string
        malicious_input = "a" * 100000
        response = client.get(f"/avatar/{malicious_input}.svg")

        # Should either succeed (hash handles it) or return appropriate error
        assert response.status_code in [200, 400, 414, 500]

        # Should not cause server crash (if we get here, server is still running)

    def test_repeated_special_characters(self):
        """Input with many repeated special characters is handled."""
        malicious_input = "../" * 1000
        response = client.get(f"/avatar/{malicious_input}.svg")

        # Should handle gracefully
        assert response.status_code in [200, 400, 414]

    def test_unicode_overflow_attempt(self):
        """Unicode overflow attempts are handled safely."""
        # Various Unicode characters that might cause issues
        malicious_input = "\u0000" * 100 + "test@example.com"
        response = client.get(f"/avatar/{malicious_input}.svg")

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]


class TestFrameParameterSecurity:
    """Tests for frame parameter security."""

    def test_frame_parameter_injection(self):
        """Frame parameter doesn't allow injection."""
        response = client.get("/avatar/test@example.com.svg?frame=<script>alert(1)</script>")

        # Should handle safely - either accept as valid frame name or reject
        assert response.status_code in [200, 400, 422]

        if response.status_code == 200:
            svg_content = response.content.decode('utf-8')
            # Should not contain unescaped script tag
            assert '<script>alert' not in svg_content

    def test_frame_parameter_path_traversal(self):
        """Frame parameter doesn't allow path traversal."""
        response = client.get("/avatar/test@example.com.svg?frame=../../etc/passwd")

        # Should handle safely
        assert response.status_code in [200, 400, 422]

        if response.status_code == 200:
            svg_content = response.content.decode('utf-8')
            # Should not contain file system content
            assert 'root:' not in svg_content


class TestBundleSecurityValidation:
    """Tests for bundle generation security."""

    def test_bundle_animation_parameter_injection(self):
        """Bundle animations parameter doesn't allow injection."""
        response = client.get("/avatar/test@example.com/bundle?animations=<script>alert(1)</script>")

        # Should handle safely
        assert response.status_code in [200, 400, 422]

    def test_bundle_post_request_validation(self):
        """POST bundle validates input properly."""
        # Test with malicious input
        response = client.post(
            "/avatar/bundle",
            json={
                "input": "<script>alert('XSS')</script>",
                "animations": ["idle"]
            }
        )

        # Should generate safely or return error
        assert response.status_code in [200, 400, 422]

        if response.status_code == 200:
            # Should be a valid ZIP
            assert response.content[:4] == b'PK\x03\x04'

    def test_bundle_post_with_injection_in_animations(self):
        """POST bundle validates animations array."""
        response = client.post(
            "/avatar/bundle",
            json={
                "input": "test@example.com",
                "animations": ["idle", "<script>alert(1)</script>"]
            }
        )

        # Should handle safely
        assert response.status_code in [200, 400, 422]


class TestTransitionSecurityValidation:
    """Tests for transition endpoint security."""

    def test_transition_emote_parameter_injection(self):
        """Transition emote parameter doesn't allow injection."""
        response = client.get("/avatar/test@example.com/transition/<script>alert(1)</script>/50")

        # Should reject or handle safely
        assert response.status_code in [400, 422, 500]

    def test_transition_weight_parameter_validation(self):
        """Transition weight parameter is properly validated."""
        # Test various invalid weight values
        test_cases = [
            ("abc", [400, 422]),  # Non-numeric
            ("-1", [400, 422, 500]),  # Negative
            ("999999", [400, 422, 500]),  # Too large
            ("1.5", [200, 400, 422]),  # Decimal (might be accepted)
        ]

        for weight, expected_codes in test_cases:
            response = client.get(f"/avatar/test@example.com/transition/happy/{weight}")
            assert response.status_code in expected_codes, \
                f"Weight {weight} should return one of {expected_codes}, got {response.status_code}"


class TestContentTypeValidation:
    """Tests for content type validation and spoofing prevention."""

    def test_svg_endpoint_correct_content_type(self):
        """SVG endpoint returns correct content type."""
        response = client.get("/avatar/test@example.com.svg")

        assert response.status_code == 200
        assert "image/svg+xml" in response.headers["content-type"]

    def test_png_endpoint_correct_content_type(self):
        """PNG endpoint returns correct content type."""
        response = client.get("/avatar/test@example.com.png")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    def test_bundle_endpoint_correct_content_type(self):
        """Bundle endpoint returns correct content type."""
        response = client.get("/avatar/test@example.com/bundle")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"

    def test_content_type_matches_actual_content(self):
        """Content type header matches actual content."""
        # Test SVG
        response = client.get("/avatar/test@example.com.svg")
        assert response.content.startswith(b'<svg') or response.content.startswith(b'<?xml')

        # Test PNG
        response = client.get("/avatar/test@example.com.png")
        assert response.content[:8] == b'\x89PNG\r\n\x1a\n'

        # Test ZIP
        response = client.get("/avatar/test@example.com/bundle")
        assert response.content[:4] == b'PK\x03\x04'


class TestCachePoisoning:
    """Tests for cache poisoning prevention."""

    def test_different_inputs_dont_collide(self):
        """Different inputs generate different cache entries."""
        response1 = client.get("/avatar/user1@example.com.svg")
        response2 = client.get("/avatar/user2@example.com.svg")

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Different inputs should produce different avatars
        assert response1.content != response2.content

        # Different ETags
        assert response1.headers["etag"] != response2.headers["etag"]

    def test_cache_key_includes_frame_parameter(self):
        """Cache key properly includes frame parameter."""
        response1 = client.get("/avatar/test@example.com.svg?frame=happy")
        response2 = client.get("/avatar/test@example.com.svg?frame=sad")

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Same input, different frames should both work correctly
        # (they might be different or might be universal SVG with different initial states)
        svg1 = response1.content.decode('utf-8')
        svg2 = response2.content.decode('utf-8')

        assert '<svg' in svg1
        assert '<svg' in svg2
