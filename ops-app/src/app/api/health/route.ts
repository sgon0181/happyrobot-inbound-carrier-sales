import { NextResponse } from "next/server";
import { getVerifiedApiUser } from "@/lib/auth";

export const dynamic = "force-dynamic";

// Protected: only a verified signed-in user gets a response, and it carries
// no configuration details.
export async function GET() {
  const user = await getVerifiedApiUser();
  if (!user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401, headers: { "Cache-Control": "no-store" } });
  }
  return NextResponse.json({ ok: true }, { headers: { "Cache-Control": "no-store" } });
}
