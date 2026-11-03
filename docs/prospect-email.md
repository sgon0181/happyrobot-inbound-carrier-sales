# Prospect email (draft)

Draft for the owner to edit and send. Fill in the two links marked `[...]` before sending.

---

**Subject:** Inbound carrier sales: working demo and results

Hi team,

I built an assistant that answers your inbound carrier calls. It verifies the carrier's authority with FMCSA and an emailed code, finds open loads on their lane in your TMS, negotiates within your pricing limits and reserves the load. A senior rep then confirms each booking from one dashboard, so nothing reaches the TMS without a person's click.

In today's live test, a carrier called in, passed both checks, countered twice and agreed a rate in the third round. The rep confirmed it in the dashboard, and the TMS returned a booking reference. Across 19 scripted test conversations, including attempts to extract your ceiling, skip verification or talk the agent into a booking, the rules held every time. The one weakness found was an agent closing a call too early after an agreement. A prompt fix is ready for review; even before it, the system never booked or reserved anything in those cases.

The dashboard shows calls answered, verified carriers, reserved handoffs, bookings and their TMS status, and the lanes carriers asked for that you could not cover.

- Walkthrough video: [...]
- Dashboard: https://carrier-sales-santiago.happyrobot.dev
- Voice workflow: [...]
- Repository: https://github.com/sgon0181/happyrobot-inbound-carrier-sales

The build description in the repository covers how it works, what was measured and the assumptions for you to review, such as how your TMS marks a booking final.

Thanks,
Santiago
