# Week 2 manual application traces, revision 1

The two files use the v1.16 package from Mohab’s commit
`c645cfc72ef9d718cfe326990059a5ca0a37b3a1`. Its walkthrough payloads carry
`schema_version = 1.10.0-draft`. The application base is PR #29 at
`56adf262de7e2506fda035d6119ef98bcb610e3c`. Both fixtures use
`MANUAL_FIXTURE` and synthetic requests. Event IDs are scoped to each trace.
Timestamps, budget examples and retrieval scores are illustrative. Model steps
and tool effects are authored examples. No provider or governance engine ran.

The historical inputs come from PR #27 at
`14c426261cba852c49fd441a1b0c0efc6f942bca`, under
`docs/architecture/reference-applications/fixtures/`. These counterparts reuse
the canonical field layout of Mohab’s walkthroughs and the application cases
and evidence from the historical files.

| Trace | Application evidence |
|---|---|
| `01-procurement-success.json` | Request for 20 laptops, USD 16,000, supplier SUP-088. The pending approval submission at e25 precedes the separate approval at e27. Proposal e30 passes argument validation e31 and the stub policy check e32. The claim is consumed at e33. The mock dispatch e34 and CREATED / COMMITTED result e35 support the final claim for PO-2044 at e38. |
| `03-rag-grounded.json` | The original laptop-request question and single supplied IT passage. Retrieval e1 binds the snapshot, source version, chunk and content hash. The rendered prompt at e2 includes that exact selected passage. The final answer at e3 binds citation [1] to the source quote at [0, 61) and the answer claim at [0, 51), in Unicode code points. This is the paper-source case. The emergency-leave FTS5 test has separate corpus and index provenance. |

## Reproduce from the application checkout

Use Python 3.12. Fetch the exact schema revision if the pinned Git object is
absent, then run the verifier from the repository root. The mutable schema
branch may have advanced or been rewritten; the verifier remains pinned.

```sh
git fetch origin c645cfc72ef9d718cfe326990059a5ca0a37b3a1
python tests/fixtures/traces/week2-v1/verify.py
```

The script checks the SHA-256 of the committed validator before loading it.
It reads each fixture independently, prints its byte hash and findings, and
returns a nonzero exit code on any failed assertion. The expected counts on
these bytes are 1,644 for Procurement and 168 for RAG, both with zero findings.
As negative controls during preparation, replacing the PO dispatch's
authorization check reference with an absent ID produced
`ERR_AUTH_CHECK_UNRESOLVED` and `ERR_PO_BINDING_FAILED`. Changing only the
RAG citation's snapshot produced `ERR_CITATION_SNAPSHOT_MISMATCH`.
