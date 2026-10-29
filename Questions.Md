# Questions to Luke

PDF: [challenge brief](FDE_Technical_Challenge_-_Inbound_Carrier_Sales.pdf).

1. **Q:** When should I actually call `LOAD_BOOK`? The PDF says the load is tentatively reserved before the senior rep confirms, but `LOAD_BOOK` commits the booking and I couldn't find a cancellation operation in the handbook. Should I book as soon as the carrier agrees to the rate, or save the pending agreement in Twin and only call `LOAD_BOOK` once the simulated senior rep approves it through the Apps dashboard?

   **Reference:** PDF pp. 2-3, Process steps 5-6; [LOAD_BOOK](https://fde-challenge-candidate-handbook-production.up.railway.app/spec/load-book/).

   **A:** Pending.

2. **Q:** Do I need to verify the OTP on every call, even if the carrier has called before?

   **Reference:** PDF p. 2, Process step 3; p. 4, Carrier identity verification (OTP).

   **A:** Pending Luke's clarification.

3. **Q:** What format should I send the rate in for `LOAD_BOOK`, and what minimum and maximum amounts does it accept (Or is this part of the challenge)? Also, is `MAX_BUY` the same thing as `max_rate` in the PDF?

   **Reference:** PDF p. 2, `max_rate`; [LOAD_GET](https://fde-challenge-candidate-handbook-production.up.railway.app/spec/load-get/) and [LOAD_BOOK](https://fde-challenge-candidate-handbook-production.up.railway.app/spec/load-book/).

   **A:** Pending Luke's clarification.

4. **Q:** Who is the demo actually directed to? Should I present it like I'm showing the solution to the brokerage's business and operations team, their IT team, or directly to you guys as technical reviewers? Basically, should I focus on showing the customer how it solves their problem, or walk you through how I built it?

   **Reference:** PDF p. 5, Deliverables items 1, 2, and 5.

   **A:** Pending Luke's clarification.

5. **Q:** When you said creativity, what exactly did you mean? Once the requirements are covered, should I focus on creative ways to solve the customer's actual problems, or are you also looking for extra ideas beyond the brief? For example, I had an idea of adding an animated face to the voice agent for a FaceTime-style experience. I could go quite far with something like that, but I'd like to understand whether you'd value that kind of extra feature or prefer that effort to go into making the solution more useful for the client and final end goal of helping the customer make more revenue. 

   **Reference:** Your comment about creativity during our conversation; PDF p. 1, Problem.

   **A:** Pending Luke's clarification.

6. **Q:** Is it fine if I deploy the Dockerized integration service on Fly.io, or should I use the same hosting platform as the TMS? The PDF says a cloud environment of the customer's choice, so just checking if you have a preference.

   **Reference:** PDF p. 4, Deployment.

   **A:** Pending Luke's clarification.

7. **Q:** FMCSA lists a carrier telephone number, but I haven't found any test carrier/contact records. For the demo, should I send the OTP to that registered number, or is it fine to map a carrier to my own phone/email and clearly mark it as demo data? Any specific test MC numbers you'd like me to use?

   **Reference:** [FMCSA API fields](https://mobile.fmcsa.dot.gov/QCDevsite/docs/apiElements), `telephone`.

   **A:** Pending Luke's clarification.
