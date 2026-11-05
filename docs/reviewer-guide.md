# Reviewing the carrier sales proof of concept

For the current proposal, start with [one-command review and current evidence](readiness.md), then [the five-minute owner script](proposal-demo.md). The historical hosted examples below remain useful but do not identify the development candidate.

## Preserved baseline examples

The following links, rubric and numbers describe the original Version 8/App Build 24 review. Use the [current candidate rubric](proposal.md#challenge-rubric) for newer evidence; historical failures are not erased.

[Reservations](https://carrier-sales-santiago.happyrobot.dev/) opens the rep's queue. Search by MC, carrier, load or lane and open [the filmed Werner agreement](https://carrier-sales-santiago.happyrobot.dev/?view=reservations&load=LD01088&run=ec839a6a-d47f-49a7-94d7-617c19049b7f) for its $975 opening, $1,000 agreement, native recording and Twin timeline. [Bookings](https://carrier-sales-santiago.happyrobot.dev/?view=bookings&load=LD01080&run=ddae86e8-c7b0-43b6-8dc1-eb902b45c33f) contains the separate historical PENDING acknowledgement. [Overview](https://carrier-sales-santiago.happyrobot.dev/?view=overview) explains 49 recorded calls, the conversion to a reservation, losses and carrier payment changes.

| Requirement | Evidence |
|---|---|
| Authority and OTP before matching | The recorded call has authority and successful code events before its search. The service rejects searches without verification. The demo code checks access to the configured inbox. A pilot should use a contact sourced from trusted carrier records. |
| Negotiation within a private ceiling | The voice agent asks the pricing service to decide. The filmed $1,000 ask was accepted in pricing round one with zero agent counteroffers. Higher asks receive a bounded response and three consumed policy rounds end bidding. The pricing ceiling stays in the service. [Pricing rules](../service/core/negotiation.py) |
| Structured activity, mocked transfer and rep control | Twin stores call and reservation histories. The originating call and load are joined by run ID so a reused load cannot show another carrier's agreement. Web calls use a spoken handoff. A rep must confirm before submission. |
| Unreliable legacy TMS | The service validates fixed-width responses and applies bounded retries to reads. A booking send uses the rep's version and a fresh load check. It is never blindly retried because the protocol has no idempotency key. PENDING and UNKNOWN each have their own review path. [Contract evidence](tms-contract.md) |
| Business reporting | Each clickable numerator opens its calls. The 49 completed demo sessions span workflow versions. The figures describe the proof of concept, including its losses. [Cohort and formulas](kpis.md) |
| Standard, edge and adversarial QA | The baseline section of [QA results](qa-results.md) separates the 487 offline service tests, 118 mocked text checkpoints, two complete text replays and human call evidence. A recorded price correction drove the focused retest. The replay closing limitation remains documented. |
| Deployment and responsibilities | [Build description](build-description.md) covers Docker, one-command deployment and system owners. [Decisions](decisions.md) records pricing assumptions and the interpretation of PENDING. |

A supervised pilot can compare dispatcher time and verified calls producing a rep-ready agreement with a comparable staffed shift. Telephony and a staffing baseline are needed to measure missed calls, waiting time and labor impact.

Luke's November 5 guidance asks for a working call at volume for both IT and business stakeholders. Review the filmed agreement and the 49 recorded sessions together. These calls span workflow versions and do not establish concurrent capacity. The source ZIP is accepted through the portal, and a private repository link is an alternative. For that route, the account to invite is supplied after reviewer assignment. [Dated clarification](questions.md)
