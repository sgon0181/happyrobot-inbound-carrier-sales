import { NextRequest, NextResponse } from "next/server";
import { getVerifiedApiUser } from "@/lib/auth";
import {
  allowedActions,
  BOOKING_ID_RE,
  describeFailure,
  getSnapshot,
  postRepAction,
  type RepAction,
} from "@/lib/ops-service";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const ACTIONS: ReadonlySet<string> = new Set(["confirm", "decline", "reconcile"]);

function reply(body: Record<string, unknown>, status: number) {
  return NextResponse.json(body, { status, headers: { "Cache-Control": "no-store" } });
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ bookingId: string; action: string }> }
) {
  // Verify the session with the platform before anything else.
  const user = await getVerifiedApiUser();
  if (!user) return reply({ error: "Unauthorized" }, 401);

  // JSON only, which also keeps plain cross-site form posts out.
  if (!request.headers.get("content-type")?.toLowerCase().startsWith("application/json")) {
    return reply({ error: "Unsupported content type" }, 415);
  }

  const { bookingId, action } = await params;
  if (!BOOKING_ID_RE.test(bookingId) || !ACTIONS.has(action)) {
    return reply({ error: "Not found" }, 404);
  }

  // The actor comes only from the verified session, never from the request.
  const actor = (user.email || user.sub || "").trim();
  if (!actor) return reply({ error: "Unauthorized" }, 401);

  // Re-check the offered actions against a fresh snapshot so Confirm can never
  // be sent for UNKNOWN or non-awaiting rows. The service remains authoritative.
  const snap = await getSnapshot();
  if (!snap.ok) return reply({ error: `Queue unavailable (${describeFailure(snap)})` }, 502);
  const row = snap.snapshot.queue.find((r) => r.id === bookingId);
  if (!row) return reply({ error: "Not found" }, 404);
  if (!allowedActions(row).includes(action as RepAction)) {
    return reply({ error: "Action not available for this booking" }, 409);
  }

  const result = await postRepAction(bookingId, action as RepAction, actor);
  if (!result.ok) return reply({ error: `Action failed (${describeFailure(result)})` }, 502);
  return reply({ ok: true }, 200);
}
