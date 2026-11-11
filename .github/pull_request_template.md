## Summary

- What behavior changed?
- Why is the change needed?

## Verification

- [ ] `python -m pytest -q`
- [ ] `ruff check .`
- [ ] `ruff format --check .`
- [ ] `mypy mcp_verdict`
- [ ] `python -m build`
- [ ] `python -m twine check dist/*`

## Compatibility and security

- Compatibility concerns:
- Security impact:
- Secrets and credentials excluded from tests/reports: [ ]

## Documentation

- [ ] User-facing behavior is documented.
- [ ] No unrelated files or generated artifacts are included.
