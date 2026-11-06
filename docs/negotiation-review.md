# Reciprocal negotiation review

Local implementation, November 7, 2026. Nothing in this change is published. The candidate service, App and voice Version 15 remain unchanged. Main remains the preserved baseline; these changes belong to ultimateProposal.

## Business policy

The service, not the voice model, decides money. A first ask within 10% above the standing offer may earn at most 2% of the opening price, rounded down to $25. Later asks must improve on the best prior ask. The concession is the smaller of that same 2% limit and half the carrier's improvement, rounded down to $25. Every amount remains bounded by the fresh working cap. An authorized ask below the resulting counter is accepted at the caller's amount, never rounded upward.

A distant ask, an increased demand or a tiny downward adjustment earns no automatic increase. A new above-offer ask consumes one round, including a hold. Exact repeated asks do not spend another round. Three rounds is a limit, not a promised route to the cap. Acceptance of the standing offer remains possible after the final counter. The pricing-v1 opening and working-cap calculation remains unchanged; its legacy target array no longer controls negotiation.

These thresholds are explicit demonstration policy choices for brokerage review, not market-derived rates or proof of optimal conversion. The service does not invent fuel, market, capacity or urgency signals.

## Executed scenarios

All figures below use the same offline fixture: opening $4,600, working cap $5,000. These are not new human calls. Machine-readable results are in [scenarios.json](evidence/reciprocal-negotiation/scenarios.json).

| Carrier asks | Service offers | Result |
|---|---|---|
| $15,000, $14,000, $13,000 | $4,600, $4,600, $4,600 | No concessions for distant asks |
| $6,000, $5,500, $5,200 | $4,600, $4,600, $4,600 | Moderate descending probes do not advance a ladder |
| $5,000, $4,900, $4,800 | $4,675, $4,725, $4,775 | Bounded reciprocal concessions |
| $5,000, $5,100, $5,200 | $4,675, $4,675, $4,675 | Raising the demand does not earn more |
| $5,000, $4,999, $4,998 | $4,675, $4,675, $4,675 | Token changes do not round into concessions |
| $15,000, $5,000, $4,900 | $4,600, $4,675, $4,725 | An extreme anchor cannot amplify a later concession |

The final counter in each sequence is the third offer, not necessarily the working cap. This is not a claim that negotiation is ungameable: a carrier can still seek the best authorized deal. The policy bounds the cost and removes automatic per-round increases.

## Memory and failure tests

Executed through the actual Twin adapter with offline storage and HTTP fixtures:

- Redial resumes the standing offer and shared three-round budget after independent verification and search.
- Repeated identical asks across calls do not buy another concession.
- A day of waiting does not reset the budget; a different carrier has separate memory.
- Separate service clients simultaneously negotiating the same carrier/load share CAS rounds 1, 2 and 3.
- Lost call writes and lost acceptance responses preserve the shared decision on retry.
- Contended writes fail closed; no booking is sent.
- Fresh lower caps durably retract quotes, including when another call holds an older quote. Later cap recovery cannot resurrect it.
- Material shipment changes allow a fresh shared negotiation. Price-only changes and workflow versions do not.
- Call-global rounds remain bounded across different loads; existing verification, consent and reservation recovery regressions pass.
- Private caps and negotiation-memory internals do not appear in agent responses.

Full validation: `make check` passed with 581 tests, 99% combined service coverage and 97.5% business-rule branch coverage, including the new memory module. Ruff, strict mypy and module/function/complexity gates passed. Production Python physical lines: 3,850. No App code changed.

Independent review found and prompted fixes for two quote-retraction defects. Both now have regressions: search must persist a lower quote, and an older call quote must not override the shared decision.

## Unpublished voice draft

[Prompt draft v16](../happyrobot/prompt-proposal-v16.md) includes:

- Temporary email sending limits explained accurately, with a conservative ten-minute retry instruction.
- Complete MC collection and a correction opportunity for ambiguous matches, rather than treating a partial number as final.
- Immediate respectful exit on goodbye, even while a code or amount confirmation is pending.
- Safe driving wording tied to reading the verification code, not carrier eligibility.
- Shorter load pitch, retaining pickup time, weight, commodity and all operating conditions and fees. Delivery time, piece count and dimensions are available on request.
- Natural counter wording and brief acknowledgment of the caller's stated concern, without invented market evidence, strategy disclosures or invented prices.
- Saved agreement awaiting senior-rep review, not a claimed live transfer or confirmed booking.

No new native model simulation or voice recording has been executed against this local draft. Before release, run the draft with the revised service and verify: email send_limit; split MC 9999 followed by 9999; goodbye during code collection; unsafe driving; repeated fuel-cost request; high and moderate ladders; reachable concession and acceptance; redial; and a full agreement ending with the correct load, rate and pending review. Inspect tool arguments and listen to audio. Static prompt edits do not establish conversational success.

## Deployment boundary

The new `negotiations` table must exist in the selected Twin environment before deploying this service. It uses `id` text primary key, `version` integer and `data` JSONB, like existing tables. The table is allowlisted by the adapter but has not been provisioned remotely. The disposable local reviewer fixture already supports it. Do not add it to the call or booking population in the App.

There is intentionally no automatic expiry. Material shipment changes replace the active shared negotiation; per-call audit events retain the previous history. No historical call rows are rewritten or backfilled. The new policy applies prospectively. Memory is keyed by verified MC, not a uniquely authenticated human dispatcher; the existing demo inbox is still not production carrier identity.

Shared memory is written before the call row, not in a distributed transaction. A later refusal or failed write can consume a concession that was never heard. This conservative behavior prevents retries from refunding money. Simultaneous searches can briefly show a conservative older quote; negotiation rechecks shared state. No new voice-latency or capacity claim is made for the additional Twin reads and writes. Staging latency and conversation acceptance remain release checks.

Owner requested results before publication. No push, service deployment, workflow publication or live booking is authorized by this report.
