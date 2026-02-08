/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "cap.skunklabs.uk",
        pathname: "/assets/**",
      },
      {
        protocol: "https",
        hostname: "cap-cms.skunklabs.uk",
        pathname: "/assets/**",
      },
    ],
  },
}

export default nextConfig
