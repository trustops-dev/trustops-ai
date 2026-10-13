# Local development

## Python workspace

Install uv 0.13.0 using the [official installation instructions](https://docs.astral.sh/uv/getting-started/installation/), then run these commands from the repository root:

```sh
uv python install
uv sync --locked --all-packages --all-groups
```

`.python-version` selects Python 3.12. uv can install that interpreter without replacing your system Python. `.venv` contains the isolated workspace environment. The same commands work in PowerShell and POSIX shells.

The workspace includes the three Python applications and six reusable packages. Each member uses its existing `src/trustops_*` namespace and declares its own dependencies in its `pyproject.toml`. The dashboard will have a separate JavaScript workspace.

Add dependencies only to the member that uses them, for example:

```sh
uv add --package trustops-api fastapi
uv add --package trustops-api trustops-contracts
```

Run these examples only when implementing a feature that needs those dependencies. Internal package sources already resolve from the workspace. Commit the changed manifests and generated root `uv.lock` together. Use `uv lock` after manual manifest changes; do not hand-edit the lockfile.

Ruff, mypy, pytest, and import-linter are development dependencies. Run them through `uv run` as described in [testing.md](testing.md). Application behavior and external-service configuration have not been implemented yet.
