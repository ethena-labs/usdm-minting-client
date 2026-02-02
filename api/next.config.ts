import type { NextConfig } from 'next'

/**
 * Next.js Configuration for USDm Minting API Documentation
 */
const nextConfig: NextConfig = {
  // API-only project, standalone output for Docker/Vercel
  output: 'standalone',
}

export default nextConfig

