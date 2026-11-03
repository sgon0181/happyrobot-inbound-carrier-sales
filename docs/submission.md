# Submission

What goes into each field of the candidate portal's submission form. Drafts for the owner to edit; fill in the two links marked `[...]`.

| Form field | What to give |
|---|---|
| Repository | The .zip built from `main` with `git archive` (no ignored files, so no secrets), or the private repository's URL |
| HappyRobot workflow URL | The Inbound Carrier Sales workflow, copied from the browser |
| Walkthrough video URL | The video, 5 minutes at most |
| Summary email to the prospect | The email below |
| Notes | The notes below |
| Files | `build-description.pdf`, made from [build-description.md](build-description.md) |

## Summary email to the prospect

**Subject:** Inbound carrier sales: what we built and next steps

Hi team,

We built an assistant that answers your inbound carrier calls. It checks the carrier's authority with FMCSA and confirms the caller with an emailed code, finds open loads on their lane in your TMS, negotiates within your pricing limits and reserves the load. A senior rep then confirms each booking from one dashboard, so nothing reaches your TMS without a person's click.

**What it does today**

- In a live test, a carrier passed both checks, countered twice and agreed a rate in the third round. The rep confirmed it in the dashboard and your TMS returned a booking reference.
- The agent never sees your rate ceiling, so it cannot reveal it, and the system will not accept a rate above it. Verification cannot be skipped, whatever the caller says.
- Every call is logged with its outcome, agreed rate and a step-by-step audit trail.
- The dashboard shows calls answered, verified carriers, deals handed to reps, bookings with their TMS status, and the lanes carriers asked for that you could not cover.

**How we tested it**

19 scripted conversations, covering normal calls, edge cases and attempts to trick the agent, plus over 400 automated checks on the rules. The rules held in every case. The one weakness found was the agent sometimes ending a call right after an agreement; the system still reserved nothing in those cases, and a fix is ready to review.

**Next steps**

1. Review the prompt fix together and put it live.
2. Agree the business rules we assumed: when the booking is sent, how your TMS marks a booking final (it currently answers "pending"), and the pricing margins.
3. Run a two-week pilot on a share of real inbound calls, measuring deals handed to reps per verified call.
4. Then send codes to each carrier's contact on file instead of a demo inbox, and connect the rep transfer to your phone system.

The walkthrough video, workflow and repository are linked below, and the build description is attached.

- Walkthrough video: [...]
- Dashboard: https://carrier-sales-santiago.happyrobot.dev
- Workflow: [...]

Thanks,
Santiago

## Notes for the reviewer

Start with README.md, then ARCHITECTURE.md; every decision and its reason is in docs/decisions.md, and QA results are in docs/qa-results.md.

Assumptions, as Luke invited: the booking (LOAD_BOOK) is sent when the rep clicks Confirm, not during the call (D-22), because the TMS has no cancel. MAX_BUY is used as max_rate (D-10). Every live booking returned PENDING with a reference, never BOOKED, so the dashboard shows the TMS's own status and never counts PENDING as confirmed. Codes go to one demo inbox, as agreed.

Bookings spend a load for good, so Confirm reaches the TMS only while LIVE_BOOKING is on; it is off by default. The dashboard needs a HappyRobot sign-in. Branch prototype/e2e is an earlier prototype, kept for reference only.
