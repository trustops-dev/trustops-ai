# Import the final integration

The ZIP contains one integrated state, commit `31354fb1bcffa8a282bec9f1d497e5f0586f7f47`, based on dev `59767ba53a168c4bf39160d8a4620504852063b4`.

- `repository/`: complete final tracked source, including all prerequisite documents.
- `integration.bundle`: Git commit transport for an existing clone with the base commit.
- `integration.patch`: alternative consolidated diff for the exact inspected dev baseline.

Use the bundle OR the patch, not both. No separate documentation patch is needed. Never apply the superseded v5 review patch afterward.

## Recommended import using the bundle

Start in a clean clone of https://github.com/trustops-dev/trustops-ai. Replace `/absolute/path/to/package` below with your extracted package directory.

```bash
git status --short
git fetch origin dev
git bundle verify /absolute/path/to/package/integration.bundle
git fetch /absolute/path/to/package/integration.bundle \
  fix/s1-03-final-integration-ci:fix/s1-03-final-integration-ci
git switch fix/s1-03-final-integration-ci
git log -1 --oneline
```

Do not overwrite an existing local branch with the same name. If dev has advanced, review/rebase onto current dev and rerun checks. Do not replace newer team configuration with a snapshot.

## Alternative import using the patch

```bash
git status --short
git fetch origin dev
git switch -c fix/s1-03-final-integration-ci origin/dev
git apply --check /absolute/path/to/package/integration.patch
git apply --whitespace=nowarn /absolute/path/to/package/integration.patch
```

`--whitespace=nowarn` preserves the original Markdown hard-break spaces; it does not bypass patch applicability or CI checks. The patch is verified against the exact base commit above. Stop and reconcile if it does not apply to a newer dev; do not force it.

## Validate using repository pins

Use uv 0.13.0, Python 3.12, Node 24.21.0 and pnpm 11.28.2. Confirm versions before execution.

```bash
uv --version
node --version
pnpm --version
uv lock --check
uv sync --locked --all-packages --all-groups --no-editable
uv run --no-sync ruff check --output-format=github .
uv run --no-sync ruff format --check .
uv run --no-sync mypy
uv run --no-sync lint-imports --no-cache
uv run --no-sync pytest tests/unit tests/contract
pnpm install --frozen-lockfile
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm audit --audit-level high
```

Export to a temporary path outside the repository, then run the Python audit:

```bash
uv export --locked --all-packages --all-groups --all-extras \
  --no-emit-workspace --format requirements-txt \
  --output-file /absolute/path/to/trustops-requirements.txt --quiet
uv run --no-sync pip-audit --requirement /absolute/path/to/trustops-requirements.txt \
  --require-hashes --disable-pip --strict --progress-spinner off
```

Install and verify Gitleaks 8.30.1 as specified by `.github/workflows/security-tests.yml`, fetch full history if the clone is shallow, then run:

```bash
gitleaks git . --log-opts="--all" --redact --no-banner
```

The portable `verification/validate_contract_examples.py` harness reads the packaged repository and runs the additional 32 validator cases and six published JSON examples. Run it in a separate Python 3.12 environment with Pydantic 2.12.3 installed. It is a temporary audit harness, not additional repository implementation; do not add it to application source.

## Commit and publish

The bundle already contains the commit. If you used the patch, review and stage only the 12 paths listed in INTEGRATION_REPORT.md, then commit with:

```bash
git commit -m "fix(reliability): integrate Week 1 deliverables and resolve CI blockers"
```

Once validation passes and your GitHub CLI is authenticated:

```bash
git push -u origin fix/s1-03-final-integration-ci
gh pr create --base dev --head fix/s1-03-final-integration-ci \
  --title "fix(reliability): integrate Week 1 deliverables and resolve CI blockers" \
  --body-file /absolute/path/to/package/PR_DESCRIPTION.md
```

Alternatively, open a PR through GitHub after pushing and paste PR_DESCRIPTION.md. Wait for all six required checks and obtain the required reviews before merging. No hosted check or teammate approval is included in this package's local validation result.
