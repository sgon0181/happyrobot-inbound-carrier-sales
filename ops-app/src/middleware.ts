import { NextRequest, NextResponse } from "next/server";
import {
  APP_ACCESS_TOKEN_MAX_AGE_SEC,
  APP_REFRESH_COOKIE_NAME,
  APP_TOKEN_COOKIE_NAME,
  CROSS_SITE_COOKIES,
  appTokenCookieOptions,
  matchesAppTwinEnvironment,
  readJwtExpSeconds,
  refreshCookieMaxAgeSec,
} from "@/lib/auth-cookies";
import { allowedWriteOrigin, getExternalOrigin } from "@/lib/request";

const PUBLIC_PREFIXES = [
  "/login",
  "/logout",
  "/callback",
  "/api/auth/refresh",
];

const REFRESH_AHEAD_SEC = 120;
const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS"]);

// SameSite=None cookies ride along on cross-site form posts, which Lax blocked.
function isCrossSiteWrite(request: NextRequest): boolean {
  if (!CROSS_SITE_COOKIES || SAFE_METHODS.has(request.method)) return false;
  // Without the user's cookies a cross-site request can't act as them.
  if (
    !request.cookies.has(APP_TOKEN_COOKIE_NAME) &&
    !request.cookies.has(APP_REFRESH_COOKIE_NAME)
  ) {
    return false;
  }
  return !allowedWriteOrigin(request.headers.get("origin"), getExternalOrigin(request), process.env.ALLOWED_ORIGINS);
}

function deny(request: NextRequest): NextResponse {
  if (request.nextUrl.pathname.startsWith("/api/")) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  return NextResponse.redirect(new URL("/login", getExternalOrigin(request)));
}

async function mintRefreshedPair(
  refreshToken: string,
  platformUrl: string
): Promise<{ token: string; refreshToken: string } | null> {
  try {
    const minted = await fetch(
      `${platformUrl.replace(/\/$/, "")}/api/apps/auth/refresh`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${refreshToken}`,
        },
        cache: "no-store",
      }
    );
    if (!minted.ok) {
      return null;
    }

    const body = (await minted.json()) as {
      token?: string;
      refresh_token?: string;
    };
    if (
      !body.token ||
      !body.refresh_token ||
      !matchesAppTwinEnvironment(body.token)
    ) {
      return null;
    }
    return { token: body.token, refreshToken: body.refresh_token };
  } catch {
    return null;
  }
}

function nextWithAppCookies(
  request: NextRequest,
  pair: { token: string; refreshToken: string }
): NextResponse {
  const cookieMap = new Map(
    request.cookies.getAll().map((cookie) => [cookie.name, cookie.value])
  );
  cookieMap.set(APP_TOKEN_COOKIE_NAME, pair.token);
  cookieMap.set(APP_REFRESH_COOKIE_NAME, pair.refreshToken);

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set(
    "cookie",
    Array.from(cookieMap.entries())
      .map(([name, value]) => `${name}=${value}`)
      .join("; ")
  );

  const response = NextResponse.next({
    request: { headers: requestHeaders },
  });
  response.cookies.set({
    name: APP_TOKEN_COOKIE_NAME,
    value: pair.token,
    ...appTokenCookieOptions(APP_ACCESS_TOKEN_MAX_AGE_SEC),
  });
  response.cookies.set({
    name: APP_REFRESH_COOKIE_NAME,
    value: pair.refreshToken,
    ...appTokenCookieOptions(refreshCookieMaxAgeSec(pair.refreshToken)),
  });
  return response;
}

export async function middleware(request: NextRequest) {
  if (isCrossSiteWrite(request)) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }
  const { pathname } = request.nextUrl;
  if (
    PUBLIC_PREFIXES.some(
      (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`)
    )
  ) {
    return NextResponse.next();
  }

  const accessToken = request.cookies.get(APP_TOKEN_COOKIE_NAME)?.value;
  if (accessToken && !matchesAppTwinEnvironment(accessToken)) {
    return deny(request);
  }
  const exp = accessToken ? readJwtExpSeconds(accessToken) : null;
  const accessTtlSec = exp === null ? 0 : exp - Math.floor(Date.now() / 1000);
  if (accessTtlSec >= REFRESH_AHEAD_SEC) {
    return NextResponse.next();
  }

  const refreshToken = request.cookies.get(APP_REFRESH_COOKIE_NAME)?.value;
  const platformUrl = process.env.HR_PLATFORM_URL?.trim();
  if (refreshToken && platformUrl) {
    const pair = await mintRefreshedPair(refreshToken, platformUrl);
    if (pair) {
      return nextWithAppCookies(request, pair);
    }
  }

  return accessTtlSec > 0 ? NextResponse.next() : deny(request);
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
