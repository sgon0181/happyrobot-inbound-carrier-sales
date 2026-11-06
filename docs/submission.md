# Submission

The five deliverables the brief asks for, and where each one is.

| Deliverable | Where |
| --- | --- |
| 1. Summary email to the prospect | [Below](#prospect-email) |
| 2. Build description for IT and business review | [build-description.md](build-description.md), exported as a PDF with the submission |
| 3. Code repository | Source ZIP of `main`, uploaded through the portal (the recruiter accepted this). A private GitHub link is available if preferred. |
| 4. HappyRobot workflow link | [Workflow, live Version 19](https://platform.happyrobot.ai/fdesantiagogonzalezalvarez/workflows/6oaskq84xpfc/editor/l6zo75s4s4vk) and its [web call](https://platform.happyrobot.ai/deployments/6oaskq84xpfc) |
| 5. Walkthrough video, about five minutes | Recorded by the owner from the [recording script](recording-script.md); link added at submission |

## Prospect email

Subject: A carrier desk that qualifies calls and keeps your team in control

Hi team,

We built a working carrier sales desk around the problems you described: missed calls at peak times, inconsistent negotiation and agreements that are hard to trace.

A carrier can call at any time. The AI agent identifies itself, checks the carrier's FMCSA authority, verifies an emailed code, finds a matching load and negotiates within your pricing limits. Every agreement becomes a reservation that a senior rep reviews, with the call, shipment and price history in one place, before a booking is sent to your TMS.

Your operations team sees how many verified calls end in a reservation and where the others stop: failed verification, no suitable freight or no agreement on price. Each number opens the calls behind it.

The build is tested against scripted, edge-case and adversarial conversations, and its pricing limits, verification and failure handling have automated tests. For this demonstration the code goes to a test inbox; a rollout would use your enrolled carrier contacts and named reps.

As a next step, I suggest a supervised shift: agree the pricing thresholds and contact list with your carrier sales team, then compare time to first offer, verified calls reaching a reservation and unresolved requests against a normal shift.

Try it here:

- Web call: https://platform.happyrobot.ai/deployments/6oaskq84xpfc
- Operations desk: https://carrier-sales-proposal-sg.happyrobot.dev/

Best,
Santiago

## Before submitting

1. Record the human call and walkthrough on the live workflow, following the [recording script](recording-script.md).
2. Rebuild the ZIP and the build description PDF from the final `main` commit (`make zip`).
3. Upload the ZIP, PDF and video link through the portal. Keep the service running until the review is done.
