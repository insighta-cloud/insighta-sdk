# Changelog

## [0.1.5] - 2026-05-28

### Changed
- Enforce Decimal types for financial calculations
- Add Google-style docstrings and type hints to all public APIs

## [0.1.4] - 2026-05-28

### Added
- AI agent use case documentation and examples
- Usage examples directory
- Linting and live test instructions in CONTRIBUTING

### Changed
- Added ruff config and pre-commit hook
- Fixed lint issues

## [0.1.3] - 2026-05-08

### Added
- Cross-platform compatibility guidelines
- Dev dependencies and author email

### Fixed
- `Dirs` path tests now OS-independent

## [0.1.2] - 2026-05-08

### Added
- Live API test infrastructure

## [0.1.1] - 2026-05-08

### Added
- 7 missing OpenAPI endpoint methods
- Authentication section in README

## [0.1.0] - 2026-03-29

### Added
- Initial release
- API client (`InsightaClient`) with portfolio CRUD and order submission
- Data models: `Trade`, `Holding`, `Deposit`, `OrderGroup`, `CashDeposit`, `RateEntry`
- Utilities: rate lookup, order grouping, deposit merging
- `Dirs` class for workspace path resolution
