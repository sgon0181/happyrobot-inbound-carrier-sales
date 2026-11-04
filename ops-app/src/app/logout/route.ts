import { getExternalOrigin } from "@/lib/request";
import { NextRequest, NextResponse } from "next/server";
import {
  APP_REFRESH_COOKIE_NAME,
  APP_TOKEN_COOKIE_NAME,
  appTokenCookieOptions,
  CROSS_SITE_COOKIES,
} from "@/lib/auth-cookies";

export async function GET(request: NextRequest) {
  const response = NextResponse.redirect(new URL("/login", getExternalOrigin(request)));
  response.cookies.set({
    name: APP_TOKEN_COOKIE_NAME,
    value: "",
    ...appTokenCookieOptions(0),
  });
  response.cookies.set({
    name: APP_REFRESH_COOKIE_NAME,
    value: "",
    ...appTokenCookieOptions(0),
  });
  if (CROSS_SITE_COOKIES) {
    // Cookies set before they were partitioned sit in a separate jar.
    for (const name of [APP_TOKEN_COOKIE_NAME, APP_REFRESH_COOKIE_NAME]) {
      response.headers.append(
        "set-cookie",
        `${name}=; Path=/; Max-Age=0; Secure; HttpOnly; SameSite=Lax`
      );
    }
  }
  return response;
}
