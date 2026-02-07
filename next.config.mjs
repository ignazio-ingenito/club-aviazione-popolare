/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  eslint: {
    ignoreDuringBuilds: true,
  },
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "cap-cms.skunklabs.uk",
        pathname: "/assets/**",
      },
    ],
  },
}

export default nextConfig
