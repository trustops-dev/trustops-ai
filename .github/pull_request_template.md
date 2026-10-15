## Summary

Describe the change and why it is needed.

## Branch target

Confirm the intended base: normal task PRs target `dev`; promotion PRs use `dev` → `main`; sync PRs use `main` → `dev`. Dependabot updates target `main`. Keep both permanent branches after a promotion or sync.

## Validation

List the commands you ran and their results. If none apply, explain why.

## Review notes

Call out configuration changes, migrations, new dependencies, or known limitations. Write "None" if there are none.

## Workflow activation

If this PR implements a stage from the [activation guide](../docs/operations/workflow-activation.md), list the workflow(s) activated, their prerequisites, and evidence that relevant failures are detected. Otherwise write "Not applicable". Add implementation and tests in this PR; required-check settings are updated only after successful activation and merge.
