export function getPublicEnv() {
  return {
    orgId: process.env.NEXT_PUBLIC_ORG_ID?.trim() ?? "",
    appSlug: process.env.NEXT_PUBLIC_APP_SLUG?.trim() ?? "",
    appName: process.env.NEXT_PUBLIC_APP_NAME?.trim() ?? "",
    appDescription: process.env.NEXT_PUBLIC_APP_DESCRIPTION?.trim() ?? "",
  };
}

export type TwinEnvironment = "production" | "staging";

// Used only to match the sign-in token's environment claim. This app does not
// read or write Twin data.
export function getTwinEnvironment(): TwinEnvironment {
  const environment =
    process.env.HR_TWIN_ENVIRONMENT?.trim() ||
    (process.env.VERCEL_ENV === "preview" ? "staging" : "production");
  if (environment !== "production" && environment !== "staging") {
    throw new Error("HR_TWIN_ENVIRONMENT must be production or staging.");
  }
  return environment;
}

export function getServerEnv() {
  return {
    platformUrl: process.env.HR_PLATFORM_URL?.trim() ?? "",
  };
}


/** Server-only. OPS_API_KEY must never be NEXT_PUBLIC, logged or returned. */
export function getOpsEnv() {
  const serviceUrl = (process.env.OPS_SERVICE_URL?.trim() ?? "").replace(/\/$/, "");
  return {
    opsApiKey: process.env.OPS_API_KEY?.trim() ?? "",
    serviceUrl: serviceUrl.startsWith("https://") ? serviceUrl : "",
  };
}
