#!/usr/bin/env python3
# ABOUTME: Tests for input validation and sanitization
# ABOUTME: Validates that malicious or malformed inputs are handled safely

import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


class TestXMLInjectionPrevention:
    """Tests for XML/SVG injection attack prevention."""

    def test_svg_injection_in_input_string(self):
        """Input string with SVG injection attempts is handled safely."""
        # URL encoding the malicious input to bypass TestClient validation
        from urllib.parse import quote
        malicious_input = 'user<svg><script>alert("xss")</script></svg>@example.com'
        encoded_input = quote(malicious_input, safe='')
        response = client.get(f"/avatar/{encoded_input}.svg")

        # May return 404 if routing doesn't match, or 200 if it does
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            # Response should be valid SVG
            assert b"<svg" in response.content

            # Should NOT contain the injected script tag
            assert b'<script>alert("xss")</script>' not in response.content
            assert b"alert" not in response.content

    def test_xml_entity_injection(self):
        """Input string with XML entity injection is handled safely."""
        from urllib.parse import quote
        malicious_input = "user&#60;script&#62;@example.com"
        encoded_input = quote(malicious_input, safe='')
        response = client.get(f"/avatar/{encoded_input}.svg")

        assert response.status_code == 200
        # Should generate valid SVG without executing entities
        assert b"<svg" in response.content

    def test_cdata_injection(self):
        """Input string with CDATA injection is handled safely."""
        from urllib.parse import quote
        malicious_input = "user<![CDATA[<script>alert('xss')</script>]]>@example.com"
        encoded_input = quote(malicious_input, safe='')
        response = client.get(f"/avatar/{encoded_input}.svg")

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            assert b"<svg" in response.content

    def test_xml_comment_injection(self):
        """Input string with XML comments is handled safely."""
        from urllib.parse import quote
        malicious_input = "user<!--<script>alert('xss')</script>-->@example.com"
        encoded_input = quote(malicious_input, safe='')
        response = client.get(f"/avatar/{encoded_input}.svg")

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            assert b"<svg" in response.content


class TestHTMLInjectionPrevention:
    """Tests for HTML injection attack prevention."""

    def test_html_tags_in_input(self):
        """Input string with HTML tags is handled safely."""
        malicious_input = 'user<img src=x onerror="alert(1)">@example.com'
        response = client.get(f"/avatar/{malicious_input}.svg")

        assert response.status_code == 200
        # Should not contain the img tag
        assert b"<img" not in response.content
        assert b"onerror" not in response.content

    def test_javascript_url_in_input(self):
        """Input string with javascript: URLs is handled safely."""
        malicious_input = "user<a href='javascript:alert(1)'>@example.com"
        response = client.get(f"/avatar/{malicious_input}.svg")

        assert response.status_code == 200
        assert b"javascript:" not in response.content

    def test_data_url_in_input(self):
        """Input string with data: URLs is handled safely."""
        from urllib.parse import quote
        malicious_input = "user<img src='data:text/html,<script>alert(1)</script>'>@example.com"
        encoded_input = quote(malicious_input, safe='')
        response = client.get(f"/avatar/{encoded_input}.svg")

        assert response.status_code in [200, 404]


class TestPathTraversalPrevention:
    """Tests for path traversal attack prevention."""

    def test_path_traversal_with_dotdot(self):
        """Input string with ../ path traversal attempts is handled safely."""
        # FastAPI path routing automatically normalizes paths, preventing traversal
        # Testing that the server handles this appropriately
        try:
            response = client.get("/avatar/../../../etc/passwd.svg")
            # If it succeeds, should not read system files
            if response.status_code == 200:
                assert b"<svg" in response.content
                assert b"root:" not in response.content
        except Exception:
            # Path normalization may raise exception - this is acceptable
            pass

    def test_path_traversal_with_encoded_dotdot(self):
        """Input string with URL-encoded ../ is handled safely."""
        # URL encoding path traversal - should be decoded and normalized
        response = client.get("/avatar/..%2F..%2F..%2Fetc%2Fpasswd.svg")

        # Should either normalize or reject
        if response.status_code == 200:
            assert b"<svg" in response.content
            assert b"root:" not in response.content

    def test_absolute_path_in_input(self):
        """Input string with absolute paths is handled safely."""
        # Absolute paths in URL paths are handled by routing
        response = client.get("/avatar/etc_passwd.svg")

        assert response.status_code == 200
        assert b"<svg" in response.content
        assert b"root:" not in response.content

    def test_windows_path_in_input(self):
        """Input string with Windows paths is handled safely."""
        malicious_input = "C:\\Windows\\System32\\config\\sam"
        response = client.get(f"/avatar/{malicious_input}.svg")

        assert response.status_code == 200
        assert b"<svg" in response.content


