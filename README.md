# Upsert Context7 GitHub Action

A GitHub Action to add or update library documentation on [Context7.com](https://context7.com).

## Usage

> **Note**: Context7 operations can take several minutes for large libraries. The action has a default timeout of 30 minutes to accommodate this processing time.

### Basic Usage

Add this step to your workflow to automatically update your library's documentation on Context7:

```yaml
- name: Update Context7 Documentation
  uses: rennf93/upsert-context7@v1
  with:
    operation: refresh
```

### Full Example Workflow

```yaml
name: Update Context7 Docs

on:
  release:
    types: [ published ]
  workflow_dispatch:  # Manual trigger

jobs:
  update-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Update Context7 Documentation
        id: context7
        uses: rennf93/upsert-context7@v1
        with:
          operation: refresh

      - name: Show result
        run: |
          echo "Success: ${{ steps.context7.outputs.success }}"
          echo "Status: ${{ steps.context7.outputs.status-code }}"
          echo "Message: ${{ steps.context7.outputs.message }}"
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `operation` | Operation to perform: `add` or `refresh` | ✅ | `refresh` |
| `library-name` | Library name in format `/owner/repo` | ❌ | Auto-detected from repository |
| `repo-url` | Repository URL | ❌ | Auto-detected from repository |
| `timeout` | Request timeout in seconds | ❌ | `1800` (30 minutes) |

## Outputs

| Output | Description |
|--------|-------------|
| `success` | Whether the operation was successful (`true`/`false`) |
| `status-code` | HTTP status code from Context7 API |
| `message` | Response message from Context7 API |

## Operations

### `refresh` (Default)
Updates documentation for an existing library on Context7:

```yaml
- uses: rennf93/upsert-context7@v1
  with:
    operation: refresh
    library-name: "/owner/repo"  # Optional, auto-detected
```

### `add`
Adds a new library to Context7:

```yaml
- uses: rennf93/upsert-context7@v1
  with:
    operation: add
    repo-url: "https://github.com/owner/repo"  # Optional, auto-detected
```

## Examples

### Conditional Operations

```yaml
- name: Add to Context7 (if new release)
  if: github.event_name == 'release'
  uses: rennf93/upsert-context7@v1
  with:
    operation: add

- name: Refresh Context7 (on manual trigger)
  if: github.event_name == 'workflow_dispatch'
  uses: rennf93/upsert-context7@v1
  with:
    operation: refresh
```

### With Custom Parameters

```yaml
- uses: rennf93/upsert-context7@v1
  with:
    operation: refresh
    library-name: "/myorg/mycustomlib"
    timeout: 3600  # 1 hour for very large libraries
```

### Error Handling

```yaml
- name: Update Context7
  id: update
  uses: rennf93/upsert-context7@v1
  with:
    operation: refresh
  continue-on-error: true

- name: Handle failure
  if: steps.update.outputs.success == 'false'
  run: |
    echo "Context7 update failed: ${{ steps.update.outputs.message }}"
    # Add your custom error handling here
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This action is available under the [MIT License](LICENSE).

## Development

### Testing

The action comes with comprehensive tests to ensure reliability:

```bash
# Install dependencies
make install-dev

# Run tests
make test

# Run with UV directly
uv run pytest tests/ --cov=src --cov-report=term-missing
```

### Test Structure

- **`tests/test_context7_action.py`** - Unit tests for core functionality
- **`tests/test_integration.py`** - Integration tests with real API calls
- **`tests/test_edge_cases.py`** - Edge cases and error scenarios
- **`tests/conftest.py`** - Shared fixtures and test configuration

### Test Categories

- **Unit Tests**: Fast tests with mocked dependencies
- **Integration Tests**: Real API calls (use `--run-integration`)
- **Edge Cases**: Error handling and boundary conditions
- **Coverage**: Minimum 80% code coverage required

### Code Quality

Code quality is enforced through pre-commit hooks and GitHub Actions:

```bash
# Install pre-commit hooks
uv run pre-commit install

# Run pre-commit checks
uv run pre-commit run --all-files

# Or use make commands
make lint  # Check code quality
make fix   # Auto-fix issues
```

### Continuous Integration

Tests run automatically on:
- Push to `master` branch
- Pull requests
- Multiple Python versions (3.10, 3.11, 3.12, 3.13)
- Code quality checks (Ruff formatting/linting, mypy type checking)
- Security checks (bandit, safety)
