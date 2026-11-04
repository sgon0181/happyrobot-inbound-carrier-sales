import { NextRequest, NextResponse } from "next/server";
import { canManageBookings } from "@/lib/rep-access";
import { getVerifiedApiUser } from "@/lib/auth";
import { describeFailure, LOAD_ID_RE, postRepAction, type RepAction } from "@/lib/ops-service";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";
export const maxDuration = 60; // a confirm runs to the end: one send, then the save

const ACTIONS: ReadonlySet<string> = new Set(["confirm", "decline", "reconcile"]);

function reply(body: Record<string, unknown>, status: number) {
  return NextResponse.json(body, { status, headers: { "Cache-Control": "no-store" } });
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ loadId: string; action: string }> }
) {
  // Verify the session with the platform before anything else.
  const user = await getVerifiedApiUser();
  if (!user) return reply({ error: "Unauthorized" }, 401);

  if (!canManageBookings(user.sub)) return reply({ error: "Senior rep access required" }, 403);

  // JSON only, which also keeps plain cross-site form posts out.
  if (!request.headers.get("content-type")?.toLowerCase().startsWith("application/json")) {
    return reply({ error: "Unsupported content type" }, 415);
  }

  const { loadId, action } = await params;
  if (!LOAD_ID_RE.test(loadId) || !ACTIONS.has(action)) return reply({ error: "Not found" }, 404);

  // The booking version the rep saw (D-31). The service refuses if the row moved on.
  const body = (await request.json().catch(() => null)) as { version?: unknown } | null;
  const version = body?.version;
  if (typeof version !== "number" || !Number.isInteger(version) || version < 1) {
    return reply({ error: "Booking version required" }, 400);
  }

  // The rep comes only from the verified session, never from the request.
  const rep = user.sub;

  const result = await postRepAction(loadId, action as RepAction, version, rep);
  if (!result.ok) return reply({ error: `Action failed (${describeFailure(result)})` }, 502);
  return reply(result.reply, 200);
}
