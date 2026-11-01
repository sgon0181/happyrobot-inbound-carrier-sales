# Carrier Sales submission candidate

## 1. Status

The isolated candidate is implemented and tested, but the required final live
owner call and App confirmation are still pending. Two real rehearsals proved
FMCSA, fresh email verification, matching, a genuine agent counteroffer and natural
booking consent without spending a load. 187 offline tests pass; 17 conversation
probes and five exact message checkpoints cover price interpretation and permission
boundaries. Deployed bookings are off. Main and the original workflow are unchanged,
and nothing was pushed. One ineligible-call hangup defect remains visible for
review. The owner will handle the video separately.

## 2. Clean-run gate

No final owner run has started. Do not combine rehearsals, older bookings and
separate speech checks to mark this gate passed.

| Exactly the nine architecture section 11 items, on one run | Result |
| --- | --- |
| Real voice call with an active MC | Not passed, final run pending |
| An emailed code | Not passed, final run pending |
| At least one counter | Not passed, final run pending |
| A TMS reference with PENDING | Not passed, final run pending |
| Neutral wording to the carrier | Not passed, final run pending |
| A spoken mocked transfer | Not passed, final run pending |
| The agent ending the session | Not passed, final run pending |
| A complete Twin record | Not passed, final run pending |
| A rep confirmation in Apps | Not passed, final run pending |

| Additional check | Evidence |
| --- | --- |
| Genuine agent counteroffer | Both rehearsals: 4200 ask,3600 response; final-run proof pending |
| Natural booking permission | Both rehearsals passed native consent; final-run proof pending |

## 3. Storage results

Calls, bookings and OTP challenges now have authoritative versioned rows.
Primary-key call/load claims precede freeze, booking row, durable intent and send.
Only FAILED bookings without intent can release claims. Past intents always block.
The 110-entity backup matched projections exactly; the old control remains frozen
and unread. Auxiliary inserts/upserts are independent and best effort.

| Real-table probe from Fly, synthetic business data | Result | Median | p95 |
| --- | --- | --- | --- |
| 8 contenders for one load | 1winner | 26217.0 ms | 27099.2 ms |
| 8 conditional booking transitions | 1winner | 4882.4 ms | 5770.5 ms |
| 8 independent call sequences, four saves each | All completed | 17186.3 ms | 18065.5 ms |

Independent sequences took 18065.7 ms wall time versus 137459.8 ms summed durations,
showing overlap without a global business-state lock. These are contention tests,
not ordinary voice-tool latency. Earlier429 failures remain recorded. SQL starts
are paced at 4/s with at most 4 in flight. Uncontended read samples from Fly measured
250.0 ms median and 260.8 ms p95, including pacing. Two redundant booking reads were
removed. A simulated 0.35 s-per-operation case can exhaust its budget after intent,
send nothing and conservatively retain claims. See [storage evidence](docs/storage-cutover.md)
and [budget limits](docs/prototype-evidence/candidate-booking-budget.json).

## 4. PDF requirements

| Requirement | Current evidence/status | Label |
| --- | --- | --- |
| Active carrier authority | Actual MC 138328 passed; broker-only policy fixture refuses | LIVE / SIMULATED |
| Email code during call, before loads | Fresh SMTP email, human code entry, failed-code retry preserved | LIVE |
| Lane/equipment matching and load fields | Real OPEN future inventory, public field projection, unit-tested mapping | HYBRID |
| Private ceiling and negotiation policy | Unchanged pricing numbers; real counter 3600 against 4200; backend bound/round checks | HYBRID |
| Three-counter limit | Durable offline policy checks; rehearsals each used two rounds | HYBRID |
| Booking while on call | Earlier real PENDING receipts exist; new per-entity candidate write path awaits final call | HYBRID |
| Mocked senior-rep handoff and native end | Fixed line passed prior voice check and final-version text; same-run live gate pending | HYBRID |
| Twin records and all activity | Real rehearsal records, consent proofs, redacted transcripts; auxiliary write loss remains a limit | LIVE |
| HappyRobot Apps and KPIs | Existing signed-in service fallback; real/synthetic cohorts separate; rep decisions separate from TMS | LIVE |
| TMS faults and duplicate protection | Fake TCP, partial/late receipts, save recovery, claims and replay checks | SIMULATED |
| Standard/edge/adversarial QA | 17 language cases, five exact checkpoints,11 final-version scenarios; failures retained | SIMULATED / HYBRID |
| Endpoint authentication | 32 service role checks and 12 App session checks rejected as expected | LIVE |
| Docker, one-command deployment, web call | Non-root Python 3.12 image, make deploy, existing Fly VM; no phone provisioned | LIVE |
| Build note, prospect email, repo, access, video | Drafts/source prepared; owner publication, reviewer access and video remain | HYBRID |

