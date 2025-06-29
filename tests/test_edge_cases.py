#!/usr/bin/env python3
"""
Edge case tests for Context7Action GitHub Action
"""

import os
import sys
from unittest.mock import Mock, patch

import requests

# Add src to path for importing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from src.main import Context7Action


class TestContext7ActionEdgeCases:
    """Test edge cases and error scenarios"""

    def test_empty_string_inputs(self) -> None:
        """Test handling of empty string inputs"""
        os.environ["INPUT_OPERATION"] = ""
        os.environ["INPUT_LIBRARY_NAME"] = ""
        os.environ["INPUT_REPO_URL"] = ""

        action = Context7Action()

        assert action.operation == "refresh"  # Should default
        assert action.library_name == ""
        assert action.repo_url == ""
        assert action.validate_inputs() is False

    def test_whitespace_only_inputs(self) -> None:
        """Test handling of whitespace-only inputs"""
        os.environ["INPUT_OPERATION"] = "   "
        os.environ["INPUT_LIBRARY_NAME"] = "   "
        os.environ["INPUT_REPO_URL"] = "   "

        action = Context7Action()

        assert action.operation == "refresh"  # Should default after strip
        assert action.library_name == ""
        assert action.repo_url == ""

    def test_very_long_inputs(self) -> None:
        """Test handling of very long inputs"""
        long_string = "a" * 1000
        os.environ["INPUT_LIBRARY_NAME"] = f"/{long_string}/{long_string}"
        os.environ["INPUT_REPO_URL"] = f"https://github.com/{long_string}/{long_string}"

        action = Context7Action()

        # Should handle long inputs without crashing
        assert len(action.library_name) > 500
        assert len(action.repo_url) > 500

    def test_special_characters_in_inputs(self) -> None:
        """Test handling of special characters in inputs"""
        os.environ["INPUT_LIBRARY_NAME"] = "/test/repo-with-special-chars_123"
        os.environ["INPUT_REPO_URL"] = (
            "https://github.com/test/repo-with-special-chars_123"
        )

        action = Context7Action()

        assert "-" in action.library_name
        assert "_" in action.library_name
        assert "123" in action.library_name

    def test_invalid_json_response_handling(self) -> None:
        """Test handling of invalid JSON responses"""
        with patch("requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_response.text = "<html>Not JSON response</html>"
            mock_post.return_value = mock_response

            os.environ["INPUT_LIBRARY_NAME"] = "/test/repo"
            action = Context7Action()

            success, status_code, message = action.refresh_library()

            assert success is True  # Should still succeed for 200
            assert status_code == 200
            assert "Documentation refresh started successfully" in message

    def test_empty_json_response(self) -> None:
        """Test handling of empty JSON response"""
        with patch("requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {}
            mock_post.return_value = mock_response

            os.environ["INPUT_LIBRARY_NAME"] = "/test/repo"
            action = Context7Action()

            success, status_code, message = action.refresh_library()

            assert success is True
            assert status_code == 200

    def test_network_connection_error(self) -> None:
        """Test handling of network connection errors"""
        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.ConnectionError("Network unreachable")

            os.environ["INPUT_LIBRARY_NAME"] = "/test/repo"
            action = Context7Action()

            success, status_code, message = action.refresh_library()

            assert success is False
            assert status_code == 0
            assert "Network unreachable" in message

    def test_timeout_error(self) -> None:
        """Test handling of timeout errors"""
        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.Timeout("Request timed out")

            os.environ["INPUT_LIBRARY_NAME"] = "/test/repo"
            action = Context7Action()

            success, status_code, message = action.refresh_library()

            assert success is False
            assert status_code == 0
            assert "Request timed out" in message

    def test_ssl_error(self) -> None:
        """Test handling of SSL errors"""
        with patch("requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.SSLError(
                "SSL certificate verify failed"
            )

            os.environ["INPUT_LIBRARY_NAME"] = "/test/repo"
            action = Context7Action()

            success, status_code, message = action.refresh_library()

            assert success is False
            assert status_code == 0
            assert "SSL certificate verify failed" in message

    def test_unicode_characters(self) -> None:
        """Test handling of unicode characters in inputs"""
        os.environ["INPUT_LIBRARY_NAME"] = "/test/репозиторий"
        os.environ["INPUT_REPO_URL"] = "https://github.com/test/репозиторий"

        action = Context7Action()

        # Should handle unicode without crashing
        assert "репозиторий" in action.library_name
        assert action.repo_url.endswith("/test/репозиторий")

    def test_github_repository_with_dots(self) -> None:
        """Test handling of repository names with dots"""
        os.environ["GITHUB_REPOSITORY"] = "user/repo.name.with.dots"
        os.environ["GITHUB_SERVER_URL"] = "https://github.com"

        action = Context7Action()

        assert action.library_name == "/user/repo.name.with.dots"
        assert action.repo_url.endswith("/user/repo.name.with.dots")

    def test_malformed_github_server_url(self) -> None:
        """Test handling of malformed GitHub server URL"""
        os.environ["GITHUB_REPOSITORY"] = "user/repo"
        os.environ["GITHUB_SERVER_URL"] = "not-a-valid-url"

        action = Context7Action()

        # Should still construct some URL
        assert len(action.repo_url) > 0
        assert action.repo_url.endswith("/user/repo")

    def test_missing_github_server_url(self) -> None:
        """Test handling when GITHUB_SERVER_URL is missing"""
        os.environ["GITHUB_REPOSITORY"] = "user/repo"
        # Don't set GITHUB_SERVER_URL

        action = Context7Action()

        # Should default to github.com
        assert action.repo_url.startswith("https://github.com")
        assert action.library_name == "/user/repo"

    def test_zero_timeout(self) -> None:
        """Test handling of zero timeout"""
        os.environ["INPUT_TIMEOUT"] = "0"

        action = Context7Action()

        # Should default to 30 for invalid timeout
        assert action.timeout == 1800

    def test_negative_timeout(self) -> None:
        """Test handling of negative timeout"""
        os.environ["INPUT_TIMEOUT"] = "-5"

        action = Context7Action()

        # Should default to 30 for invalid timeout
        assert action.timeout == 1800

    def test_float_timeout(self) -> None:
        """Test handling of float timeout"""
        os.environ["INPUT_TIMEOUT"] = "30.5"

        action = Context7Action()

        # Should default to 30 for invalid timeout
        assert action.timeout == 1800

    def test_very_large_timeout(self) -> None:
        """Test handling of very large timeout"""
        os.environ["INPUT_TIMEOUT"] = "99999"

        action = Context7Action()

        # Should accept large but reasonable timeout
        assert action.timeout == 99999

    @patch("builtins.open", side_effect=PermissionError("Permission denied"))
    def test_github_output_permission_error(self, mock_open: Mock) -> None:
        """Test handling of permission error when writing to GITHUB_OUTPUT"""
        os.environ["GITHUB_OUTPUT"] = "/tmp/github_output"

        action = Context7Action()

        # Should not crash when unable to write to file
        action.set_output("test_key", "test_value")
        # Should fall back to print method

    def test_missing_slash_in_library_name(self) -> None:
        """Test auto-detection when library name doesn't start with slash"""
        os.environ["GITHUB_REPOSITORY"] = "user/repo"

        action = Context7Action()

        # Should add the leading slash
        assert action.library_name.startswith("/")
        assert action.library_name == "/user/repo"

    def test_library_name_already_has_slash(self) -> None:
        """Test when manually provided library name already has slash"""
        os.environ["INPUT_LIBRARY_NAME"] = "/user/repo"

        action = Context7Action()

        # Should not double-add slashes
        assert action.library_name == "/user/repo"
        assert not action.library_name.startswith("//")

    def test_case_sensitivity_in_operation(self) -> None:
        """Test various case combinations for operation"""
        test_cases = ["REFRESH", "Refresh", "rEfReShh", "ADD", "Add", "aDd"]

        for op in test_cases:
            os.environ["INPUT_OPERATION"] = op
            action = Context7Action()
            expected = op.lower()
            if expected not in ["refresh", "add"]:
                expected = "refresh"  # default
            assert action.operation in ["refresh", "add"]
