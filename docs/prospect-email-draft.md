# Prospect summary email, draft only

Do not send this draft until the clean-call result and review links below are
final. Sending is not authorized by the current isolated-build instruction.

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
- Walkthrough video: pending clean-call recording.

The first live test exposed a booking-consent defect. It is preserved as failed
evidence; a clean retest is required before claiming the final flow passed.

Thanks,
Santi
