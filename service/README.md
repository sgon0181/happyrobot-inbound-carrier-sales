# Carrier Sales Service

Python 3.12 service for inbound carrier verification, load matching, negotiation,
booking permission and one-shot TMS submission. See [the candidate report](../PROTOTYPE_REPORT.md)
for the tested run, deployed version and remaining limits.

## Run and deploy

On a fresh clone, create the ignored environment with Python 3.12:

```bash
python3.12 -m venv secrets/venv
secrets/venv/bin/python -m pip install -r requirements.txt
```

```bash
make test
make deploy
make warm
make idle
```

Tests use a local fake TCP TMS. Their network guard blocks external connections.
Do not import service.tests in a live process. The deploy command builds the
non-root Docker image and updates the existing approved Fly app only.
Deployment needs Docker Desktop running and an installed, authenticated Fly CLI.
Provision required runtime variables privately in the existing Fly app's secret
store first. make deploy does not upload the local .env file.

Copy the blank root .env.example into an ignored .env and provision existing
credentials privately. The service needs TMS access, FMCSA, the HappyRobot
organization and API key, the prototype workflow ID, separate agent and operations
keys, OTP hashing and pricing secrets, and Gmail SMTP sender credentials.
PROTOTYPE_WORKFLOW_ID must identify the prototype whose native speech is checked.
Expected codes and internal pricing never belong in voice tools or logs.

BOOKING_MODE defaults to off:

| Mode | Behavior |
| --- | --- |
| off | No booking intent or send. |
| rehearse | Checks actual native booking consent and records rehearsal_complete, without a booking intent or send. |
| live | Requires a verified real call, current stored agreement, fresh natural permission, eligible inventory and durable claims before one send. |

Changing a mode does not authorize a load. Every live test needs allocated
inventory and the owner's permitted call. Read the authenticated health route
using the agent key to verify the deployed mode. Turn live mode off immediately
after the take. Repeated tool requests never authorize resending a spent load.

## Storage and safety

Twin entity rows are authoritative. Calls, bookings and OTP challenges each use
row version checks. Call and load claims use primary-key conditional inserts in
proto_booking_claims. Claim first, freeze the current agreement, create the
booking row, persist intent, then send. A crash gap remains blocked for review.
Only FAILED bookings with no intent can release a claim. Every past intent
continues to block its load. The frozen legacy control row is excluded from views.

Events, rounds, carriers, unmet demand and transcripts use independent auxiliary
inserts or upserts. They cannot block booking submission, but failed auxiliary
writes are a reliability limit. MemoryRepository follows the same row contract.
The measured cutover and contention results are in [storage-cutover.md](../docs/storage-cutover.md).

The tracked policy file service/policy/blocked-loads-v1.json separates spent,
protected and void inventory. Pricing policy numbers are unchanged. The model
receives public offers only, with at most three counter rounds across a call.

Price agreement and permission to book are separate. The service reads actual
native messages and requires its exact load-and-total question as the final
sentence, an uninterrupted turn, a fresh same-session affirmative and the current
agreement. Natural short approvals are accepted; conditions, rate questions,
interrupted or stale speech fail closed. The fixed handoff text is unchanged.

A valid PENDING receipt becomes ACK_PENDING. Ambiguous transport becomes UNKNOWN.
The final controlled owner run 5783608f-d54b-4a5d-b028-89db98ae10ec produced one
PENDING receipt and saved App approval. LD01062 is spent and blocked. See the
report for complete evidence and quality limits.

Only authoritative final evidence becomes CONFIRMED. Neither rep approval nor
simulated speech changes the external TMS. UNKNOWN and caller_confirmation_review
have no Confirm action. LD01094 remains blocked for consent review.

Receipt bytes, phase, digest and intent are captured independently of socket
cleanup. Persistence recovery never resends. The private container journal is
ephemeral, so export it before replacement. No cross-machine durability is claimed.

## Operations and access

Every service route requires its agent or operations credential. The signed-in
HappyRobot App uses the operations API from its server because the native Apps
Twin gateway failed. The ops key stays server-side and the verified App session
supplies the rep identity. Real and synthetic cohorts remain separate.

Transcripts preserve a contextual MC number and redact code attempts, including
failed and spoken attempts. Ambiguous mixed code/MC labels favor redaction.
Collection retries incomplete projections and does not rewrite completed current
projections. The summary is deterministic and sentiment remains not_assessed.
Privileged platform recordings and ignored evidence are private.

Use make warm only during active work, then make idle. Keep the existing single
256 MB Fly Machine. The owner budget is USD3 total and Fly has no hard spending cap.
No new machines, volumes, plans or prepaid credit are authorized.