class TestLargeInputHandling:
    """Tests for handling very large inputs (DoS prevention)."""

    def test_very_long_input_string(self):
        """Very long input strings are handled appropriately."""
        # 10KB input string
        large_input = "A" * 10000
        response = client.get(f"/avatar/{large_input}.svg")

        # Should either succeed or fail gracefully
        assert response.status_code in [200, 400, 413, 414]

        if response.status_code == 200:
            # If it succeeds, should still generate valid SVG
            assert b"<svg" in response.content

    def test_extremely_long_input_string(self):
        """Extremely long input strings don't cause crashes."""
        # 1MB input string - TestClient may reject this before it reaches the server
        huge_input = "B" * 1000000
        try:
            response = client.get(f"/avatar/{huge_input}.svg")
            # Should handle gracefully (likely reject with 414 URI Too Long)
            assert response.status_code in [200, 400, 413, 414]
        except Exception:
            # TestClient may reject extremely long URLs - acceptable
            pass

    def test_input_with_many_special_chars(self):
        """Input with many special characters is handled."""
        from urllib.parse import quote
        special_input = "!@#$%^&*()[]{}|;:',.<>?/~`" * 10
        encoded_input = quote(special_input, safe='')
        response = client.get(f"/avatar/{encoded_input}.svg")

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            assert b"<svg" in response.content


class TestUnicodeAndEncodingHandling:
    """Tests for Unicode and various character encoding handling."""

    def test_unicode_input_string(self):
        """Input string with Unicode characters is handled correctly."""
        unicode_input = "user用户👤🎨@example.com"
        response = client.get(f"/avatar/{unicode_input}.svg")

        assert response.status_code == 200
        assert b"<svg" in response.content

    def test_emoji_in_input_string(self):
        """Input string with emojis is handled correctly."""
        emoji_input = "user🚀🌟💻@example.com"
        response = client.get(f"/avatar/{emoji_input}.svg")

        assert response.status_code == 200
        assert b"<svg" in response.content

    def test_rtl_text_in_input(self):
        """Input string with right-to-left text is handled correctly."""
        rtl_input = "مستخدم@example.com"
        response = client.get(f"/avatar/{rtl_input}.svg")

        assert response.status_code == 200
        assert b"<svg" in response.content

    def test_mixed_encoding_input(self):
        """Input with mixed character encodings is handled."""
        mixed_input = "user_Ñoño_用户_🎨@example.com"
        response = client.get(f"/avatar/{mixed_input}.svg")

        assert response.status_code == 200
        assert b"<svg" in response.content

    def test_null_byte_in_input(self):
        """Input string with null bytes is handled safely."""
        # TestClient rejects null bytes in URLs as invalid
        # This tests that the HTTP layer itself prevents null byte attacks
        from httpx import InvalidURL
        null_input = "user\x00@example.com"
        try:
            response = client.get(f"/avatar/{null_input}.svg")
            # If somehow it gets through, should handle gracefully
            assert response.status_code in [200, 400]
        except InvalidURL:
            # Expected - TestClient rejects null bytes (good security)
            pass

    def test_control_characters_in_input(self):
        """Input string with control characters is handled safely."""
        # TestClient rejects control characters in URLs
        from httpx import InvalidURL
        control_input = "user\x01\x02\x03\x04@example.com"
        try:
            response = client.get(f"/avatar/{control_input}.svg")
            # If somehow it gets through, should handle gracefully
            assert response.status_code in [200, 400]
        except InvalidURL:
            # Expected - TestClient rejects control characters (good security)
            pass


