# Contributing Guidelines

Thank you for helping improve AI-SATHI. This document outlines how to set up your local development environment, run tests, adhere to project conventions, and submit contributions.

## Development Environment Setup

### 1. Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher (for frontend development)
- Docker and Docker Compose (recommended for local database setup)
- Git

### 2. Backend Setup

```bash
# Clone the repository
git clone https://github.com/AkashKundu114/AI-SATHI.git
cd AI-SATHI

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Linux or macOS:
source .venv/bin/activate
# On Windows PowerShell:
.venv\Scripts\Activate.ps1

# Install runtime and development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .[test]

# Create local environment configuration
cp .env.example .env
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend development server starts at `http://localhost:5173` and proxies API requests to `http://localhost:8000`.

## Testing Protocol

All code changes must pass the offline test suite before a pull request can be accepted. The test suite does not require network access or live API credentials.

```bash
# Run the complete test suite (390 tests)
python -m pytest tests/ -q

# Run quick smoke tests
make test-fast

# Run a specific test module
python -m pytest tests/unit/test_ledger_node.py -v

# Run with test coverage output
python -m pytest tests/ --cov=shared --cov-report=term
```

## Engineering Standards

- **Code Quality**: Run `ruff check backend/` to catch syntax issues, unused imports, and style violations.
- **Type Safety**: Verify static type hints with `mypy backend/shared/ backend/services/`.
- **Financial Logic**: Never allow language models to generate or guess numerical financial values. All currency calculations, cost floors, margins, and totals must be computed in standard Python code.
- **Error Handling**: All external API calls (Sarvam, Azure, WhatsApp) must be wrapped with timeouts, circuit breakers, and localized fallback error messages. Unhandled exceptions must never crash the service turn.
- **Documentation**: Write clear docstrings for public classes and functions. Keep inline comments focused on non-obvious business logic or dialect edge cases.

## Repository Organization

The repository follows a service-oriented structure:

- `backend/services/`: Independent services for the API gateway, LangGraph orchestrator, voice gateway, PDF generator, vision pipeline, document search, and market analysis.
- `backend/shared/`: Shared utilities including database sessions, rate limiting, financial guardrails, number converters, and security logging.
- `backend/scripts/`: Setup, migration, database seeding, and maintenance scripts.
- `frontend/`: React 18 single-page application built with Vite and Tailwind CSS.
- `tests/`: Offline unit and integration test suites with synthetic fixtures.
- `docs/`: In-depth architecture guides, product specifications, security reviews, and runbooks.

## Pull Request and Release Workflow

1. Create a descriptive branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-fix-name
   ```
2. Make your changes and write unit tests for any new behavior or bug fixes.
3. Ensure all tests and linters pass locally:
   ```bash
   ruff check backend/
   mypy backend/shared/ backend/services/
   python -m pytest tests/ -q
   ```
4. Commit your changes with clear, imperative commit messages (for example, `fix: normalize phone numbers before creating user`).
5. Push your branch and open a pull request against `main`. Describe what you changed, why the change was needed, and how you tested it.
6. Once merged, releases and tags follow semantic versioning (`vMAJOR.MINOR.PATCH`). Repository tags are published directly:
   ```bash
   git tag -a v2.1.0 -m "Release v2.1.0: web UI persistence and auth fixes"
   git push origin v2.1.0
   ```

## Licensing

By contributing to AI-SATHI, you agree that your contributions are licensed under the [AGPL-3.0 License](LICENSE).
