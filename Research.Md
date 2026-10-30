# Research and design decisions

I used Perplexity for deep research into US freight brokerage workflows and spoke with Gian Clerici about operational needs. Luke's [answers](Questions.Md) establish the challenge expectations; the research below explains my design choices.

## Industry input: Gian Clerici

**Source:** Voice notes shared by Santiago, 2026-10-30. Gian is Sales Lead at HM Cargo, Buenos Aires, with experience in commercial pricing and logistics for human and animal healthcare.

**Context:** His provider-quoting examples concern outbound workflows; this demo handles inbound carrier calls. His operational insights inform the design without changing the requirements.

### Relevant insights

- **Carrier history:** Show calls, loads offered, confirmed bookings and reasons for no agreement in Apps using Twin. Identify recurring mismatches and follow up; low conversion alone does not prove poor performance.
- **Conditions:** Communicate relevant TMS notes, including time allowances or waiting charges. Flag unclear terms for the simulated rep; do not invent terms or negotiate extra charges outside policy.
- **Written records:** Preserve the load, agreed rate, conditions and outcome in Twin. Distinguish pending agreements from confirmed bookings.

### Demo scope

Carrier history and reasons for no agreement are included as a view in the operations app (D-14). Load notes are read as written, and unclear terms are flagged for the rep. Confirmation emails remain a later option; insurance quoting, extra-charge pricing and outbound prospecting are outside scope. Gian did not resolve questions 1-3.

## Perplexity research: questions 1-3

**Source:** [Full research output](Archive/Perplexity_Questions_1-3_Research_2026-10-30.md), 2026-10-30. Key recommendations were checked against primary sources and the handbook. These examples do not establish majority industry practice.

### 1. When should the load be booked?

[C.H. Robinson](https://www.chrobinson.com/en-us/carriers/carrier-support/support-book-loads/) distinguishes making an offer from booking. This supports separating agreement from commitment, but does not establish mandatory senior approval.

**Decision (D-6 to D-8):** Keep a pending agreement in Twin, then book after simulated rep approval. Persist the attempt before sending it; uncertain results stay blocked for review, including after restarts. [AWS's retry guidance](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/) explains why local request IDs alone cannot make external bookings safe to retry.

### 2. Should returning carriers repeat OTP?

[RXO](https://rxo.com/carriers/technology/mfa-instructions/) documents MFA for its platforms, not an OTP requirement for every inbound call. There is no evidence here of a universal per-call policy.

**Decision:** Keep fresh OTP on every call as my POC assumption (D-9). Bind it to the call and MC, consume it once, and keep failure limits across resends. [NIST](https://pages.nist.gov/800-63-4/sp800-63b.html) informs these controls; it does not endorse email as an out-of-band authenticator. Luke-approved demo email proves inbox access, not carrier identity.

### 3. How should rates and ceilings work?

The [TMS handbook](https://fde-challenge-candidate-handbook-production.up.railway.app/spec/load-get/) defines `RATE` as the posted rate and exposes `MAX_BUY` only for enabled tokens. Perplexity could not access that handbook, so its claim that `RATE` was wholly undefined is not adopted.

**Decision (D-4, D-10, D-11):** Keep `MAX_BUY` as the provisional `max_rate` mapping. Confirm units and [booking validation](https://fde-challenge-candidate-handbook-production.up.railway.app/spec/load-book/) through controlled tests. Missing ceilings block negotiation; do not derive one from `RATE`. Derive offers from a versioned policy with keyed, load-specific gaps below the validated ceiling: a known percentage can reveal the ceiling by division. Ceiling headroom is not broker margin.

## Design impact

The four components in [ARCHITECTURE.md](ARCHITECTURE.md) remain. The research tightens booking recovery, OTP lifecycle and pricing rules. Implementation and live contract checks are still pending.
