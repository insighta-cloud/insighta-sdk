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

## Linting

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and import sorting.

```bash
ruff check .          # check for issues
ruff check --fix .    # auto-fix
```

A pre-commit hook is provided. Install it once:

```bash
pre-commit install
```

## Live Tests

Integration tests run against the dev API. They require a valid API key:

```bash
export INSIGHTA_DEV_API_KEY="your-dev-key"
pytest tests/test_live.py --live -v
```

On Windows (PowerShell):

```powershell
$env:INSIGHTA_DEV_API_KEY = "your-dev-key"
pytest tests/test_live.py --live -v
```

Live tests are skipped by default when running `pytest` without `--live`.

## Code Style

- Follow PEP 8 (enforced by Ruff)
- All comments and docstrings in English
- Type hints required for public APIs
- Use `Decimal` for financial values, never `float`

### Docstrings

Use [Google-style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) docstrings with `Args`, `Returns`, `Raises` sections as needed:

```python
def get_news(self, period: int, source_type: str | None = None) -> dict:
    """Fetch recent news articles.

    Args:
        period: Number of days to look back.
        source_type: Optional filter by source type.

    Returns:
        Dict with "data" key containing list of news items.

    Raises:
        requests.HTTPError: If the API returns a non-2xx status.
    """
    ...
```

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new API method
fix: correct rate lookup for edge case
docs: update README
test: add missing test for merge_and_sort_groups
```

## Cross-Platform Compatibility

This project must work on both Windows and Linux/macOS:

- Use `os.path.join()` for file paths — never hardcode `/` or `\`
- In tests, compare paths with `os.path.join()` instead of string literals
- Avoid shell-specific commands in code; use Python stdlib (`os`, `shutil`, `pathlib`)
- Test locally on your OS, but don't assume forward slashes in assertions

## Good First Contributions

New to the project? Here are some ways to get started:

- **Add or improve examples** — Add a new script to `examples/` or fix an existing one that doesn't work as expected.
- **Spec conformance** — Compare `insighta_sdk/client.py` against the [OpenAPI spec](https://github.com/insighta-cloud/insighta/tree/main/insighta-app/openapi-docs) and report or fix any parameter mismatches, missing fields, or incorrect HTTP methods.
- **Internationalization (i18n)** — Add locale support for CLI-facing error messages or user-visible strings. See the i18n section below for conventions.
- **Documentation** — Improve docstrings, add type hints to untyped functions, or translate the README into another language.
- **Test coverage** — Write tests for edge cases or untested utility functions.

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
