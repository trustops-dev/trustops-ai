# Security

Do not commit credentials, raw sensitive datasets, traces with secrets, or generated model artifacts. Report vulnerabilities privately to the repository maintainers. Redact sensitive trace attributes before export and require authorization for approval and tool operations.

## Automated secret scanning

The `Security` workflow runs Gitleaks against all fetched Git history for pull requests and pushes to `main` and `dev`, and supports manual runs. Findings fail the `Secret scan` check; logs redact secret values. The scan needs no application dependencies or provider keys.

Gitleaks is downloaded from a pinned release and checked against its SHA-256 checksum before execution. To update it, change both `GITLEAKS_VERSION` and `GITLEAKS_SHA256` in `.github/workflows/security-tests.yml`, using the official release checksum for the Linux x64 archive. Dependabot updates action references, not this binary version.

If a real credential is detected, revoke or rotate it and contact the maintainers; removing it from the latest file does not remove it from Git history. Scanning helps detect known secret patterns and does not guarantee that every secret is found.
