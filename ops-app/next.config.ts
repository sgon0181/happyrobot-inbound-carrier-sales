import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Docker exposes Next dev on loopback; production origin checks remain unchanged.
  ...(process.env.NODE_ENV === "development" ? { allowedDevOrigins: ["127.0.0.1"] } : {}),
  turbopack: {
    root: process.cwd(),
  },
};

export default nextConfig;