Personal-inbox OTP is the approved demo scope, not real carrier-contact ownership.
AI summary/sentiment is not mandatory in the PDF: summary is deterministic and
sentiment remains not_assessed. PENDING finalization still awaits Luke's answer.

## 5. Load ledger

Nine historical wire sends across seven loads: six complete pending receipts,
two explicit errors, one UNKNOWN, zero BOOKED. This run has made zero new sends.
The prototype's two prior intent rows are only part of that cross-harness history.

| Load | MC | Rate text | Exact outcome |
| --- | --- | --- | --- |
| LD01086 | 872144 | 7900 | PENDING, XNX9PRX500PBRT9Z |
| LD01082 | 872144 | 2142.00 | PENDING, YCAG1N39CWWFCKXZ |
| LD01081 | 872144 | 1324.50 | INVALID_RATE, positive integer required |
| LD01075 | 872144 | 1 | PENDING, CWUYRY2VPN298ZEM |
| LD01081 | 872144 | 1324 | PENDING, Z7G5ZSRACFA5BU7G |
| LD01086 | 872144 | 7900 | Authorized historical replay, ALREADY_BOOKED |
| LD01077 | 138328 | 3225 | UNKNOWN, no retained receipt/reference; later status-only PENDING |
| LD01094 | 138328 | 1075 | ACK_PENDING/PENDING, 3PUHTGRJNDQ5EKMM; consent review, Confirm blocked |
| LD01085 | 138328 | 2950 | ACK_PENDING/PENDING, EME8U26DKEX5DESS; valid consent/local rep approval, shortened-speech failure |

No replay is authorized. LD01062 was OPEN at final preflight, but no owner call
started in that bounded window; it was not spent or claimed. Refresh inventory
before allocating the next take. The [TMS contract](docs/tms-contract.md) preserves
the earlier sends and their limits.

## 6. Proposed architecture changes

- D-8: distinguish price agreement from permission to submit. Require the exact
  load/total question and fresh natural approval before intent. Permit one exact
  neutral acknowledgment afterwards, retaining all ignored IDs in the proof.
- Make per-entity rows authoritative, with a separate claims table and ordered
  crash-safe writes. Keep orphan reservations blocked for review.
- Use off/rehearse/live modes. A mode flag never replaces owner allocation.
- Keep T-7's authenticated service fallback for Apps while its native gateway fails.
  The ops key stays server-side and actor identity comes from verified sign-in.
- Keep tentative handoffs, TMS confirmations and rep decisions as separate KPIs.
- Review deterministic terminal-call closure: one ineligible simulation omitted
  closing tools and idled about 66 seconds. Eligibility and booking protection held.
  No per-outcome automatic hangup action/flag was verified in the exposed platform
  schemas. Shortening the global silence timeout would also affect code waits.

ARCHITECTURE.md and Questions.Md were not edited. Claude decides the final design
and documentation changes after reviewing these commits.

## 7. Still unproven

- The final candidate's single-run nine-item gate, including a new receipt and owner Confirm.
- External finalization, cancellation, expiry and full money semantics; Q8 awaits Luke.
- Reliable pronunciation and every possible interruption/utterance. Some text
  traces establish a bounded language phase only. See [conversation coverage](docs/conversation-coverage.md).
