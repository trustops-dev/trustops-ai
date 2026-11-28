# Prompt pack v1 — proposed review assets

Read ../prompt-pack.md for contract mapping, all templates, complete examples, trust boundaries and open dependencies. The templates are proposed for the app locations recorded in prompt-manifest.json; they are documentation assets, not installed app code or SDK payloads.

Run `python3 validate_prompt_pack.py` from this directory with the existing Pydantic 2 dependency. It performs offline checks and writes validation-report.json. No network, model, tool execution, DB, approval or purchase is performed. JSON Schemas are ADR/provider-boundary candidates and strict offline tool argument transcriptions, not frozen shared API contracts.

Each example separates input.json and rendered-prompt.txt from expected.json and review.json. Only verified input data and selected templates may enter a future live call. Expected outputs, hypothetical gates and review notes never authenticate evidence or become ground truth in prompts. The examples are alternatives unless the main illustrative path is explicitly identified in the document.

All values/results are synthetic. The 5000.00 threshold and USD currency in the paper-style example do not configure policy. No live/canonical runtime validation or stakeholder approval is claimed. Formal missing contracts and owner gates remain documented in ../prompt-pack.md.

Review revision 1.1 strengthens identity/type binding and duplicate-key rejection. Template versions remain unchanged; validation-report.json records the current offline check scope.