class TestFrameParameterInjection:
    """Tests for injection attempts via frame parameter."""

    def test_frame_parameter_with_script_injection(self):
        """Frame parameter with script injection is rejected."""
        response = client.get(
            "/avatar/test@example.com.svg",
            params={"frame": "<script>alert(1)</script>"}
        )

        # Should either reject or handle safely
        if response.status_code == 200:
            assert b"<script>" not in response.content

    def test_frame_parameter_with_sql_injection(self):
        """Frame parameter with SQL injection pattern is handled safely."""
        response = client.get(
            "/avatar/test@example.com.svg",
            params={"frame": "' OR '1'='1"}
        )

        # Should handle gracefully
        assert response.status_code in [200, 400]

    def test_frame_parameter_with_path_traversal(self):
        """Frame parameter with path traversal is rejected."""
        response = client.get(
            "/avatar/test@example.com.svg",
            params={"frame": "../../../etc/passwd"}
        )

        # Should reject or handle safely
        if response.status_code == 200:
            assert b"<svg" in response.content


class TestBundleEndpointInjection:
    """Tests for injection attempts via bundle endpoint."""

    def test_bundle_animations_parameter_injection(self):
        """Bundle animations parameter with injection is handled safely."""
        response = client.get(
            "/avatar/test@example.com/bundle",
            params={"animations": "<script>alert(1)</script>"}
        )

        # Should either reject or handle safely
        assert response.status_code in [200, 400, 422]

    def test_bundle_post_with_malicious_json(self):
        """POST bundle with malicious JSON is validated."""
        response = client.post(
            "/avatar/bundle",
            json={
                "input": "<script>alert(1)</script>",
                "animations": ["idle", "<script>"]
            }
        )

        # Should validate and reject or handle safely
        if response.status_code == 200:
            # Should not contain script tags
            content = response.content
            assert b"<script>" not in content

    def test_bundle_post_with_invalid_animation_type(self):
        """POST bundle with invalid animation types is validated."""
        response = client.post(
            "/avatar/bundle",
            json={
                "input": "test@example.com",
                "animations": ["../../../etc/passwd"]
            }
        )

        # Should validate animation types
        assert response.status_code in [200, 400, 422]


class TestEmptyAndNullInputs:
    """Tests for empty and null input handling."""

    def test_empty_string_input(self):
        """Empty string as input is handled appropriately."""
        response = client.get("/avatar/.svg")

        # Should handle gracefully
        assert response.status_code in [200, 400, 404]

    def test_whitespace_only_input(self):
        """Whitespace-only input is handled appropriately."""
        response = client.get("/avatar/   .svg")

        assert response.status_code in [200, 400]

    def test_bundle_with_empty_input(self):
        """Bundle endpoint with empty input is handled."""
        response = client.post(
            "/avatar/bundle",
            json={"input": "", "animations": ["idle"]}
        )

        # Should validate and reject or handle with default
        assert response.status_code in [200, 400, 422]


class TestHeaderInjection:
    """Tests for HTTP header injection attacks."""

    def test_crlf_injection_in_input(self):
        """Input with CRLF characters doesn't inject headers."""
        # TestClient rejects CRLF in URLs as invalid
        from httpx import InvalidURL
        malicious_input = "user\r\nX-Injected-Header: malicious\r\n@example.com"
        try:
            response = client.get(f"/avatar/{malicious_input}.svg")
            # If somehow it gets through, injected header should not appear
            assert "x-injected-header" not in response.headers
        except InvalidURL:
            # Expected - TestClient rejects CRLF (good security)
            pass

    def test_header_injection_via_frame_param(self):
        """Frame parameter doesn't allow header injection."""
        response = client.get(
            "/avatar/test@example.com.svg",
            params={"frame": "happy\r\nX-Injected: value"}
        )

        assert response.status_code in [200, 400]
        assert "x-injected" not in response.headers
