# Contributing to TrustOps AI

This repository contains the planned directories, Python and frontend workspace setup, and repository checks. Add application behavior, tests, and configuration with the work that needs them. Follow the [local development guide](docs/operations/local-development.md), and read [ARCHITECTURE.md](ARCHITECTURE.md) before changing module boundaries.

## Branches and pull requests

The team workflow is **task branch → PR → `dev` → PR → `main`**.

- `dev` is the shared integration branch. Use lowercase `dev` consistently.
- `main` contains reviewed, tested work promoted from `dev`.
- Both branches are permanent and protected. Push your changes to a task branch;
  do not push directly to `dev` or `main`.

### Teammate: clone and start a task

Clone once:

```sh
git clone https://github.com/trustops-dev/trustops-ai.git
cd trustops-ai
git switch dev
```

For every new task, start with a clean working tree and the latest `dev`:

```sh
git switch dev
git pull --ff-only origin dev
git switch -c feature/api-health
```

Replace `feature/api-health` with a unique task name. Other examples are
`fix/api-validation` or `docs/setup-guide`. Branches belong to tasks, not people.
Follow the [local setup guide](docs/operations/local-development.md), implement
the task and its tests, and run the relevant [checks](docs/operations/testing.md).

Review `git status` and stage only the intended files. Replace the example paths
and commit message below with the files and purpose of your task:

```sh
git status
git add path/to/changed-file path/to/test-file
git commit -m "Implement API health endpoint and tests"
git push -u origin feature/api-health
```

On GitHub, open a PR with **base: `dev`**, **compare: your task branch**. Check
the base explicitly: GitHub may suggest the default branch, `main`.

### Review and merge a task

1. Describe the change, link its task/issue, and list the checks actually run.
   Remove a directory's `.gitkeep` when it gains another tracked file.
2. Request review from Nour or Malak. A PR author cannot approve their own PR.
3. Address feedback and wait for all required checks. Push fixes to the same task
   branch; stale approvals may need to be renewed after changes.
4. If the task branch is behind `dev`, merge the latest `origin/dev` into the task
   branch, resolve conflicts, rerun relevant checks, and push. Never force-push
   a protected branch.
5. Merge the approved PR into `dev`, then delete only its completed task branch.

### Maintainer: promote tested work to main

After the selected tasks have been integrated and tested together, Nour or Malak
coordinates a promotion PR with **base: `main`**, **compare: `dev`**. Summarize the
included tasks, validation, and any migrations or configuration changes. Obtain
Code Owner approval and passing checks just as for a task PR.

Use **Create a merge commit** for PRs between `dev` and `main` to preserve their
shared history. Keep both permanent branches afterward. A promotion includes all
changes in `dev` that are not yet in `main`; review that complete diff before merging.

### Dependabot and changes already merged into main

Dependabot continues to target the default branch, `main`, so its version and
security update behavior stays aligned. Review those PRs and require passing
checks. After a dependency update or an exceptional fix merges into `main`, open
a sync PR with **base: `dev`**, **compare: `main`**, obtain approval, and merge with
a merge commit. Keep both branches. Normal team feature work still targets `dev`.

Never disable protections to synchronize branches. If the sync has conflicts,
resolve them on a temporary branch created from `dev` and submit that branch as
a PR to `dev`.

## What to include in a change

- Keep shared contracts in `packages/contracts`. Packages must not import from apps, and FastAPI routers should only handle the HTTP boundary.
- Add or update relevant tests and tooling with the implementation they verify. Do not add empty source files or workflows that depend on commands that do not exist yet.
- Never commit credentials, real secrets, sensitive datasets, or generated artifacts. Use safe example values in `.env.example` when configuration is introduced.
- Report exact validation commands and results in the pull request. If a check does not yet exist or cannot run, say so.
- When implementing a feature covered by an inactive workflow template, follow the [activation guide](docs/operations/workflow-activation.md) and activate the relevant check in the same PR as its code and tests. Record successful execution and failure behavior before requesting a new required check.
