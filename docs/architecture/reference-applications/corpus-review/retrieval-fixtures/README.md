# Offline retrieval fixtures — v0.1

**Status:** Authored, reproducible fixtures. No embeddings, vector index, provider call, measured retrieval score or application acceptance is claimed.

Run from the repository root:

```bash
python docs/architecture/reference-applications/corpus-review/retrieval-fixtures/build.py --check
python -m pytest -q docs/architecture/reference-applications/corpus-review/retrieval-fixtures/test_build.py
```

`authored-inputs.json` separately declares eight questions, pinned snapshots and simulated returned/selected IDs. `build.py` without `--check` regenerates the three derived JSON files. It verifies each UTF-8 NFC/LF source, exact SHA-256, source version, full protected span and snapshot membership before writing. `inference-inputs.json` holds the authored query/retrieval/selection inputs, full source text, canonical character spans, source/version/chunk identities and authored rank. Its score is null because no search was executed. `evaluation-sidecar.json` holds expected outcomes, relevance/conflict labels and the intentionally invalid partial-source example; **never provide it or `review-cases.json` to the retriever, generator, prompt or runtime trace**. An ID returned by the authored retrieval input remains legitimate even when that ID also appears in the evaluation sidecar.

The protected whole-document units preserve conditions and exceptions together. These are deterministic **source-slice fixtures**, not a proof that the proposed `cl100k_base` 512/640/64 chunker or Gemini native input limits accept the units. Before ingestion, run the selected token counter and native-limit admission check. If a unit exceeds the cap, revise and version the source; do not silently split away an exception. The opaque chunk ID in this offline fixture is a local deterministic locator, pending Mohab/Alaa's canonical ID and digest convention. Full-file SHA-256 equals chunk-text SHA-256 here solely because the exact source bytes are the complete chunk.

`proposed-policy-pairing.json` checks the two source versions/hashes in the separate OD-03 candidate. It is intentionally **not loaded by the eight RAG inference cases**, not part of s01/s02 and not an index. The stage-rule textual coverage, tool-version alias, chunk digest, release membership and index identity still require Mohamed/Mohab review. `index_version` remains null. No fixture is authorization evidence or a deployed policy.

After the pairing review, build an independently versioned corpus/index and update citation fixtures only against that accepted source snapshot. The current cases remain symbolic where they refer to T/C; no USD-specific answer is assigned to them.
