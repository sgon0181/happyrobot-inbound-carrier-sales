import { getTwinEnvironment } from "@/lib/env";

export const APP_TOKEN_COOKIE_NAME = "hr_token";
export const APP_REFRESH_COOKIE_NAME = "hr_refresh";

export const APP_ACCESS_TOKEN_MAX_AGE_SEC = 15 * 60;
export const APP_REFRESH_TOKEN_MAX_AGE_SEC = 3 * 24 * 60 * 60;

// Deployed apps are embedded cross-site in the platform, where Lax cookies are dropped.
export const CROSS_SITE_COOKIES = process.env.NODE_ENV === "production";

export function appTokenCookieOptions(maxAge: number) {
  return {
    httpOnly: true,
    secure: CROSS_SITE_COOKIES,
    sameSite: CROSS_SITE_COOKIES ? ("none" as const) : ("lax" as const),
    partitioned: CROSS_SITE_COOKIES,
    path: "/",
    maxAge,
  };
}

// Unverified decode for routing only; the platform and Twin verify the signature.
function readJwtPayload(
  token: string
): { exp?: unknown; twin_environment?: unknown } | null {
  const parts = token.split(".");
  if (parts.length < 2) return null;
  try {
    const payload: unknown = JSON.parse(
      atob(parts[1]!.replace(/-/g, "+").replace(/_/g, "/"))
    );
    return payload && typeof payload === "object" ? payload : null;
  } catch {
    return null;
  }
}

export function readJwtExpSeconds(token: string): number | null {
  const exp = readJwtPayload(token)?.exp;
  return typeof exp === "number" ? exp : null;
}

// Tokens without the claim predate Twin environments and are production.
export function matchesAppTwinEnvironment(token: string): boolean {
  const payload = readJwtPayload(token);
  if (!payload) return false;
  return (payload.twin_environment ?? "production") === getTwinEnvironment();
}

export function refreshCookieMaxAgeSec(refreshToken: string): number {
  const exp = readJwtExpSeconds(refreshToken);
  if (exp === null) return APP_REFRESH_TOKEN_MAX_AGE_SEC;
  return Math.max(exp - Math.floor(Date.now() / 1000), 0);
}
