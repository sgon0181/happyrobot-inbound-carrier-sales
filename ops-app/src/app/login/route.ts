import { NextRequest, NextResponse } from "next/server";
import { getPublicEnv, getServerEnv, getTwinEnvironment } from "@/lib/env";
import { getExternalOrigin } from "@/lib/request";

export async function GET(request: NextRequest) {
  const { orgId, appSlug } = getPublicEnv();
  const { platformUrl } = getServerEnv();

  if (!platformUrl || !orgId) {
    return NextResponse.json(
      { error: "HR_PLATFORM_URL or NEXT_PUBLIC_ORG_ID is missing." },
      { status: 500 }
    );
  }

  const origin = getExternalOrigin(request);
  const callbackUrl = new URL("/callback", origin);
  const loginUrl = new URL("/api/apps/auth", platformUrl);
  loginUrl.searchParams.set("redirect", callbackUrl.toString());
  loginUrl.searchParams.set("org_id", orgId);
  loginUrl.searchParams.set("twin_environment", getTwinEnvironment());
  if (appSlug) {
    loginUrl.searchParams.set("app_slug", appSlug);
  }

  return NextResponse.redirect(loginUrl);
}
