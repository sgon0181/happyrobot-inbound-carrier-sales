# Plan: operations dashboard redesign

Status: **proposed**, for the owner's and Codex's review. Nothing here is built yet.

## Goal

Make the operations app feel like the TMS a brokerage's operations team already works in, so a rep or manager can use it without training. The reference is Uber Freight's TMS (the owner's screenshots, 2026-11-03): Uber's Base design language, which matches the wider pattern of broker systems such as McLeod PowerBroker and Turvo. Familiar, not a copy: no Uber branding, logo or proprietary font.

It must keep meeting the PDF: an internal app in HappyRobot Apps that surfaces "key operational signals and actions for the brokerage's operations manager, without accessing raw platform logs".

## What the reference does, and what we take

| Reference pattern | What we build |
|---|---|
| Dark icon rail on the left for sections | Rail with Overview, Bookings, Calls, Demand |
| Large bold page title, one primary action top right | Page title per section; search top right |
| "Boards": saved views with live counts | Boards per section: Awaiting rep, Sent and TMS pending, Needs review, Failed or released; Calls: Today, Booked, No match, Ineligible, Test calls |
| Filter chips above the table, with a "+" | Chips for status, pickup date, real or test calls; kept in the URL, so a view can be shared |
| Dense full-width tables: ID links, city and state apart, times with a timezone, sticky header | The same, with horizontal scroll inside the table only, never the page |
| Monochrome, colour only for status | Black, white and grays; status pills in four colours with a legend |
| Forms in labelled sections | The side panel's detail sections |

## What we can change, and what limits it

- **Ours:** the app is our Next.js 16 code with Tailwind 4 and the shadcn kit (Base UI). Layout, routes, components, colours and type are all ours. The kit already has a side panel (`sheet`), tables, badges and tooltips.
- **Fixed:** it stays in HappyRobot Apps with the template's sign-in, and reads only through the service with the ops key kept server-side (D-30).
- **Data:** the screen can only show what the service returns. Today a booking row stores the MC, rate and call, not the lane or pickup, so piece 1 adds them.

## Pieces

Each piece is one commit, reviewed by Codex before the next, per the project workflow.

### 1. Service: each reservation keeps its load's details

Today the rep sees a load ID and a rate, and cannot judge the deal without the lane and pickup.

- `selling.py`: `_fresh_terms` already reads the load just before reserving. It returns the load with its terms, and `negotiate` passes a summary to `reserve`. This touches `selling.py`, which was set aside for another session; **needs the owner's approval**.
- `bookings.py`: `new_booking` stores `load`: origin and destination city and state, pickup, delivery, equipment, miles, weight, commodity and the posted rate. **Never the ceiling** (`max_rate`), so a row read by any screen cannot carry it.
- `dashboard.py`: projects `load` on each booking, and the carrier name joined from the booking's call row.
- Rows reserved before this change, such as LD01080, show "not recorded" rather than a guess.
- Tests: the stored fields, the ceiling scan extended to booking rows, and the old-row case. Estimated +40 production lines.

### 2. App foundation: names, times, labels

- Title: set the App's name in HappyRobot settings to "Carrier Sales" (it is still "[CODEX LAB ONLY] Carrier Sales v2.4"), and default to it in `layout.tsx` when the setting is empty.
- `lib/format.ts`: one place for times in Central Time with "CT", money, and plain-language labels for every state and outcome ("Awaiting rep", "Sent, TMS pending", "Needs review", "No load matched", "Carrier not eligible", and so on). Raw codes stay visible only in the side panel's audit trail.
- Caveat to show in a tooltip: the TMS does not say which timezone pickup times are in; we assume UTC (docs/tms/README.md).

### 3. App shell: rail, pages and boards

- Routes `/` (Overview), `/bookings`, `/calls`, `/demand`, each a server page reading the one snapshot.
- The rail replaces the current sidebar; a boards panel per page lists saved views with counts.
- Filters as URL search parameters, applied on the server; chips show and clear them.
- Auto-refresh, the receipt recovery panels and the snapshot error stay outside every page's content, as now.

### 4. Tables

- Bookings: Load, Carrier, MC, Origin, Destination, Pickup CT, Equipment, Agreed rate, Posted rate, Status, Updated.
- Calls: Started CT, Carrier, MC, Code passed, Lane asked, Rounds, Outcome, Load and rate.
- Sticky header, row hover, underlined IDs that open the side panel, empty states that say what the view is for.

### 5. Side panel per load and per call

- Load: the lane and cargo, the carrier, agreed versus posted rate, the TMS status and reference, the timeline of events in plain language, and Confirm, Decline or Reconcile with today's safeguards (the version check and the confirm prompt).
- Call: the summary, verification steps, each offer and counter by round, the outcome, and its booking.

### 6. Overview

- A compact KPI strip: calls, code passed, reserved handoffs, the northstar, rep confirmed, TMS acknowledged and confirmed, unknown, time to first offer.
- The outcome breakdown and the funnel from call to booking.
- What needs attention now: reservations waiting, unknown sends, stuck sends.

### 7. Polish and check

- Loading skeletons, keyboard focus, readable at 1280px and on a laptop, no page-level horizontal scroll.
- Typecheck, build and the production dependency audit in `node:22`.
- A visual check in the app's browser after each piece is published, against the live snapshot. A local preview would need a fixture mode that skips sign-in; we do not add one, because a mistake there would expose the dashboard.

## Delivery

- Pieces 1 and 2 first: they fix what a rep needs most and what looks broken now.
- Then 3 to 6 as one design pass, reviewed screen by screen by the owner after each App publish.
- Publishing the App is done in HappyRobot by the owner or Codex, as Build 17 was.
- Estimate: about a day of work across the seven commits.

## Decisions for the owner

1. Approve the small `selling.py` change in piece 1.
2. Separate pages with a rail (recommended) or one long page as now.
3. Central Time for all times (recommended for a Chicago team) or UTC.
4. Show the posted rate next to the agreed rate to reps (recommended; the ceiling stays out either way).
5. Run this before the PDF compliance audit, after it, or alongside it.
