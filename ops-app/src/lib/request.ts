import { type NextRequest } from "next/server";

const loopback = new Set(["localhost", "127.0.0.1", "[::1]"]);

/** Pinned public App origin. Forwarding headers are attacker controlled at an untrusted ingress. */
export function getExternalOrigin(request: NextRequest): string {
  const configured = process.env.OPS_APP_ORIGIN?.trim();
  if (configured) {
    const url = new URL(configured);
    if (url.protocol === "https:" && url.origin === configured.replace(/\/$/, "")) return url.origin;
    throw new Error("OPS_APP_ORIGIN must be an HTTPS origin");
  }
  if (process.env.NODE_ENV !== "production" && loopback.has(request.nextUrl.hostname))
    return request.nextUrl.origin;
  throw new Error("OPS_APP_ORIGIN is required for this deployment");
}

/** Cookie-bearing unsafe requests need the browser's origin, including inside a platform iframe. */
export function allowedWriteOrigin(origin: string | null, app: string, extra: string | undefined) {
  if (!origin || origin === "null") return false;
  const allowed = [app, ...(extra ?? "").split(",").map(s => s.trim()).filter(Boolean)];
  return allowed.includes(origin);
}
