/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  images: {
    remotePatterns: [
      {
        protocol: "http",
        hostname: "localhost",
        port: "8055",
        pathname: "/assets/**",
      },
      {
        protocol: "https",
        hostname: "cms.clubaviazionepopolare.org",
        pathname: "/assets/**",
      },
    ],
  },
}

export default nextConfig
