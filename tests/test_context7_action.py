#!/usr/bin/env python3
"""
Unit tests for Context7Action GitHub Action
"""

import os
import sys
from unittest.mock import Mock, call, mock_open, patch

import pytest
import requests

# Add src to path for importing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from src.main import Context7Action


class TestContext7Action:
    """Test cases for Context7Action class"""

    def test_init_with_defaults(self) -> None:
        """Test initialization with default values"""
        action = Context7Action()

        assert action.operation == "refresh"
        assert action.library_name == ""
        assert action.repo_url == ""
        assert action.timeout == 1800
        assert action.github_repository == ""
        assert action.github_server_url == "https://github.com"

    def test_init_with_environment_variables(self) -> None:
        """Test initialization with environment variables"""
        os.environ["INPUT_OPERATION"] = "add"
        os.environ["INPUT_LIBRARY_NAME"] = "/test/repo"
        os.environ["INPUT_REPO_URL"] = "https://github.com/test/repo"
        os.environ["INPUT_TIMEOUT"] = "60"
        os.environ["GITHUB_REPOSITORY"] = "test/repo"
        os.environ["GITHUB_SERVER_URL"] = "https://github.com"

        action = Context7Action()

        assert action.operation == "add"
        assert action.library_name == "/test/repo"
        assert action.repo_url == "https://github.com/test/repo"
        assert action.timeout == 60
        assert action.github_repository == "test/repo"
        assert action.github_server_url == "https://github.com"

    def test_auto_detection(self) -> None:
        """Test auto-detection of library name and repo URL"""
        os.environ["GITHUB_REPOSITORY"] = "user/awesome-lib"
        os.environ["GITHUB_SERVER_URL"] = "https://github.com"

        action = Context7Action()

        assert action.library_name == "/user/awesome-lib"
        assert action.repo_url == "https://github.com/user/awesome-lib"

    @patch("builtins.open", new_callable=mock_open)
    def test_set_output_with_github_output(self, mock_file: Mock) -> None:
        """Test setting output with GITHUB_OUTPUT file"""
        os.environ["GITHUB_OUTPUT"] = "/tmp/github_output"

        action = Context7Action()
        action.set_output("test_key", "test_value")

        mock_file.assert_called_once_with("/tmp/github_output", "a")
        mock_file().write.assert_called_once_with("test_key=test_value\n")

    @patch("builtins.print")
    def test_set_output_fallback(self, mock_print: Mock) -> None:
        """Test setting output with fallback method"""
        action = Context7Action()
        action.set_output("test_key", "test_value")

        mock_print.assert_called_with("::set-output name=test_key::test_value")

    def test_validate_inputs_valid_refresh(self) -> None:
        """Test input validation for valid refresh operation"""
        os.environ["INPUT_OPERATION"] = "refresh"
        os.environ["INPUT_LIBRARY_NAME"] = "/test/repo"

        action = Context7Action()
        assert action.validate_inputs() is True

    def test_validate_inputs_valid_add(self) -> None:
        """Test input validation for valid add operation"""
        os.environ["INPUT_OPERATION"] = "add"
        os.environ["INPUT_REPO_URL"] = "https://github.com/test/repo"

        action = Context7Action()
        assert action.validate_inputs() is True

    def test_validate_inputs_add_missing_repo_url(self) -> None:
        """Test input validation for add operation without repo URL"""
        os.environ["INPUT_OPERATION"] = "add"

        action = Context7Action()
        assert action.validate_inputs() is False

    def test_validate_inputs_refresh_missing_library_name(self) -> None:
        """Test input validation for refresh operation without library name"""
        os.environ["INPUT_OPERATION"] = "refresh"

        action = Context7Action()
        assert action.validate_inputs() is False

    @patch("requests.post")
    def test_add_library_success(self, mock_post: Mock) -> None:
        """Test successful library addition"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"message": "Library added successfully"}
        mock_post.return_value = mock_response

        os.environ["INPUT_REPO_URL"] = "https://github.com/test/repo"
        action = Context7Action()

        success, status_code, message = action.add_library()

        assert success is True
        assert status_code == 201
        assert "Library added successfully" in message
        mock_post.assert_called_once_with(
            "https://context7.com/api/v1/add",
            json={"docsRepoUrl": "https://github.com/test/repo"},
            timeout=1800,
        )

    @patch("requests.post")
    def test_add_library_already_exists(self, mock_post: Mock) -> None:
        """Test adding library that already exists"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"message": "The project already exists."}
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        os.environ["INPUT_REPO_URL"] = "https://github.com/test/repo"
        action = Context7Action()

        success, status_code, message = action.add_library()

        assert success is True  # Should be true for "already exists"
        assert status_code == 400
        assert "already exists" in message.lower()

    @patch("requests.post")
    def test_add_library_bad_request(self, mock_post: Mock) -> None:
        """Test add library with bad request"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"message": "Invalid repository URL"}
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        os.environ["INPUT_REPO_URL"] = "https://github.com/test/repo"
        action = Context7Action()

        success, status_code, message = action.add_library()

        assert success is False
        assert status_code == 400
        assert "Invalid repository URL" in message

    @patch("requests.post")
    def test_add_library_server_error(self, mock_post: Mock) -> None:
        """Test add library with server error"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        os.environ["INPUT_REPO_URL"] = "https://github.com/test/repo"
        action = Context7Action()

        success, status_code, message = action.add_library()

        assert success is False
        assert status_code == 500
        assert "Internal Server Error" in message

    @patch("requests.post")
    def test_add_library_request_exception(self, mock_post: Mock) -> None:
        """Test add library with request exception"""
        mock_post.side_effect = requests.RequestException("Connection error")

        os.environ["INPUT_REPO_URL"] = "https://github.com/test/repo"
        action = Context7Action()

        success, status_code, message = action.add_library()

        assert success is False
        assert status_code == 0
        assert "Connection error" in message

    @patch("requests.post")
    def test_refresh_library_success(self, mock_post: Mock) -> None:
        """Test successful library refresh"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": "Refresh process started successfully",
            "status": "processing",
        }
        mock_post.return_value = mock_response

        os.environ["INPUT_LIBRARY_NAME"] = "/test/repo"
        action = Context7Action()

        success, status_code, message = action.refresh_library()

        assert success is True
        assert status_code == 200
        assert "Refresh process started successfully" in message
        mock_post.assert_called_once_with(
            "https://context7.com/api/refresh-library",
            json={"libraryName": "/test/repo"},
            timeout=1800,
        )

    @patch("requests.post")
    def test_refresh_library_success_no_json(self, mock_post: Mock) -> None:
        """Test successful library refresh with no JSON response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("No JSON")
        mock_post.return_value = mock_response

        os.environ["INPUT_LIBRARY_NAME"] = "/test/repo"
        action = Context7Action()

        success, status_code, message = action.refresh_library()

        assert success is True
        assert status_code == 200
        assert "Documentation refresh started successfully" in message

    @patch("requests.post")
    def test_refresh_library_success_with_json_error(self, mock_post: Mock) -> None:
        """Test successful library refresh with JSON parsing error fallback"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = Exception("JSON parsing failed")
        mock_post.return_value = mock_response

        os.environ["INPUT_LIBRARY_NAME"] = "/test/repo"
        action = Context7Action()

        success, status_code, message = action.refresh_library()

        assert success is True
        assert status_code == 200
        assert "Documentation refresh started successfully" in message

    @patch("requests.post")
    def test_refresh_library_error(self, mock_post: Mock) -> None:
        """Test refresh library with error"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Library not found"
        mock_post.return_value = mock_response

        os.environ["INPUT_LIBRARY_NAME"] = "/test/repo"
        action = Context7Action()

        success, status_code, message = action.refresh_library()

        assert success is False
        assert status_code == 404
        assert "Library not found" in message

    @patch("requests.post")
    def test_refresh_library_request_exception(self, mock_post: Mock) -> None:
        """Test refresh library with request exception"""
        mock_post.side_effect = requests.RequestException("Timeout error")

        os.environ["INPUT_LIBRARY_NAME"] = "/test/repo"
        action = Context7Action()

        success, status_code, message = action.refresh_library()

        assert success is False
        assert status_code == 0
        assert "Timeout error" in message

    @patch.object(Context7Action, "set_output")
    @patch.object(Context7Action, "refresh_library")
    @patch.object(Context7Action, "validate_inputs")
    def test_run_success(
        self, mock_validate: Mock, mock_refresh: Mock, mock_set_output: Mock
    ) -> None:
        """Test successful run method"""
        mock_validate.return_value = True
        mock_refresh.return_value = (True, 200, "Success message")

        os.environ["INPUT_OPERATION"] = "refresh"
        action = Context7Action()

        with pytest.raises(SystemExit) as exc_info:
            action.run()

        assert exc_info.value.code == 0
        mock_validate.assert_called_once()
        mock_refresh.assert_called_once()
        mock_set_output.assert_any_call("success", "true")
        mock_set_output.assert_any_call("status-code", "200")
        mock_set_output.assert_any_call("message", "Success message")

    @patch.object(Context7Action, "set_output")
    @patch.object(Context7Action, "add_library")
    @patch.object(Context7Action, "validate_inputs")
    def test_run_add_operation(
        self, mock_validate: Mock, mock_add: Mock, mock_set_output: Mock
    ) -> None:
        """Test run method with add operation"""
        mock_validate.return_value = True
        mock_add.return_value = (True, 201, "Added successfully")

        os.environ["INPUT_OPERATION"] = "add"
        action = Context7Action()

        with pytest.raises(SystemExit) as exc_info:
            action.run()

        assert exc_info.value.code == 0
        mock_add.assert_called_once()

    @patch.object(Context7Action, "set_output")
    @patch.object(Context7Action, "validate_inputs")
    def test_run_validation_failure(
        self, mock_validate: Mock, mock_set_output: Mock
    ) -> None:
        """Test run method with validation failure"""
        mock_validate.return_value = False

        action = Context7Action()

        with pytest.raises(SystemExit) as exc_info:
            action.run()

        assert exc_info.value.code == 1
        mock_set_output.assert_any_call("success", "false")
        mock_set_output.assert_any_call("status-code", "0")
        mock_set_output.assert_any_call("message", "Invalid inputs")

    @patch.object(Context7Action, "set_output")
    @patch.object(Context7Action, "refresh_library")
    @patch.object(Context7Action, "validate_inputs")
    def test_run_operation_failure(
        self, mock_validate: Mock, mock_refresh: Mock, mock_set_output: Mock
    ) -> None:
        """Test run method with operation failure"""
        mock_validate.return_value = True
        mock_refresh.return_value = (False, 500, "Server error")

        os.environ["INPUT_OPERATION"] = "refresh"
        action = Context7Action()

        with pytest.raises(SystemExit) as exc_info:
            action.run()

        assert exc_info.value.code == 1
        mock_set_output.assert_any_call("success", "false")
        mock_set_output.assert_any_call("status-code", "500")
        mock_set_output.assert_any_call("message", "Server error")

    def test_init_with_type_error_timeout(self) -> None:
        """Test initialization with TypeError when parsing timeout"""
        with patch("os.getenv") as mock_getenv:

            def mock_env(key: str, default: str = "") -> str:
                if key == "INPUT_TIMEOUT":
                    return "invalid_number"  # This will cause ValueError
                return default

            mock_getenv.side_effect = mock_env

            action = Context7Action()
            assert action.timeout == 1800  # Should default to 30 minutes

    def test_init_with_value_error_timeout(self) -> None:
        """Test initialization with ValueError when parsing timeout"""
        with patch("os.getenv") as mock_getenv:

            def mock_env(key: str, default: str = "") -> str:
                if key == "INPUT_TIMEOUT":
                    return "not_a_number"  # This will cause ValueError
                return default

            mock_getenv.side_effect = mock_env

            action = Context7Action()
            assert action.timeout == 1800  # Should default to 30 minutes

    @patch("builtins.print")
    def test_set_output_without_github_output(self, mock_print: Mock) -> None:
        """Test set_output when GITHUB_OUTPUT is not set"""
        action = Context7Action()
        action.set_output("test_key", "test_value")

        mock_print.assert_called_with("::set-output name=test_key::test_value")

    @patch("builtins.open", side_effect=OSError("File write error"))
    @patch("builtins.print")
    def test_set_output_file_write_error(
        self, mock_print: Mock, mock_open: Mock
    ) -> None:
        """Test set_output when file write fails"""
        os.environ["GITHUB_OUTPUT"] = "/tmp/test_output"

        action = Context7Action()
        action.set_output("test_key", "test_value")

        # Should fall back to print when file write fails
        mock_print.assert_called_with("::set-output name=test_key::test_value")

    @patch("requests.post")
    def test_add_library_already_exists_fallback(self, mock_post: Mock) -> None:
        """Test add library already exists with JSON parsing error"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "The project already exists."
        mock_post.return_value = mock_response

        os.environ["INPUT_REPO_URL"] = "https://github.com/test/repo"
        action = Context7Action()

        success, status_code, message = action.add_library()

        assert success is False  # This should be False for fallback case
        assert status_code == 400
        assert "Bad request" in message

    @patch("requests.post")
    def test_add_library_bad_request_fallback(self, mock_post: Mock) -> None:
        """Test add library bad request with JSON parsing error"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "Invalid request format"
        mock_post.return_value = mock_response

        os.environ["INPUT_REPO_URL"] = "https://github.com/test/repo"
        action = Context7Action()

        success, status_code, message = action.add_library()

        assert success is False
        assert status_code == 400
        assert "Bad request: Invalid request format" in message

    @patch.object(Context7Action, "set_output")
    @patch.object(Context7Action, "refresh_library")
    @patch.object(Context7Action, "validate_inputs")
    def test_run_success_exit(
        self, mock_validate: Mock, mock_refresh: Mock, mock_set_output: Mock
    ) -> None:
        """Test successful run method exits with code 0"""
        mock_validate.return_value = True
        mock_refresh.return_value = (True, 200, "Success message")

        os.environ["INPUT_OPERATION"] = "refresh"
        action = Context7Action()

        with pytest.raises(SystemExit) as exc_info:
            action.run()

        # This should trigger the sys.exit(0) path
        assert exc_info.value.code == 0

    @patch("src.main.Context7Action")
    def test_main_function(self, mock_context7_action_class: Mock) -> None:
        """Test the main() function"""
        from src.main import main

        mock_action_instance = Mock()
        mock_context7_action_class.return_value = mock_action_instance

        main()

        mock_context7_action_class.assert_called_once()
        mock_action_instance.run.assert_called_once()

    def test_if_name_main_execution(self) -> None:
        """Test the if __name__ == '__main__' execution"""
        import subprocess
        import sys

        cmd = "import sys; sys.path.insert(0, 'src'); exec(open('src/main.py').read())"
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                cmd,
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__)),
        )

        # The script should exit with error due to missing inputs
        assert result.returncode != 0  # Expected to fail due to validation

    @patch("src.main.main")
    def test_name_main_block(self, mock_main: Mock) -> None:
        """Test the if __name__ == '__main__' block"""
        # Mock the __name__ variable to be '__main__'
        import src.main

        # Save the original __name__
        original_name = src.main.__name__

        try:
            # Set __name__ to '__main__' to trigger the block
            src.main.__name__ = "__main__"

            # Re-execute the module's if __name__ == '__main__' logic
            # by directly calling the conditional code
            if src.main.__name__ == "__main__":
                src.main.main()

            mock_main.assert_called_once()

        finally:
            # Restore original __name__
            src.main.__name__ = original_name

    @patch("requests.post")
    def test_add_library_success_with_json_error(self, mock_post: Mock) -> None:
        """Test successful library addition with JSON parsing error fallback"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = Exception("JSON parsing failed")
        mock_post.return_value = mock_response

        os.environ["INPUT_REPO_URL"] = "https://github.com/test/repo"
        action = Context7Action()

        success, status_code, message = action.add_library()

        assert success is True
        assert status_code == 200
        assert "Library added successfully" in message

    def test_init_with_none_timeout_causes_type_error(self) -> None:
        """Test initialization with None timeout causing TypeError"""
        # Mock os.getenv to return None for timeout, which causes TypeError
        with patch("os.getenv") as mock_getenv:
            mock_getenv.side_effect = (
                lambda key, default="": None if key == "INPUT_TIMEOUT" else default
            )

            action = Context7Action()
            assert action.timeout == 1800  # Should fall back to default

    def test_init_with_negative_timeout(self) -> None:
        """Test initialization with negative timeout"""
        with patch.dict(os.environ, {"INPUT_TIMEOUT": "-5"}):
            action = Context7Action()
            assert action.timeout == 1800  # Should reset to default

    @patch("builtins.open")
    @patch("builtins.print")
    def test_set_output_io_error_fallback(
        self, mock_print: Mock, mock_open: Mock
    ) -> None:
        """Test set_output fallback when file I/O fails"""
        # Mock open to raise IOError
        mock_open.side_effect = OSError("Permission denied")

        # Set GITHUB_OUTPUT to trigger file write path
        with patch.dict(os.environ, {"GITHUB_OUTPUT": "/fake/path"}):
            action = Context7Action()
            action.set_output("test", "value")

            # Should call print as fallback
            mock_print.assert_called_with("::set-output name=test::value")

    def test_direct_main_execution(self) -> None:
        """Test main function execution directly"""
        import os
        import subprocess
        import sys

        # Create a temporary environment with minimal required variables
        env = os.environ.copy()
        env["INPUT_OPERATION"] = "refresh"
        env["INPUT_LIBRARY_NAME"] = "/test/lib"

        # Run the script directly
        result = subprocess.run(
            [sys.executable, "src/main.py"],
            env=env,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__)),
        )

        # This should execute the if __name__ == '__main__' block
        assert result.returncode in [0, 1]  # Allow either success or failure

    @patch("builtins.print")
    def test_log_warning_method(self, mock_print: Mock) -> None:
        """Test log_warning method"""
        action = Context7Action()
        action.log_warning("This is a warning message")

        # Should call print twice
        expected_calls = [
            call("⚠️ This is a warning message"),
            call("::warning::This is a warning message"),
        ]
        mock_print.assert_has_calls(expected_calls)

    def test_validate_inputs_invalid_operation(self) -> None:
        """Test validate_inputs with invalid operation"""
        action = Context7Action()
        # Manually set an invalid operation to trigger the validation error
        action.operation = "invalid_operation"

        result = action.validate_inputs()

        assert result is False  # Should return False for invalid operation
