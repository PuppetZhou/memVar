import type { NextConfig } from "next";

const apiOrigin = (process.env.MEMVAR_API_INTERNAL_ORIGIN ?? "http://127.0.0.1:8000").replace(/\/$/, "");
const configuredDistDir = process.env.MEMVAR_NEXT_DIST_DIR?.trim();

const nextConfig: NextConfig = {
  // Keep the long-running local preview isolated from `next build`. Both
  // commands otherwise write `.next`, which can invalidate client chunks and
  // make Search -> protein navigation stall until the preview is restarted.
  distDir: configuredDistDir || (process.env.NODE_ENV === "development" ? ".next-dev" : ".next"),
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${apiOrigin}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
