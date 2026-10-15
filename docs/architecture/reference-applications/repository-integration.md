# Week 1 repository integration record

Date: 2026-10-15. Source: supplied `TrustOps_AI_Week1_Contracts` Markdown folder,
S1-01 revision 0.5. Status: imported on a task branch for review; PR merge and
contract freeze are separate, pending milestones.

## Repository evidence

- Repository: https://github.com/trustops-dev/trustops-ai
- Base branch: `dev`, fetched before creating `docs/week1-reference-contracts`.
- Audited base commit: `3e513db26e5f4af80f4fb74a5067d17b20d0e10b`.
- The working tree was clean before the import.
- `ARCHITECTURE.md` describes module ownership and dependency boundaries.
  `CONTRIBUTING.md` requires task branches and reviewed PRs into `dev`.
- `docs/architecture/` and `docs/adr/` contained only `.gitkeep` files.
  No equivalent application contracts, ADR index or numbered ADRs were present.
- `packages/contracts` contains its packaging configuration and an importable
  package shell; no canonical Trace Schema v1 was present in the audited base.
  Application evidence requirements remain proposals awaiting that schema.

## File mapping and integration edits

| Supplied content | Repository destination / treatment |
|---|---|
| Package `README.md` | [Reference application index](README.md); links made relative to its new location, import status updated |
| Ten `docs/architecture/reference-applications/*.md` files | Same paths; business contracts retained |
| `docs/adr/reference-application-orchestration-and-llm.md` | Same path; inventory note updated, no ADR number invented |
| Repository `README.md` and `ARCHITECTURE.md` | Added navigation to the Week 1 draft |
| Empty documentation placeholders | Removed `.gitkeep` files as required by contribution guidance |

The historical audit is explicitly labelled. OD-01 and the repository acceptance
row now distinguish completed comparison/import from pending PR review and merge.
The supplied source folder has not been modified. Other decisions, ownership,
proposed schedules and pending sign-offs retain their supplied status.

## Evidence limits and remaining work

The handoff contains 12 Markdown files. The original proposal, sprint plan,
architecture DOCX, diagrams, roadmap and source-hash manifest mentioned in the
historical audit were not supplied in this folder. Their content and historical
hash-verification claims were not independently rechecked during this import.

Provider/model selections and external documentation claims are imported draft
content, not fresh capability verification. Confirm the exact available model,
API/SDK configuration and live access when closing OD-LLM-01/02. No live model
request, schema validation, runtime scenario or measured result is claimed here.

1. Obtain Code Owner review and merge the import PR into `dev`; record its PR
   number and merge commit here to close OD-01.
2. Resolve the [open decisions](open-decisions.md) and collect the named
   [handoff sign-offs](handoffs.md) before claiming contract freeze. GitHub PR
   approval alone does not satisfy all specialist sign-offs.
3. Add implementation and executable tests in later task PRs. Follow the
   [workflow activation guide](../../operations/workflow-activation.md) when a
   feature meets a template's activation requirements.

This documentation import does not activate workflows, change required checks,
add application code or dependencies, or replace existing smoke tests.
