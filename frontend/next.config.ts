// frontend/next.config.ts

import type { NextConfig } from "next";

module.exports = {
  allowedDevOrigins: ['192.168.0.254', '201.47.155.233'],
}

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: true,
};

export default nextConfig;