- High-concurrency voice latency, auxiliary log durability and cross-machine receipt
  journal durability. The local container journal is ephemeral and must be exported.
- The newer App UI source in Production, actual reviewer access and the final video.

## 8. Resources and cleanup

| Resource created/changed/reused | Identity and how to scrap later |
| --- | --- |
| Isolated code | prototype/e2e in e2e-prototype worktree. Export ignored evidence before owner-approved archival. Main stays 2d08ae1; harness stays 6ed7d4b. |
| Fly | Existing codex-e2e-lab-sg-20261031, machine 84eee5dbdd0008, iad, 256 MB. Use make idle, then stop the same VM after exports. No new VM/volume/plan; budget USD3 total, no hard cap. Billed total not verified. |
| Prototype workflow | 01a19476-5384-704b-9c5e-569fd96f9adf, slug yhcdrf4kne4j. Unpublish only this prototype after preserving evidence; original 01a18119-67a1-79a3-b220-369aa359d4fb untouched. |
| Versions this run | v12=01a195d8-59dc-7e7e-a713-61e78631fb49; v13=01a195e6-06cd-74c6-af1c-e624fa32d35c; v14=01a195f3-8fbf-7706-8f4e-1068ee1a92bd; v15=01a195f7-d2e8-79da-a553-ddbeed310f4d; v16=01a1960a-43b4-7448-8310-93e814308f2c; Production v17=01a1961c-9e0b-7d40-aea5-957e4d6e1453. Preserve failures before owner cleanup. |
| Native QA | Eight reused scenario resources; all run IDs in final/native conversation evidence. Six custom-eval resources, including failed baseline 01a19608-4c0a-7c90-b512-60df0953db73; exact IDs in checkpoint evidence. Export definitions/outcomes before removing only prototype tests. |
| Twin | Existing proto_carriers, proto_calls, proto_call_transcripts, proto_call_events, proto_otp_challenges, proto_negotiation_rounds, proto_bookings, proto_unmet_demand, proto_booking_claims. Keep records/control frozen until export; later owner cleanup must target only this namespace. Synthetic contention probe 7fe611ed2eff49f485ce3167fcc99cd3 and earlier failed probes remain preserved. |
| App | Existing codex-lab-carrier-sales-v24, renamed HappyRobot Logistics Carrier Sales; alias carrier-sales-santiago.happyrobot.dev. Old URL remains active. Two-file candidate overlay exactly matches source e6766e64915e4a4069253fb28fbb7d358c8d6b79 over b2fd163. Production source publish canceled because it merges App main. Revert metadata/alias or publish only after owner review. |
| Private configuration | Existing approved keys reused; no roles/capacity changed. Remove only prototype-specific app variables/keys after owner cleanup. No values in Git. |
| Local recording setup | Unfinished OBS scene Carrier Sales Final Take and new macOS Screen Capture 2. No recording started. Owner now handles video and can remove that scene/source later. |

The [synthetic resource inventory](docs/prototype-evidence/candidate-synthetic-resource-inventory.json)
lists the exact 64 call, 24 booking and 36 claim row IDs from the four storage probes.
No rows or resources were deleted.

## 9. Before merge and submission

1. Owner replies Ready, makes one final allocated real voice call, then confirms
   its valid pending receipt in Apps. Verify the exact nine items on that run,
   export the receipt, append its ledger entry and block its spent load.
2. Switch live off immediately, verify health, finish the final record and restore
   Fly idle/stopped state. Do not resend or use a second send after a clean run.
3. Resolve/review the ineligible-call closure failure and slow-storage limits.
4. Review Q8/Luke's reply, App source publication and this candidate with Claude.
5. Owner supplies the video, reviewer accounts and access, selects the exact private
   remote commit and approves push/sharing/submission. Nothing was pushed or sent.

Checks and source hashes are in [QA results](docs/qa-results.md). The current 34
runtime/policy/requirements hashes match deployed bytes. The delivery check also
compares these contents against the final Git commit's blobs.
