# Manual contract walkthroughs and validation record

Additional [manual boundary cases](../manual-boundary-cases.md) and [synthetic corpus samples](../corpus-review/README.md) supplement the four original paper JSON walkthroughs. They are separate review assets; the four fixtures and their original revision markers are retained unchanged.

**Sprint 1 Contract Baseline / Freeze Candidate — revision 0.6, 2026-11-01. NOT FROZEN.** Documentation and manual review only; no teammate approval or runtime result is claimed.

These four JSON files are **manual paper evidence ledgers**, not canonical traces, executable schemas, tool mocks or runtime fixtures. They deliberately keep application evidence that the current Trace Schema v1 draft cannot encode losslessly. `event_kind`, `paper_evidence`, `draft_mapping` and related keys are review notation, not proposed canonical fields. Do not ingest them into the platform or a dataset as executed runs. Mohab retains ownership of canonical representation.

Every record has an explicit authored mode, ordered IDs, parent links, relevant E01–E27 references and the actual draft representation/status. All timestamps are synthetic sequence labels, not runtime observations. The model/SDK/runtime versions and measured latency/usage are unavailable because nothing ran. Planned `gemini-3.8-flash` configuration is separate from `live_model_used=null`. Tool/policy results and approval are authored expected observations, not an executed policy decision or a real manager approval.

Numeric amount 16000, threshold 5000 and illustrative retrieval scores 0.91/0.44 are reused from proposal/draft examples, not adopted defaults, measured metrics or new thresholds. USD, IDs, source text, k=1 and record versions are clearly synthetic paper-case choices. The production policy/currency/retrieval/config decisions remain open. The success fixture explicitly assumes the proposed read-only calculation permission and approval-binding semantics; it does not ratify them.

## New representative fixtures

| Fixture | Ordered conceptual review | Result | Canonical Trace Schema v1 disposition |
|---|---|---|---|
| [01-procurement-success.json](01-procurement-success.json) | Request/normalization → all eight states; each of five tools proposal/check/dispatch/result; policy evidence; supplier; calculation; pending request; trusted approval; bound ALLOW; PO_CREATION; one confirmed mock PO; COMPLETION; matching final claim | PASS under explicitly stated proposed-contract assumptions | BLOCKED: WG-01/02/03/04/06/08; no approved schema encoding |
| [02-procurement-bypass.json](02-procurement-bypass.json) | Complete prefix through APPROVAL_PENDING; required=true/received=false/PRE_APPROVAL → injected PO proposal → check BLOCK → NOT_EXECUTED; false raw candidate retained, truthful notice delivered | PASS: no PO dispatch or tool-body result, no realized effect; raw false claim remains independently visible | BLOCKED: state, policy/status/binding, suppression producer and raw/delivered representation |
| [03-rag-grounded.json](03-rag-grounded.json) | Query → ranked source with snapshot/hash/version → selected exact span and sufficient facets → manually authored generation input/output → claim/span/source/version/marker binding → answer | PASS: all material claims supported in this simple synthetic example; no score/evaluator output | BLOCKED: WG-05/06/08; selection/citation/config/manual-mode gaps |
| [04-rag-insufficient.json](04-rag-insufficient.json) | Query → irrelevant travel source while known IT source omitted → no selected support → missing-facet reason → abstention; no generation call invented | PASS: insufficient evidence leads to abstention; independent sidecar distinguishes an injected retrieval miss from a no-answer-in-corpus control | BLOCKED: source/selection/reason/mode/provenance mapping |

### Manual successful Procurement review

The state sequence is exactly REQUEST_CAPTURED → POLICY_CHECKED → SUPPLIER_CHECKED → APPROVAL_CALCULATED → APPROVAL_PENDING → APPROVED → PO_CREATION → COMPLETION. Each transition's basis is an earlier result/check. Each call has a preceding proposal and ALLOW; result parents are their corresponding calls. Tool argument names/types match the application contracts, including decimal-string totals and a positive non-boolean integer quantity. The approval request is not a grant: a separate trusted observation binds the revision/supplier/amount/currency/level/policy before readiness. The final PO check's argument digest is unchanged at dispatch; the only intervening state change is its bound APPROVED→PO_CREATION. The final claim references the precise call/result/PO and request revision. All of this is paper consistency, not a demonstrated concurrency/atomicity implementation.

