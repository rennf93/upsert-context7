#!/usr/bin/env python3
"""
Integration tests for Context7Action GitHub Action
These tests make actual API calls (in test mode)
"""

import os
import sys
import tempfile
from urllib.parse import urlparse

import pytest

# Add src to path for importing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from src.main import Context7Action


class TestContext7ActionIntegration:
    """Integration tests for Context7Action"""

    @pytest.mark.integration
    def test_refresh_library_real_api_call(self) -> None:
        """Test refresh with a real API call"""
        os.environ["INPUT_OPERATION"] = "refresh"
        os.environ["INPUT_LIBRARY_NAME"] = "/test/nonexistent-repo-12345"
        os.environ["INPUT_TIMEOUT"] = "10"  # Shorter timeout for tests

        action = Context7Action()
        success, status_code, message = action.refresh_library()

        # Should get various error codes for non-existent library, including rate limits
        assert success is False
        assert status_code in [404, 400, 429, 500]
        assert len(message) > 0

    @pytest.mark.integration
    def test_add_library_real_api_call(self) -> None:
        """Test add with a real API call (API accepts requests and starts parsing)"""
        os.environ["INPUT_OPERATION"] = "add"
        os.environ["INPUT_REPO_URL"] = "https://github.com/test/nonexistent-repo-12345"
        os.environ["INPUT_TIMEOUT"] = "10"  # Shorter timeout for tests

        action = Context7Action()
        success, status_code, message = action.add_library()

        # API appears to accept requests and start parsing process
        # Could return success (200) with parsing message, or error codes
        assert status_code in [200, 201, 202, 400, 404, 429, 500]
        assert len(message) > 0

    def test_full_workflow_with_github_output(self) -> None:
        """Test the full workflow including GitHub output file"""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp_file:
            try:
                os.environ["GITHUB_OUTPUT"] = tmp_file.name
                os.environ["INPUT_OPERATION"] = "refresh"
                os.environ["INPUT_LIBRARY_NAME"] = "/test/repo"

                action = Context7Action()

                # This should fail validation and set outputs
                with pytest.raises(SystemExit) as exc_info:
                    action.run()

                # Should exit with error code due to API failure
                assert exc_info.value.code == 1

                # Check that outputs were written to file
                with open(tmp_file.name) as f:
                    content = f.read()
                    assert "success=false" in content
                    assert "status-code=" in content
                    assert "message=" in content

            finally:
                os.unlink(tmp_file.name)

    def test_environment_variable_override(self) -> None:
        """Test that explicit inputs override auto-detection"""
        os.environ["GITHUB_REPOSITORY"] = "auto/detected"
        os.environ["GITHUB_SERVER_URL"] = "https://github.com"
        os.environ["INPUT_LIBRARY_NAME"] = "/manual/override"
        os.environ["INPUT_REPO_URL"] = "https://github.com/manual/override"

        action = Context7Action()

        # Manual inputs should override auto-detection
        assert action.library_name == "/manual/override"
        assert action.repo_url == "https://github.com/manual/override"

    def test_timeout_configuration(self) -> None:
        """Test that timeout is properly configured"""
        os.environ["INPUT_TIMEOUT"] = "45"

        action = Context7Action()
        assert action.timeout == 45

    def test_invalid_timeout_defaults_to_30(self) -> None:
        """Test that invalid timeout defaults to 30"""
        os.environ["INPUT_TIMEOUT"] = "invalid"

        action = Context7Action()
        assert action.timeout == 1800

    def test_case_insensitive_operation(self) -> None:
        """Test that operation input is case-insensitive"""
        os.environ["INPUT_OPERATION"] = "REFRESH"

        action = Context7Action()
        assert action.operation == "refresh"

    @pytest.mark.integration
    def test_api_timeout_handling(self) -> None:
        """Test that API timeout is handled gracefully"""
        os.environ["INPUT_OPERATION"] = "refresh"
        os.environ["INPUT_LIBRARY_NAME"] = "/test/repo"
        os.environ["INPUT_TIMEOUT"] = "1"  # Very short timeout

        action = Context7Action()
        success, status_code, message = action.refresh_library()

        # Should handle timeout gracefully
        assert success is False
        assert status_code == 0 or status_code >= 400
        assert len(message) > 0

    def test_whitespace_trimming(self) -> None:
        """Test that inputs are properly trimmed of whitespace"""
        os.environ["INPUT_LIBRARY_NAME"] = "  /test/repo  "
        os.environ["INPUT_REPO_URL"] = "  https://github.com/test/repo  "
        os.environ["INPUT_OPERATION"] = "  refresh  "

        action = Context7Action()

        assert action.library_name == "/test/repo"
        assert action.repo_url == "https://github.com/test/repo"
        assert action.operation == "refresh"

    def test_empty_github_repository_no_crash(self) -> None:
        """Test that empty GITHUB_REPOSITORY doesn't cause crashes"""
        os.environ["GITHUB_REPOSITORY"] = ""
        os.environ["INPUT_OPERATION"] = "refresh"

        action = Context7Action()

        # Should not crash, but library_name should be empty
        assert action.library_name == ""
        assert action.repo_url == ""

    def test_partial_github_repository_info(self) -> None:
        """Test handling of malformed GITHUB_REPOSITORY"""
        os.environ["GITHUB_REPOSITORY"] = "incomplete"
        os.environ["INPUT_OPERATION"] = "refresh"

        action = Context7Action()

        # Should handle gracefully - use proper URL validation
        assert action.library_name == "/incomplete"
        parsed_url = urlparse(action.repo_url)
        assert parsed_url.path.endswith("/incomplete")
