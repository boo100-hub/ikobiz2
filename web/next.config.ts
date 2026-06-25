import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "images.unsplash.com" },
      { protocol: "https", hostname: "res.cloudinary.com" },
      { protocol: "https", hostname: "via.placeholder.com" },
      { protocol: "https", hostname: "placehold.co" },
    ],
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"}/:path*`,
      },
    ];
  },
  async redirects() {
    return [
      { source: "/auth/login", destination: "/login", permanent: true },
      { source: "/auth/register", destination: "/register", permanent: true },
      { source: "/checkout/:path*", destination: "/orders/:path*", permanent: true },
      { source: "/dashboard", destination: "/seller/dashboard", permanent: true },
      { source: "/dashboard/inventory", destination: "/seller/inventory", permanent: true },
      { source: "/dashboard/shop-settings", destination: "/seller/settings", permanent: true },
      { source: "/dashboard/onboarding", destination: "/seller/onboarding", permanent: true },
    ];
  },
};

export default nextConfig;
