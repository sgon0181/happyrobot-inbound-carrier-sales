# Dashboard clarity, approved 2026-11-04

The assignment requires an internal HappyRobot App that lets an operations manager understand calls and act without raw platform logs. This change makes existing records useful at first glance. It does not change voice behavior, pricing, booking rules, credentials or data.

## Order and scope

1. **Work first:** show reservations needing review and uncertain or stalled submissions before performance statistics. Separate current booking status from historical call results.
2. **Explain every number:** replace Northstar and code jargon with business labels. Show the conversion numerator, denominator, reporting scope and small-sample warning beside the percentage. Keep test traffic separate from business KPIs.
3. **Use consistent populations:** remove the mixed call/booking funnel. Historical call progress uses call records only; current booking status uses booking rows only. Do not compare incompatible units or silently change the service's KPI definitions.
4. **Make records readable:** format monetary amounts, shipment times and negotiation rounds; put implementation identifiers behind technical details. Keep missing data explicit. Put the reservation's next action before secondary details, and let status text wrap.
5. **Ship a bounded change:** preserve the template, authentication, receipt recovery, version checks and action handlers. Publish the existing Carrier Sales App after checks and independent review, then refresh release/submission records. Workflow Version 8 and service release 17 remain unchanged.

## Acceptance

- An operator can identify the current data scope, the next action and its affected record without hover text or platform logs.
- A historical 1/3 reservation conversion is visibly explained as 33%, not three distinct carriers or a final-booking success rate.
- Test overview does not display real business KPI values. Changing scope never silently changes the cohort of only part of the page.
- Historical reservation counts survive a release and reuse, while current booking counts reflect current states. Failed submissions cannot make two identically named metrics disagree.
- A call timeline reads as a sequence of carrier asks and service decisions, retains earlier asks and captured load terms, and excludes expected codes, credentials and ceilings.
- Confirm stays disabled when sends are off or unknown; authentication, version forwarding and receipt recovery tests still pass. No booking action is used for verification.
- Frontend tests, lint, typecheck, production build and dependency audit pass; service make check retains 100% coverage. Changed modules remain at most 300 lines. The unchanged template sidebar is 726 lines and remains a baseline size exception.
- Published real and test overview, reservation details and call activity are visually checked at the intended 1280px demo width, including long labels and missing historical fields.

## Verification limits

This improves communication of captured records. It does not repair missing activity capture, prove carrier identity from the demo inbox, establish production capacity or prove zero indirect ceiling inference. Publishing the App does not publish a voice workflow or deploy the service.

## Delivery record

Implemented in reviewed commits 7262be4 and 8ff094a. The latter makes empty strings explicit after the live visual check. See [the dashboard release](../releases/2026-11-04-dashboard-clarity/README.md) for publication, validation and remaining limits.
