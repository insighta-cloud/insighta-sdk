# Contributing to insighta-sdk

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Development Setup

### Requirements

- Python 3.10+
- pip

### Installation

```bash
git clone https://github.com/insighta-cloud/insighta-sdk.git
cd insighta-sdk
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

## Code Style

- Follow PEP 8
- All comments and docstrings in English
- Type hints required for public APIs
- Use `Decimal` for financial values, never `float`

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new API method
fix: correct rate lookup for edge case
docs: update README
test: add missing test for merge_and_sort_groups
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Write tests for new functionality
4. Ensure all tests pass (`pytest`)
5. Submit a pull request against `main`

## Multilingual Support (i18n)

This project uses **English** as the primary language for:
- Source code, comments, and docstrings
- README and documentation
- Commit messages and PR descriptions

User-facing messages (CLI output, error messages) may support multiple locales via the i18n system in `insighta-cli`. When adding translatable strings:
- Add the English key first
- Use ICU MessageFormat or simple key-value pairs
- Keep keys descriptive (e.g., `upload_success`, not `msg_01`)

## License

By contributing, you agree that your contributions will be licensed under the CC-BY-NC-4.0 license.
