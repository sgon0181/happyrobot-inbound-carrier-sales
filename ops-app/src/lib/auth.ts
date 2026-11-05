import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import {
  APP_ACCESS_TOKEN_MAX_AGE_SEC,
  APP_REFRESH_COOKIE_NAME,
  APP_TOKEN_COOKIE_NAME,
  appTokenCookieOptions,
  matchesAppTwinEnvironment,
  refreshCookieMaxAgeSec,
} from "@/lib/auth-cookies";
import { getPublicEnv, getServerEnv } from "@/lib/env";

export {
  APP_ACCESS_TOKEN_MAX_AGE_SEC,
  APP_REFRESH_COOKIE_NAME,
  APP_REFRESH_TOKEN_MAX_AGE_SEC,
  APP_TOKEN_COOKIE_NAME,
  appTokenCookieOptions,
} from "@/lib/auth-cookies";

export type AppUser = {
  sub: string;
  email: string;
  first_name?: string;
  last_name?: string;
  image_url?: string;
  role?: string;
  aud?: string;
};

/** Normalize only a platform-verified identity. Token claims are never authorization. */
export function parseAppUser(value: unknown): AppUser | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const body = value as Record<string, unknown>;
  const subject = (v: unknown): v is string =>
    typeof v === "string" && /^[A-Za-z0-9][A-Za-z0-9:_-]{0,127}$/.test(v);
  if (("id" in body && !subject(body.id)) || ("sub" in body && !subject(body.sub))) return null;
  if (body.id !== undefined && body.sub !== undefined && body.id !== body.sub) return null;
  const id = body.id ?? body.sub;
  if (!subject(id)) return null;
  const text = (key: string, max: number): string | undefined =>
    typeof body[key] === "string" ? body[key].slice(0, max) : undefined;
  return { sub: id, email: text("email", 254) ?? "", first_name: text("first_name", 100),
    last_name: text("last_name", 100), image_url: text("image_url", 2000) };
}

export type AppTokenPair = {
  token: string;
  refreshToken: string;
};

export async function getAppToken(): Promise<string | null> {
  const cookieStore = await cookies();
  const token = cookieStore.get(APP_TOKEN_COOKIE_NAME)?.value;
  return token && matchesAppTwinEnvironment(token) ? token : null;
}

export async function getAppRefreshToken(): Promise<string | null> {
  const cookieStore = await cookies();
  return cookieStore.get(APP_REFRESH_COOKIE_NAME)?.value ?? null;
}

export async function setAppTokenCookies(pair: AppTokenPair): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.set(APP_TOKEN_COOKIE_NAME, pair.token, {
    ...appTokenCookieOptions(APP_ACCESS_TOKEN_MAX_AGE_SEC),
  });
  cookieStore.set(APP_REFRESH_COOKIE_NAME, pair.refreshToken, {
    ...appTokenCookieOptions(refreshCookieMaxAgeSec(pair.refreshToken)),
  });
}

/** Exchange hr_refresh at the platform broker. Does not touch cookies. */
export async function refreshAppTokenPair(
  refreshToken: string
): Promise<AppTokenPair | null> {
  const { platformUrl } = getServerEnv();
  if (!platformUrl) return null;

  const response = await fetch(`${platformUrl}/api/apps/auth/refresh`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${refreshToken}`,
    },
    cache: "no-store",
  });
  if (!response.ok) return null;

  const body = (await response.json()) as {
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
}

/**
 * Ensure a usable access token for this request: refresh via broker when
 * access is missing/rejected and a refresh cookie is present.
 */
export async function ensureAppToken(): Promise<string | null> {
  const existing = await getAppToken();
  if (existing) {
    const user = await getCurrentUser(existing);
    if (user) return existing;
  }

  const refreshToken = await getAppRefreshToken();
  if (!refreshToken) return null;

  const pair = await refreshAppTokenPair(refreshToken);
  if (!pair) return null;

  try {
    await setAppTokenCookies(pair);
  } catch {
    // Server Components cannot Set-Cookie; middleware covers that path and
    // still returns the fresh access token for this request.
  }
  return pair.token;
}

export async function getCurrentUser(
  token?: string | null
): Promise<AppUser | null> {
  const resolvedToken = token ?? (await getAppToken());
  const { platformUrl } = getServerEnv();
  const { appSlug } = getPublicEnv();
  if (
    !resolvedToken ||
    !platformUrl ||
    !matchesAppTwinEnvironment(resolvedToken)
  ) {
    return null;
  }

  const response = await fetch(`${platformUrl}/api/apps/me`, {
    headers: {
      Authorization: `Bearer ${resolvedToken}`,
      ...(appSlug ? { "X-App-Slug": appSlug } : {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    return null;
  }

  return parseAppUser(await response.json().catch(() => null));
}

/** Route-handler variant of requireAppUser: returns null instead of redirecting. */
export async function getVerifiedApiUser(): Promise<AppUser | null> {
  const existing = await getAppToken();
  if (existing) {
    const user = await getCurrentUser(existing);
    if (user) return user;
  }
  const token = await ensureAppToken();
  return token ? getCurrentUser(token) : null;
}

export async function requireAppUser(): Promise<{
  token: string;
  user: AppUser;
}> {
  const existing = await getAppToken();
  if (existing) {
    const user = await getCurrentUser(existing);
    if (user) return { token: existing, user };
  }

  const token = await ensureAppToken();
  if (!token) {
    redirect("/login");
  }

  const user = await getCurrentUser(token);
  if (!user) {
    redirect("/login");
  }

  return { token, user };
}
