# Contributing to AI-SATHI

Thank you for your interest in contributing to AI-SATHI! This document provides guidelines for contributing to the project.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/AkashKundu114/AI-SATHI.git
cd AI-SATHI

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .[test]

# Copy environment config
cp .env.example .env
```

## Running Tests

```bash
# Full test suite (390 tests, all offline, no API keys needed)
python -m pytest tests/ -q

# Specific test file
python -m pytest tests/unit/test_ledger_node.py -v

# With coverage
python -m pytest tests/ --cov=shared --cov-report=term
```

## Code Style

- **Linting**: `ruff check backend/`
- **Type checking**: `mypy backend/shared/ backend/services/`
- Python 3.11+, type hints on all public functions
- No comments in production code (docstrings only where needed)

## Project Structure

All backend Python code lives under `backend/`:
- `backend/services/` - Microservice modules (gateway, orchestrator, etc.)
- `backend/shared/` - Shared utilities (config, db, guardrails, i18n, knowledge)
- `backend/scripts/` - Admin and maintenance scripts

## Pull Request Process

1. Fork the repository and create a feature branch
2. Ensure all 390 tests pass: `python -m pytest tests/ -q`
3. Run linting: `ruff check backend/`
4. Update documentation if your change affects the public API
5. Submit a pull request with a clear description of changes

## License

By contributing, you agree that your contributions will be licensed under the AGPL-3.0 License.
