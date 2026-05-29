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

Integration tests run against the API and require a valid API key:

```bash
export INSIGHTA_API_KEY="your-api-key"
pytest tests/test_live.py --live -v
```

On Windows (PowerShell):

```powershell
$env:INSIGHTA_API_KEY = "your-api-key"
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

### Issues

- **Always open an issue first** before starting work on a feature or bug fix.
- Use labels to categorize: `bug`, `feat`, `docs`, `breaking`.
- Assign yourself to the issue when you start working on it.

### Branch & PR

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Write tests for new functionality
4. Ensure all tests pass (`pytest`)
5. Submit a pull request against `main`

### PR Conventions

- PR title must follow [Conventional Commits](https://www.conventionalcommits.org/) (e.g., `feat: add delete_order method`)
- Reference the issue in the PR body: `Closes #123`
- For breaking changes, include `BREAKING CHANGE:` in the PR body with a migration note
- Add a label to hint the version bump: `patch`, `minor`, or `major`

### Version Bumps

- **Contributors do NOT bump the version.** Maintainers decide the version at release time based on PR labels and changelog.
- CI runs lint + tests on every PR. Merging requires all checks to pass.

## Releasing to PyPI

### Versioning (SemVer)

This project follows [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`

| Bump | When | Example |
|------|------|---------|
| **PATCH** (0.1.5 → 0.1.6) | Bug fixes, docstring updates, internal refactors with no API change | Fix rate lookup edge case |
| **MINOR** (0.1.6 → 0.2.0) | New features that are backward-compatible (new methods, new optional params) | Add `delete_order()` method |
| **MAJOR** (0.2.0 → 1.0.0) | Breaking changes (removed/renamed methods, changed return types, dropped Python version support) | Rename `send_order` → `create_order` |

> While pre-1.0 (`0.x.y`), minor bumps may include small breaking changes. After 1.0, strict SemVer applies.

### Release Steps

When publishing a new version:

1. Bump `version` in `pyproject.toml`
2. Commit the version bump (`chore: bump version to X.Y.Z`)
3. Tag the commit (`git tag vX.Y.Z`)
4. Push the commit **and** tag (`git push --tags`)
5. Build and upload:
   ```bash
   python -m build
   python -m twine upload dist/insighta_sdk-X.Y.Z*
   ```

**The version bump commit must be pushed before uploading to PyPI.** The Git tag and PyPI version must always match.

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
