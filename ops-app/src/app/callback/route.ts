import { getExternalOrigin } from "@/lib/request";
import { NextRequest, NextResponse } from "next/server";
import {
  APP_ACCESS_TOKEN_MAX_AGE_SEC,
  APP_REFRESH_COOKIE_NAME,
  APP_TOKEN_COOKIE_NAME,
  appTokenCookieOptions,
  matchesAppTwinEnvironment,
  refreshCookieMaxAgeSec,
} from "@/lib/auth-cookies";

export async function GET(request: NextRequest) {
  const token = request.nextUrl.searchParams.get("token");
  const refresh = request.nextUrl.searchParams.get("refresh");
  if (!token) {
    const destination = new URL("/login?error=missing_token", getExternalOrigin(request));
    return NextResponse.redirect(destination);
  }
  // The platform iframe may hand over a token for the other environment.
  if (!matchesAppTwinEnvironment(token)) {
    return NextResponse.redirect(new URL("/login", getExternalOrigin(request)));
  }

  const response = NextResponse.redirect(new URL("/", getExternalOrigin(request)));
  response.cookies.set({
    name: APP_TOKEN_COOKIE_NAME,
    value: token,
    ...appTokenCookieOptions(APP_ACCESS_TOKEN_MAX_AGE_SEC),
  });
  if (refresh) {
    response.cookies.set({
      name: APP_REFRESH_COOKIE_NAME,
      value: refresh,
      ...appTokenCookieOptions(refreshCookieMaxAgeSec(refresh)),
    });
  }

  return response;
}
