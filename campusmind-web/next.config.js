/** @type {import('next').NextConfig} */
const nextConfig = {
  // Environment variable for the API backend
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },
  // Allow all image domains (can restrict later)
  images: {
    remotePatterns: [],
  },
};

module.exports = nextConfig;

