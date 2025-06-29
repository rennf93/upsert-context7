# Supported Python versions
PYTHON_VERSIONS = 3.10 3.11 3.12 3.13
DEFAULT_PYTHON = 3.10

# Install dependencies
.PHONY: install
install:
	@uv sync
	@find . | grep -E "(__pycache__|\\.pyc|\\.pyo|\\.pytest_cache|\\.ruff_cache|\\.mypy_cache)" | xargs rm -rf

# Install dev dependencies
.PHONY: install-dev
install-dev:
	@uv sync --extra dev
	@find . | grep -E "(__pycache__|\\.pyc|\\.pyo|\\.pytest_cache|\\.ruff_cache|\\.mypy_cache)" | xargs rm -rf

# Update dependencies
.PHONY: lock
lock:
	@uv lock
	@find . | grep -E "(__pycache__|\\.pyc|\\.pyo|\\.pytest_cache|\\.ruff_cache|\\.mypy_cache)" | xargs rm -rf

# Lint code
.PHONY: lint
lint:
	@echo "Formatting w/ Ruff..."
	@echo ''
	@uv run ruff format .
	@echo ''
	@echo ''
	@echo "Linting w/ Ruff..."
	@echo ''
	@uv run ruff check .
	@echo ''
	@echo ''
	@echo "Type checking w/ Mypy..."
	@echo ''
	@uv run mypy .
	@find . | grep -E "(__pycache__|\\.pyc|\\.pyo|\\.pytest_cache|\\.ruff_cache|\\.mypy_cache)" | xargs rm -rf

# Fix code
.PHONY: fix
fix:
	@echo "Fixing formatting w/ Ruff..."
	@echo ''
	@uv run ruff check --fix .
	@find . | grep -E "(__pycache__|\\.pyc|\\.pyo|\\.pytest_cache|\\.ruff_cache|\\.mypy_cache)" | xargs rm -rf

# Run tests (default Python version)
.PHONY: test
test:
	@echo "Running tests..."
	@echo ''
	@uv run pytest tests --cov=.
	@find . | grep -E "(__pycache__|\\.pyc|\\.pyo|\\.pytest_cache|\\.ruff_cache|\\.mypy_cache)" | xargs rm -rf

# Clean Cache Files
.PHONY: clean
clean:
	@find . | grep -E "(__pycache__|\\.pyc|\\.pyo|\\.pytest_cache|\\.ruff_cache|\\.mypy_cache)" | xargs rm -rf

# Help
.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make install            	   - Install dependencies"
	@echo "  make install-dev        	   - Install dev dependencies"
	@echo "  make lock               	   - Update dependencies"
	@echo "  make lint               	   - Run linting checks"
	@echo "  make fix                	   - Auto-fix linting issues"
	@echo "  make test               	   - Run tests with Python $(DEFAULT_PYTHON)"
	@echo "  make clean                    - Clean cache files"
	@echo "  make help             		   - Show this help message"
	@echo "  make show-python-versions     - Show supported Python versions"

# Python versions list
.PHONY: show-python-versions
show-python-versions:
	@echo "Supported Python versions: $(PYTHON_VERSIONS)"
	@echo "Default Python version: $(DEFAULT_PYTHON)"
