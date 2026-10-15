# Inactive workflow templates

These files are preparation only. GitHub does not run them from this directory,
and their `.yml.template` extension is not an active workflow extension.

Follow [the activation guide](../../docs/operations/workflow-activation.md) in the
same PR that introduces the implementation, dependencies, and real tests.
Move the selected template into `.github/workflows/`, remove `.template` from its
filename, and adapt the commands and paths to the reviewed implementation.

Do not activate all templates at once or require their check names in branch
protection before they execute successfully. Missing implementation must fail
an activated check; do not add successful placeholder steps or file-existence
conditions that skip the job.

The action SHAs and tool versions match the current active workflows. Dependabot
may not update actions inside these inactive templates: recheck those pins against
the maintained workflows when activating one.
