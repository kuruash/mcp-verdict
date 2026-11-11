# Changelog

All notable changes are documented here. The project is pre-1.0 and follows
Semantic Versioning conventions: minor releases may add compatible behavior,
patch releases fix compatible defects, and breaking changes are called out
explicitly before 1.0.

## [0.1.0] - Planned

Initial planned public release, including:

- Real MCP STDIO and Streamable HTTP connections.
- YAML-driven tool and HTTP status checks.
- PASS, FAIL, and ERROR classification with exit codes 0, 1, and 2.
- Human-readable and schema-versioned JSON reports.
- Atomic report files and bounded diagnostic redaction.
- Local STDIO and HTTP integration examples.
- GitHub Actions CI and release-artifact validation.

This release does not provide comprehensive OAuth/JWT auditing, sandboxing,
remote target discovery, or a guarantee that arbitrary third-party output is
safe to disclose.
