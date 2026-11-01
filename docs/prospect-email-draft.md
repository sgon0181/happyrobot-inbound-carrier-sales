# Prospect summary email, draft only

Do not send this draft until the review links and video below are final. Sending is not authorized by the current isolated-build instruction.

Subject: Inbound carrier sales prototype and demonstration

Hi team,

I built a prototype that handles the first part of an inbound carrier call:
authority verification, an emailed code, load matching, controlled negotiation
and a tentative booking request, followed by a simulated senior-rep handoff.

The operations dashboard brings the agreed rate, actual TMS receipt, review
status and call record into one place. Rep approval stays separate from the
TMS status, so a pending request is never presented as a confirmed booking.

The demonstration will show the real call journey, the operator review and
the documented standard, failure and adversarial checks. The build document
explains the assumptions, controls and remaining production work.

Review package:

- Private repository and submitted commit: pending owner-approved publication.
- Workflow: https://platform.happyrobot.ai/deployments/yhcdrf4kne4j
- Dashboard: https://codex-lab-carrier-sales-v24.happyrobot.dev/
- Walkthrough video: pending final recording and review.

The first live test exposed a consent defect, which is retained as failed
evidence. A subsequent real call passed strict permission, received a PENDING
receipt and was rep-approved in the dashboard. Its shortened spoken disclosure
was corrected and checked separately without submitting another booking.
The evidence distinguishes the original call from that later speech check.

Thanks,
Santi
