# TrustOps v1.13 supplied archive review — 2026-11-18

Disposition: AMEND; G01 HOLD. Review input is the supplied archive, not an accepted runtime release. No provider calls or credential access occurred.

## Verified results

All 12 manifest file hashes and sizes match. Direct extraction runs require no filename alias. Schema regression: 101/101 cases, 2,788 baseline assertions. Mock diagnostic suite: 22/22. Bundled independent probes: 6/6 expected rejections. Bundled reproduction suite: 10/10 no reproduced original defect. Bundled remaining-controls suite: 7/7 reports no reproduced original defect. SDK local self-test passes. These are Linux offline results; Windows locking is simulated.

## Prior findings disposition

- RR-01 PARTIAL: file hashes, sizes and script defaults fixed. Delivered filename is v1.13 but manifest identifies v1.12.0-rev2 and TrustOps_v1.12_Complete_Package.zip. Correct the release/archive mapping explicitly and supply a pushed dedicated PR/head. No such commit is supplied by this archive. Historical test-count blocks should be labelled historical.
- RR-02 PARTIAL: omitted flags now block with zero calls. However count=2 and pause=True alone allow C01/G01 with an empty observation list, null pause evidence and UNKNOWN_UNCONFIRMED dashboard headroom. The CLI provides no observation-evidence input. Bundled ATTESTED data even uses observations only five minutes apart. Add an admission record interface and validate two observations at least 15 minutes apart, matching project/model, zero reported activity (not No data available), capture/evidence references, explicit pause window and confirmed headroom. Human observation truth still requires operator confirmation; schema validation cannot establish dashboard truth.
- RR-03 improved: shared session.lock path, existing two-run reservation cap and spacing lock tests pass. Full lifetime safety remains coupled to RR-06: the lock is released while a timed-out worker remains active.
- RR-04 targeted boundary fixed: with 16 prior attempts, C01 and G01 now complete within one admitted reservation. Local accounting is correctly labelled local. This does not confirm external headroom or establish shared persisted margin semantics across every runner/restart; review those with the accepted ledger interface.
- RR-05 FIXED for reproduced scope: absent ledger paths block independently of their filenames; bootstrap is explicit.
- RR-06 STILL OPEN: Event.wait bounds caller latency but does not cancel a Python thread. Our event-controlled mocked handler remained blocked after the caller returned at 20ms, while session.lock could already be reacquired. An unfinished ledger debit is retained, which is good, but it does not demonstrate transport termination. Use a terminable worker/cancellable transport and verify local worker/socket shutdown before releasing the session lock; retain unknown provider outcome and the charged attempt. Do not infer that stopping local work cancels a request already received remotely.

## Additional portability gap

probe_remaining_controls.py unconditionally imports fcntl and cannot run unchanged on native Windows, despite documentation describing cross-platform reproduction commands. Make that probe portable or clearly label it Linux-only and supply the native Windows equivalent/results. The main runner's Windows simulation is not a native Windows test.

## Evidence and next return

[Structured verification record](../validation/mohab-v1.13-review-2026-11-18.json) pins the archive, component files, prior test logs and additional mocked findings. [External reproduction bundle](https://chatgpt.com/library?file_id=libfile_77ccd6583e1c8191ae7f7ba3ddffe04a&account_id=personal) contains the logs and independent script. This owner-packet update records the completed review; those external suites were not rerun during documentation integration.

The archive was received through Nour; Mohab’s acceptance of these new findings and a response date/message ID are not supplied. Recording this review does not record an email as sent. The original E01–E27 mapping is historical; this focused regression review does not replace it with a new row-by-row mapping.


additional_probes.py uses only synthetic data, temporary SQLite files and httpx.MockTransport. Run from the parent directory containing review-v113; no provider access is needed. additional-results.json records count-only admission and worker-lifetime findings. Other logs contain the supplied suite reruns.

Return an exact pushed implementation commit, corrected release manifest, admission-record negative cases, worker termination/lock-lifetime tests and native Windows evidence. Keep REST transport compatibility distinct from google-genai SDK compatibility. The schema may proceed to scoped specialist review as an offline-tested draft, but joint/runtime acceptance and G01 execution remain open. Historical November 9 outcomes and USD 0 paid authorization remain unchanged.
