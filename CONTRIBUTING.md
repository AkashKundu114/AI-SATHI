# Contributing Guidelines

Thank you for your interest in contributing to AI-SATHI. This document outlines the engineering standards and workflows for the project.

## Development Environment Setup

`ash
# Clone the repository
git clone https://github.com/AkashKundu114/AI-SATHI.git
cd AI-SATHI

# Initialize virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .[test]

# Configure environment variables
cp .env.example .env
`

## Testing Protocol

All code modifications must pass the existing test suite before review.

`ash
# Execute the full offline test suite
python -m pytest tests/ -q

# Execute a specific test module
python -m pytest tests/unit/test_ledger_node.py -v

# Generate a coverage report
python -m pytest tests/ --cov=shared --cov-report=term
`

## Engineering Standards

- **Static Analysis**: Enforce code quality using uff check backend/\.
- **Type Checking**: Validate type hints using \mypy backend/shared/ backend/services/\.
- **Language Features**: Code must be compatible with Python 3.11+. Strict type hinting is required for all public interfaces.
- **Documentation**: Inline comments in production code should be minimized. Utilize comprehensive docstrings for structural documentation.

## Repository Architecture

The \ackend/\ directory structure is strictly organized:
- \ackend/services/\: Microservice components (e.g., gateway, orchestrator).
- \ackend/shared/\: Common utilities, including configuration, database ORM, guardrails, and centralized knowledge.
- \ackend/scripts/\: Administrative tooling and maintenance operations.

## Code Review Process

1. Fork the repository and isolate changes within a feature branch.
2. Ensure the complete test suite executes successfully (\python -m pytest tests/ -q\).
3. Resolve all static analysis warnings (uff check backend/\).
4. Update associated technical documentation for any modifications affecting public APIs or system architecture.
5. Submit a pull request detailing the technical justification and scope of changes.

## Licensing Agreement

By contributing to this repository, you acknowledge and agree that your contributions will be distributed under the AGPL-3.0 License.
