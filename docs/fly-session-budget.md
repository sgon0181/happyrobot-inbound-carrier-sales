# Fly test-session budget

Owner budget: USD3 total for this challenge, clarified on 2026-11-01.
This is not permission for an indefinite monthly plan.

Use the existing codex-e2e-lab-sg-20261031 app, one shared-cpu-1x with 256 MB
Machine in iad, shared IPv4, no autoscaler, no extra app or database. Deployment
uses --ha=false. No prepaid credits, support plan or reservation is purchased.

During active QA, make warm temporarily sets min_machines_running=1 for that
one Machine and explicitly starts it if it was stopped or suspended. The
minimum setting alone does not start a stopped Machine. Run make idle when
the session pauses or finishes. The tracked
default remains 0 with auto-stop enabled. Both commands require exactly one
existing Machine and use the already-built prototype image with --ha=false.
This avoids paying for continuous uptime after testing, while allowing the
same app to start for a later authorized review.

The published compute rate is USD2.19 per 30 days. Four hours is approximately
USD0.0122 before traffic, tax and existing usage. Stopped root filesystems can
still incur storage charges. These are estimates, not a hard account cap.
[Pricing](https://docs.fly.io/about/pricing)

Fly's trial stops Machines after five minutes. The owner completed payment
setup, and the Billing page now lists a saved payment method for the same
account that owns this app. The continuous-runtime check passed: 373.91 seconds
observed without a restart, VM uptime reaching 440.93 seconds. Card entry and any payment terms
were completed by the owner; no card fields or numbers enter this repository.
[Trial limits](https://docs.fly.io/about/free-trial)

Fly does not provide a hard spending cap or billing alerts. Check the account
usage before and after the session. Remove billable resources after the
challenge only with owner authorization; stopping a Machine is not equivalent
to deleting all billed resources.
[Cost controls](https://docs.fly.io/about/cost-management)

No persistent volume has been added in this continuation. Exact receipts
remain in Twin and are exported privately immediately after a real send.
The container journal is supplementary and still ephemeral across replacement.
