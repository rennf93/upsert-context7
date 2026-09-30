#!/usr/bin/env python3
"""
Upsert Context7 GitHub Action
Add or update library documentation on Context7.com
"""

import os
import sys

import requests


class Context7Action:
    """Handler for Context7 API operations"""

    def __init__(self) -> None:
        operation_raw = os.getenv("INPUT_OPERATION", "refresh").strip().lower()
        if not operation_raw:
            self.operation = "refresh"
        elif operation_raw in ["add", "refresh"]:
            self.operation = operation_raw
        else:
            self.operation = "refresh"  # Default for invalid operations
        self.library_name = os.getenv("INPUT_LIBRARY_NAME", "").strip()
        self.repo_url = os.getenv("INPUT_REPO_URL", "").strip()

        # Handle timeout
        try:
            timeout_str = os.getenv("INPUT_TIMEOUT", "1800")  # 30 minutes default
            self.timeout = int(timeout_str)
            if self.timeout <= 0:
                self.timeout = 1800  # 30 minutes
        except (ValueError, TypeError):
            self.timeout = 1800  # 30 minutes

        self.github_repository = os.getenv("GITHUB_REPOSITORY", "")
        self.github_server_url = os.getenv("GITHUB_SERVER_URL", "https://github.com")

        # Auto-detect values if not provided
        if not self.library_name and self.github_repository:
            self.library_name = f"/{self.github_repository}"

        if not self.repo_url and self.github_repository:
            self.repo_url = f"{self.github_server_url}/{self.github_repository}"

    def set_output(self, name: str, value: str) -> None:
        """Set GitHub Actions output"""
        github_output = os.getenv("GITHUB_OUTPUT")
        if github_output:
            try:
                with open(github_output, "a") as f:
                    f.write(f"{name}={value}\n")
            except OSError:
                # Fallback if file write fails
                print(f"::set-output name={name}::{value}")
        else:
            # Fallback for older runners
            print(f"::set-output name={name}::{value}")

    def log_info(self, message: str) -> None:
        """Log info message"""
        print(f"💡 {message}")

    def log_success(self, message: str) -> None:
        """Log success message"""
        print(f"✅ {message}")

    def log_warning(self, message: str) -> None:
        """Log warning message"""
        print(f"⚠️ {message}")
        print(f"::warning::{message}")

    def log_error(self, message: str) -> None:
        """Log error message"""
        print(f"❌ {message}")
        print(f"::error::{message}")

    def log_notice(self, message: str) -> None:
        """Log notice message"""
        print(f"📢 {message}")
        print(f"::notice::{message}")

    def validate_inputs(self) -> bool:
        """Validate required inputs"""
        if self.operation not in ["add", "refresh"]:
            self.log_error(
                f"Invalid operation: {self.operation}. Must be 'add' or 'refresh'"
            )
            return False

        if self.operation == "add" and not self.repo_url:
            self.log_error("repo-url is required for 'add' operation")
            return False

        if self.operation == "refresh" and not self.library_name:
            self.log_error("library-name is required for 'refresh' operation")
            return False

        return True

    def add_library(self) -> tuple[bool, int, str]:
        """Add library to Context7"""
        url = "https://context7.com/api/v1/add"
        payload = {"docsRepoUrl": self.repo_url}

        self.log_info(f"Adding library to Context7: {self.repo_url}")
        self.log_info("⏳ This may take several minutes for large libraries...")

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)

            if response.status_code in [200, 201, 202]:
                try:
                    result = response.json()
                    message = result.get("message", "Library added successfully")
                    self.log_success(f"Library added successfully: {message}")
                    return True, response.status_code, message
                except Exception:
                    message = "Library added successfully"
                    self.log_success(message)
                    return True, response.status_code, message

            elif response.status_code == 400:
                try:
                    result = response.json()
                    message = result.get("message", response.text)

                    if "already exists" in message.lower():
                        self.log_notice(f"Library already exists: {message}")
                        return True, response.status_code, message
                    else:
                        self.log_error(f"Bad request: {message}")
                        return False, response.status_code, message
                except Exception:
                    message = f"Bad request: {response.text}"
                    self.log_error(message)
                    return False, response.status_code, message

            else:
                message = f"API error (HTTP {response.status_code}): {response.text}"
                self.log_error(message)
                return False, response.status_code, message

        except requests.RequestException as e:
            message = f"Request failed: {str(e)}"
            self.log_error(message)
            return False, 0, message

    def refresh_library(self) -> tuple[bool, int, str]:
        """Refresh library documentation on Context7"""
        url = "https://context7.com/refresh-library"
        payload = {"requestedLibrary": self.library_name}

        self.log_info(f"Refreshing library documentation: {self.library_name}")
        self.log_info("⏳ This may take several minutes for large libraries...")

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)

            if response.status_code == 200:
                try:
                    result = response.json()
                    message = result.get(
                        "message", "Documentation refresh started successfully"
                    )
                    status = result.get("status", "processing")

                    self.log_success(f"Documentation refresh successful: {message}")
                    self.log_info(f"Status: {status}")

                    return True, response.status_code, message
                except Exception:
                    message = "Documentation refresh started successfully"
                    self.log_success(message)
                    return True, response.status_code, message

            else:
                message = f"API error (HTTP {response.status_code}): {response.text}"
                self.log_error(message)
                return False, response.status_code, message

        except requests.RequestException as e:
            message = f"Request failed: {str(e)}"
            self.log_error(message)
            return False, 0, message

    def run(self) -> None:
        """Main execution method"""
        self.log_info("🚀 Starting Upsert Context7 action")
        self.log_info(f"Operation: {self.operation}")
        self.log_info(f"Library name: {self.library_name}")
        self.log_info(f"Repository URL: {self.repo_url}")
        self.log_info(
            f"Request timeout: {self.timeout} seconds ({self.timeout // 60} minutes)"
        )

        # Validate inputs
        if not self.validate_inputs():
            self.set_output("success", "false")
            self.set_output("status-code", "0")
            self.set_output("message", "Invalid inputs")
            sys.exit(1)

        # Execute operation
        if self.operation == "add":
            success, status_code, message = self.add_library()
        else:  # refresh
            success, status_code, message = self.refresh_library()

        # Set outputs
        self.set_output("success", str(success).lower())
        self.set_output("status-code", str(status_code))
        self.set_output("message", message)

        if success:
            self.log_notice("🎉 Action completed successfully!")
            sys.exit(0)
        else:
            self.log_error("💥 Action failed!")
            sys.exit(1)


def main() -> None:
    """Entry point"""
    action = Context7Action()
    action.run()


if __name__ == "__main__":
    main()
