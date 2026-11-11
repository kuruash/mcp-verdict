# Release checklist

This checklist is for a maintainer; no step publishes automatically until a
version tag is deliberately pushed.

1. Review the changelog and confirm the `pyproject.toml` version is `0.1.0`.
2. Run `python -m pytest -q`, `ruff check .`, `ruff format --check .`, and
   `mypy mcp_verdict` locally.
3. Run `python -m build` and `python -m twine check dist/*`.
4. Install both artifacts into clean virtual environments and run
   `mcp-verdict --help`, a STDIO example, an HTTP example, JSON output, and an
   atomic report-file check.
5. Inspect wheel and sdist contents for credentials, generated reports, and
   unintended files.
6. Confirm the repository has no secrets, `.env` files, or fixture processes.
7. Review the pending diff and obtain explicit maintainer approval.
8. Create the annotated tag `v0.1.0` locally and push it only after approval.
9. Before tagging, configure a PyPI Trusted Publisher for this repository and
   workflow (`.github/workflows/release.yml`) in PyPI's project settings. Use
   the repository owner/name, workflow filename, and the `pypi` environment;
   do not add an API token secret.
10. After the tag workflow succeeds, verify the package metadata and installation
    from PyPI manually. Rollback means publishing a subsequent corrected
    version; PyPI releases are not silently replaced.

The release workflow runs only for `v*` tags. Pull requests and ordinary pushes
run CI validation but never publish.
