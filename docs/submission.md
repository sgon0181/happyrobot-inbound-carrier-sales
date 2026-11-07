# Submission

The five deliverables the brief asks for, and where each one is.

| Deliverable | Where |
| --- | --- |
| 1. Summary email to the prospect | [Below](#prospect-email) |
| 2. Build description for IT and business review | [build-description.md](build-description.md), exported as a PDF with the submission |
| 3. Code repository | [Private GitHub repository, main branch](https://github.com/sgon0181/happyrobot-inbound-carrier-sales/tree/main). Invite the assigned reviewer when the recruiter supplies their GitHub account. |
| 4. HappyRobot workflow link | [Workflow, live Version 20](https://platform.happyrobot.ai/fdesantiagogonzalezalvarez/workflows/6oaskq84xpfc/editor/zynb7wm66n9w) and its [web call](https://platform.happyrobot.ai/deployments/6oaskq84xpfc) |
| 5. Walkthrough video, about five minutes | Recorded by the owner from the [recording script](recording-script.md); link added at submission |

## Prospect email

Subject: A carrier desk that qualifies calls and keeps your team in control

Hi team,

We built a working carrier sales desk around the problems you described: missed calls at peak times, inconsistent negotiation and agreements that are hard to trace.

A carrier can call at any time. The AI agent identifies itself, checks the carrier's FMCSA authority, verifies an emailed code, finds a matching load and negotiates within your pricing limits. Every agreement becomes a reservation that a senior rep reviews, with the call, shipment and price history in one place, before a booking is sent to your TMS.

Your operations team sees how many verified calls end in a reservation and where the others stop: failed verification, no suitable freight or no agreement on price. Funnel stages and exception groups open supporting calls.

The build is tested against scripted, edge-case and adversarial conversations, and its pricing limits, verification and failure handling have automated tests. For this demonstration the code goes to a test inbox; a rollout would use your enrolled carrier contacts and named reps.

As a next step, I suggest a supervised shift: agree the pricing thresholds and contact list with your carrier sales team, then compare time to first offer, verified calls reaching a reservation and unresolved requests against a normal shift.

Try it here:

- Web call: https://platform.happyrobot.ai/deployments/6oaskq84xpfc
- Operations desk: https://carrier-sales-proposal-sg.happyrobot.dev/

Best,
Santiago

## Before submitting

1. Record the human call and walkthrough on the live workflow, following the [recording script](recording-script.md).
2. Submit the private GitHub repository link above. Check that `main` contains the reviewed commit and its GitHub Actions checks pass. Invite the assigned reviewer when their account is supplied.
3. Export the build description PDF from the same commit. This uses pandoc and Google Chrome; links to repository files become plain text, and web links stay clickable:

   ```bash
   mkdir -p ../submission-release
   sha=$(git rev-parse --short HEAD)
   git show HEAD:docs/build-description.md \
     | sed -E 's/\[([^]]+)\]\([^)h][^)]*\)/\1/g' \
     | pandoc --from gfm --to html5 --standalone \
         --metadata pagetitle="Carrier Sales: build description" -o /tmp/build-description.html
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --no-pdf-header-footer \
     --print-to-pdf="../submission-release/carrier-sales-build-description-$sha.pdf" /tmp/build-description.html
   ```

4. Submit the GitHub link, PDF and video link through the portal. The walkthrough video is pending until the owner records it. Keep the service running until the review is done.
