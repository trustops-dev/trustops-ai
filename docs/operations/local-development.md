# Local development

## Python workspace

Install uv 0.13.0 using the [official installation instructions](https://docs.astral.sh/uv/getting-started/installation/), then run these commands from the repository root:

```sh
uv python install
uv sync --locked --all-packages --all-groups
```

`.python-version` selects Python 3.12. uv can install that interpreter without replacing your system Python. `.venv` contains the isolated workspace environment. The same commands work in PowerShell and POSIX shells.

The workspace includes the three Python applications and six reusable packages. Each member uses its existing `src/trustops_*` namespace and declares its own dependencies in its `pyproject.toml`. The dashboard uses the separate JavaScript workspace below.

Add dependencies only to the member that uses them, for example:

```sh
uv add --package trustops-api fastapi
uv add --package trustops-api trustops-contracts
```

Run these examples only when implementing a feature that needs those dependencies. Internal package sources already resolve from the workspace. Commit the changed manifests and generated root `uv.lock` together. Use `uv lock` after manual manifest changes; do not hand-edit the lockfile.

Ruff, mypy, pytest, and import-linter are development dependencies. Run them through `uv run` as described in [testing.md](testing.md). Application behavior and external-service configuration have not been implemented yet.

## Frontend workspace

Install Node.js 24.21.0 (the LTS version pinned in `.nvmrc`) and pnpm 12.11.2. A version manager that supports `.nvmrc` can select Node automatically; otherwise install that version from the [official Node.js downloads](https://nodejs.org/en/download). To install the pinned package manager with npm:

```sh
npm install --global pnpm@12.11.2
```

Then run from the repository root:

```sh
pnpm install --frozen-lockfile
pnpm dev
```

Open `http://localhost:3000`. The dashboard currently contains only an entry page with an empty application state. It does not connect to an API or display real traces yet.

The root `package.json` owns shared lint, TypeScript, and test tools. React is also a root development dependency so the central dashboard test suite can resolve it. `apps/dashboard/package.json` owns the dashboard's runtime dependencies. Both use the same React version. The root `pnpm-lock.yaml` covers the entire JavaScript workspace.

ESLint 9 and TypeScript 5.9 are pinned for compatibility with Next.js's current lint plugins. ESLint 9 is deprecated upstream; move to ESLint 10 when the React, import, and accessibility plugins declare support. Do not bypass peer-dependency validation to upgrade them independently.

Add a dashboard runtime dependency with `pnpm --filter @trustops/dashboard add <package>`. Add shared test tooling with `pnpm add --workspace-root --save-dev <package>`. Commit the manifests and generated lockfile together. Use `pnpm install` after intentional manifest changes; CI uses `--frozen-lockfile` and rejects a stale or missing lockfile. Review dependency install scripts before allowing them in `pnpm-workspace.yaml`.

Next.js generates `next-env.d.ts` and `.next` locally. These are ignored. `pnpm typecheck` generates route types before checking source and test types, so it works on a fresh checkout. Use `pnpm build` followed by `pnpm start` to run the production build locally.