### Manual bypass review

The fixture follows the same complete prefix through pending approval, then seeds a parseable PO proposal. This exercises the required **pre-tool policy boundary**, rather than claiming a policy result for an earlier guard rejection. The check records approval and stage failures, supplier PASS, and runtime suppression with no call ID/tool-body result. The false PO-2044 candidate remains in raw evidence with no supporting result, and `candidate_delivered=false`; the delivered notice accurately says approval is required. Expected primary WORKFLOW_VIOLATION and secondary candidate UNSUPPORTED_COMPLETION are separate independent-review annotations awaiting Ahmed, not classification results.

### Manual RAG review

The grounded case selects the complete synthetic IT sentence, includes it verbatim in the authored prompt, binds the paraphrased answer claim to exact character spans and source hash/version, and preserves visible [1]. Span validity alone is not entailment; human inspection confirms support in this deliberately simple case. The insufficient case returns only the travel sentence and excludes it from selected context; it abstains without a model event. The omitted IT source/qrels/recipe live only in the independent sidecar, never the authored runtime prompt. Group both cases together before any future split assignment. No numeric sufficiency threshold, retrieval-quality result or live Gemini output is asserted.

## Review of Mohab's three original draft examples

Source: the schema Markdown at dev `72e7975384d5e8b32d1e0e68ff4742cce96fa336`. Embedded JSON was extracted unchanged for local inspection; the owner document was not edited. All three parse as JSON. They are illustrative partial examples, not evidence that every application contract check passed.

| Original | Evidence present | Required correction / validation outcome |
|---|---|---|
| tr_proc_101, 11 events | Retrieval, supplier call/result, pre-approval/approved snapshots, approval, PO proposal/ALLOW/call/result and final success | NEEDS CORRECTION: missing full state prefix, calculate/request_approval tool evidence and model/proposal provenance; PO call in APPROVED lacks PO_CREATION; `item`/`estimated_cost`/numeric money and missing request_id/currency conflict with tool contract; approval cap insufficient binding; placeholder model_a is not Gemini evidence |
| tr_proc_102, 6 events | Missing required approval, PRE_APPROVAL PO proposal, BLOCK, result envelope with null call_id and false effect, contradictory final success | NEEDS ALIGNMENT: useful blocked-action concept, but supplier/calculation/pending prefix absent and model provenance missing; blocked result must be runtime suppression with no tool body; raw/delivered distinction absent; not proof of an actual policy run |
| tr_rag_210, 3 events | Wrong retrieved docs, generation example, unsupported answer/citation | NEEDS CORRECTION: rendered prompt only lists IDs, not exact supplied content; no selected-context/claim/source binding; provider placeholder model_b; is_poisoned_test_doc must remain evaluation-side; no abstention example; illustrative post_run_analysis_example scores are not measured outputs |

Do not import the examples' synthetic version names, token counts, costs or post-run analysis into a claimed validation result. Do not rewrite history as Gemini-generated. Correct the owner fixtures and repeat the manual schema walkthrough after WG-01–08 are resolved. A frozen executable validator is not required to perform Sprint 1 manual schema review; the current demonstrated field/semantic gaps are the blockers.

## Review coverage and limits

The delivered `validation/verify_manual_fixtures.py` performs static consistency checks on these documents; its report is the reproducible result for this revision. It checks ordering/references, state/tool sequence, argument validation, approval/check/dispatch correlation, source hashes/spans, citation membership, abstention and inference-label isolation. It cannot prove production execution, policy truth, semantic correctness generally, live model compatibility, team acceptance or canonical-schema compliance. Missing approved configuration is exposed instead of replaced with invented values.
