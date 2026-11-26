# Agent Instructions

## Development

When making breaking changes, ask whether backward compatibility should be preserved.

## Tests

Always add tests for new functionality. When changing existing functionality, run the tests and add tests for any changed behavior that is not already covered. Do not assert on logs.

Run the tests using `make test`.

## CHANGELOG

Always update `CHANGELOG.md` when making changes to the project. Keep both `AGENTS.md` and `CHANGELOG.md` in English.

- Add all new entries only to the `## Unreleased` section unless the user explicitly requests a specific release.
- If the `## Unreleased` section does not exist, create it before the most recent version section.
- Use the appropriate category: `### Added`, `### Changed`, or `### Fixed`. Keep them in that order.
- Describe changes briefly and in language users can understand.
- Do not add entries for purely technical actions that do not change the project, such as running tests or formatting without changes.
- Before releasing a version, use `make version X.Y.Z` to rename the `## Unreleased` section to the version heading and update `manifest.json`.
- Do not modify changelog entries for older released versions during refactoring. Changes are allowed only in the `## Unreleased` section.
