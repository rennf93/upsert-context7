#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures for Context7Action tests
"""

import os
from collections.abc import Generator

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests (may make real API calls)",
    )
    config.addinivalue_line("markers", "slow: marks tests as slow running")


@pytest.fixture(autouse=True)
def clean_environment() -> Generator[None, None, None]:
    """Clean up environment variables before each test"""
    # Store original values
    original_env = {}
    env_vars = [
        "INPUT_OPERATION",
        "INPUT_LIBRARY_NAME",
        "INPUT_REPO_URL",
        "INPUT_TIMEOUT",
        "GITHUB_REPOSITORY",
        "GITHUB_SERVER_URL",
        "GITHUB_OUTPUT",
        "GITHUB_WORKSPACE",
    ]

    for var in env_vars:
        if var in os.environ:
            original_env[var] = os.environ[var]
            del os.environ[var]

    yield

    # Restore original values
    for var, value in original_env.items():
        os.environ[var] = value


# Pytest collection hooks
def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Modify test collection to add markers based on test names"""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)

        # Mark slow tests
        if "slow" in item.nodeid.lower() or "real_api" in item.nodeid.lower():
            item.add_marker(pytest.mark.slow)


# Skip integration tests by default unless explicitly requested
def pytest_runtest_setup(item: pytest.Item) -> None:
    """Setup hook to skip integration tests unless requested"""
    # Remove the skipping logic - let integration tests run by default
    pass


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom command line options"""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that make real API calls (now runs by default)",
    )
    parser.addoption(
        "--run-slow", action="store_true", default=False, help="Run slow tests"
    )
