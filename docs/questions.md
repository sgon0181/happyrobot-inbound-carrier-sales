# Questions to Luke

PDF: [challenge brief](FDE_Technical_Challenge_-_Inbound_Carrier_Sales.pdf).

Luke replied on 2026-10-30 (Australia/Sydney): [source email](https://mail.google.com/mail/u/?authuser=santiagog11999%40gmail.com#all/1a18873af586e52d). That initial reply asked the candidate to choose and document assumptions for questions 1 to 3. The later email below accepts the demonstrated booking approach. Project assumptions are recorded in [`decisions.md`](decisions.md).

1. **Q:** When should I actually call `LOAD_BOOK`? The PDF says the load is tentatively reserved before the senior rep confirms, but `LOAD_BOOK` commits the booking and I couldn't find a cancellation operation in the handbook. Should I book as soon as the carrier agrees to the rate, or save the pending agreement in Twin and only call `LOAD_BOOK` once the simulated senior rep approves it through the Apps dashboard?

   **Reference:** PDF pp. 2-3, Process steps 5-6; [LOAD_BOOK](https://fde-challenge-candidate-handbook-production.up.railway.app/spec/load-book/).

   **A:** On October 30 Luke left the timing to the candidate. On November 5 he accepted the approach in the November 3 follow-up, described under Q8.

   **Our assumption (D-22, replacing D-8):** Reserve the load in Twin at rate agreement, then send `LOAD_BOOK` once when the senior rep confirms. See [`decisions.md`](decisions.md) and [the architecture](../ARCHITECTURE.md#10-reservation-and-confirm).

2. **Q:** Do I need to verify the OTP on every call, even if the carrier has called before?

   **Reference:** PDF p. 2, Process step 3; p. 4, Carrier identity verification (OTP).

   **A:** Luke: intentionally ambiguous; choose and document an assumption. He did not specify returning-carrier OTP policy.

3. **Q:** What format should I send the rate in for `LOAD_BOOK`, and what minimum and maximum amounts does it accept (Or is this part of the challenge)? Also, is `MAX_BUY` the same thing as `max_rate` in the PDF?

   **Reference:** PDF p. 2, `max_rate`; [LOAD_GET](https://fde-challenge-candidate-handbook-production.up.railway.app/spec/load-get/) and [LOAD_BOOK](https://fde-challenge-candidate-handbook-production.up.railway.app/spec/load-book/).

   **A:** Luke: intentionally ambiguous; investigate and document assumptions. Rate format, bounds and the `MAX_BUY` mapping were not confirmed.

   **Live read-only evidence, 2026-10-30 (Australia/Sydney):** A study of 302 full `LOAD_GET` records found `MAX_BUY` on every one with our token, always above `RATE`, unlike the handbook examples. This confirms field availability, but does not prove the mapping to the assignment's `max_rate`, currency units, or booking validation rules. That read-only study performed no booking tests. Later [2026-10-31 booking experiments](tms-contract.md#booking-experiments-2026-10-31) support whole-value initial acceptance and record pending acknowledgements, but not currency/scale, full bounds or finalization. The handbook leaves accepted bounds undocumented. The summary and its limits are in [`docs/tms-contract.md`](tms-contract.md). `python3 scripts/query_loads.py --load-id LD01023` re-checks that one load; it does not reproduce the study.

4. **Q:** Who is the demo actually directed to? Should I present it like I'm showing the solution to the brokerage's business and operations team, their IT team, or directly to you guys as technical reviewers? Basically, should I focus on showing the customer how it solves their problem, or walk you through how I built it?

   **Reference:** PDF p. 5, Deliverables items 1, 2, and 5.

   **A:** The October 30 guidance emphasized the brokerage's business team. On November 5 Luke specified both IT and business stakeholders and asked for a working call at volume. The reviewers will evaluate the code, dashboard and demo.

5. **Q:** When you said creativity, what exactly did you mean? Once the requirements are covered, should I focus on creative ways to solve the customer's actual problems, or are you also looking for extra ideas beyond the brief? For example, I had an idea of adding an animated face to the voice agent for a FaceTime-style experience. I could go quite far with something like that, but I'd like to understand whether you'd value that kind of extra feature or prefer that effort to go into making the solution more useful for the client and final end goal of helping the customer make more revenue.

   **Reference:** Your comment about creativity during our conversation; PDF p. 1, Problem.

   **A:** Creative additions are optional. Follow the rubric and guide, and add what would be valuable to a real client or business. No particular extra feature was requested.

6. **Q:** Is it fine if I deploy the Dockerized integration service on Fly.io, or should I use the same hosting platform as the TMS? The PDF says a cloud environment of the customer's choice, so just checking if you have a preference.

   **Reference:** PDF p. 4, Deployment.

   **A:** Fly.io is fine; any cloud environment works.

7. **Q:** FMCSA lists a carrier telephone number, but I haven't found any test carrier/contact records. For the demo, should I send the OTP to that registered number, or is it fine to map a carrier to my own phone/email and clearly mark it as demo data? Any specific test MC numbers you'd like me to use?

   **Reference:** [FMCSA API fields](https://mobile.fmcsa.dot.gov/QCDevsite/docs/apiElements), `telephone`.

   **A:** Use a web-call trigger and deliver OTP through an email integration to my personal email, rather than SMS or a real carrier number. No specific test MC numbers were supplied. Document the email destination as demo data.

8. **Q:** Is `STATUS:PENDING` expected for my candidate token after `LOAD_BOOK`? What supported action moves an acknowledged request to `BOOKED`? If the sandbox intentionally stops at `PENDING`, what outcome should the demo demonstrate? If needed, could this be routed to the TMS owner?

   Earlier probes on the candidate token returned PENDING references. A separate active-carrier attempt lost its receipt and was recorded as UNKNOWN. The documented examples and those observations do not establish a general sandbox rule. [Probe and recovery evidence](tms-contract.md#active-mc-attempt-on-a-real-call)

   On November 3, 2026 Santiago described the completed web call and the separate rep-approved TMS submission. The response contained a reference and `STATUS:PENDING`. He proposed saving the carrier agreement in Twin, waiting for the senior rep to authorize one send, and displaying the returned acknowledgement separately from a final booking. He also asked whether there was a supported step to reach `BOOKED`.

   Luke replied by email on November 5, 2026 at 02:32 Sydney time and accepted proceeding with that approach for the challenge. The rep's Confirm remains the only path to submit the booking. The reply supplied no finalization command or condition and did not establish whether every candidate token returns `PENDING`. The service retains the receipt, reports `ACK_PENDING` and recognizes a final booking only from authoritative `BOOKED` evidence. [November 5 email thread, owner access](https://mail.google.com/mail/u/?authuser=santiagog11999%40gmail.com#all/1a17a9a9aa848990)

## Logistics from the same November 5 reply

1. **Source submission.** Luke accepts the source ZIP through the candidate portal. A private GitHub link is an alternative. HappyRobot assigns a reviewer after submission, and Luke can provide the GitHub account to invite then. The ZIP route needs no GitHub invitation before submission.
2. **Review and availability.** Reviewers will assess the code, dashboard and demo. Show a working call at volume to IT and business stakeholders. Our evidence pairs the filmed call with 49 completed demo sessions across workflow versions. These sessions measure observed activity and provide no concurrent throughput benchmark. Luke did not say whether reviewers will operate the web call or dashboard themselves and gave no required uptime window.
3. **Sandbox inventory.** Luke believes inventory is unlikely to be limited and said a few more demo bookings were acceptable. If a limit is encountered, report it to him. No per-candidate quota, reset mechanism or unlimited supply was established.
