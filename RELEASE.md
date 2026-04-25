# Release Process

## Versioning

- Tags follow `vX.Y.Z` (example: `v0.2.1`).
- `pyproject.toml` version must match release tag without `v` prefix.

## Release Checklist

1. Run tests locally.
2. Update `CHANGELOG.md`.
3. Bump version in `pyproject.toml`.
4. Commit and push.
5. Create and push tag: `git tag vX.Y.Z && git push origin vX.Y.Z`.

## Automated Release Outputs

Tag push triggers `.github/workflows/release.yml` and produces:

- Python sdist + wheel artifacts attached to GitHub release.
- Container image pushed to `ghcr.io/<owner>/<repo>`.
