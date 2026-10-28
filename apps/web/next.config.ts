import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  poweredByHeader: false,
  distDir: process.env.NEXT_DIST_DIR || ".next",
  turbopack: { root: process.cwd() },
  outputFileTracingRoot: process.cwd(),
};

export default nextConfig;
