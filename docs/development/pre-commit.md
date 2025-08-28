# Pre-commit Setup

This project uses pre-commit hooks to ensure code quality and consistency.

## Installation

1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Install dotenv-linter (binary):
   ```bash
   # On Linux/macOS:
   curl -sSfL https://github.com/dotenv-linter/dotenv-linter/releases/latest/download/dotenv-linter-$(uname -s)-x86_64.tar.gz | tar xzf - dotenv-linter
   sudo mv dotenv-linter /usr/local/bin
   
   # Or using brew on macOS:
   brew install dotenv-linter
   ```

3. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## What's Included

- **Python Linting & Formatting**: Uses `ruff` for fast Python linting and formatting
- **Dotenv Linting**: Uses `dotenv-linter` to ensure `.env` files are properly formatted
- **General Hooks**: 
  - Trailing whitespace removal
  - End-of-file fixer (ensures files end with a newline)
  - YAML syntax checking
  - Large file detection
  - Merge conflict detection

## Running Manually

To run all hooks on all files:
```bash
pre-commit run --all-files
```

To run a specific hook:
```bash
pre-commit run dotenv-linter --all-files
pre-commit run ruff --all-files
```

## Skipping Hooks

If you need to skip hooks for a specific commit:
```bash
git commit -m "your message" --no-verify
```

## Configuration

- Pre-commit config: `.pre-commit-config.yaml`
- Ruff config: `pyproject.toml`