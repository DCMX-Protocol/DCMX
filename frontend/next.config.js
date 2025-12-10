/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  images: {
    domains: ['localhost', 'ipfs.io', 'gateway.pinata.cloud'],
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.ipfs.dweb.link',
      },
    ],
  },
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
    NEXT_PUBLIC_TRON_NETWORK: process.env.NEXT_PUBLIC_TRON_NETWORK,
    NEXT_PUBLIC_TRON_RPC: process.env.NEXT_PUBLIC_TRON_RPC,
    NEXT_PUBLIC_NFT_CONTRACT: process.env.NEXT_PUBLIC_NFT_CONTRACT,
    NEXT_PUBLIC_TOKEN_CONTRACT: process.env.NEXT_PUBLIC_TOKEN_CONTRACT,
    NEXT_PUBLIC_GOVERNANCE_CONTRACT: process.env.NEXT_PUBLIC_GOVERNANCE_CONTRACT,
    NEXT_PUBLIC_REWARD_DISTRIBUTOR: process.env.NEXT_PUBLIC_REWARD_DISTRIBUTOR,
    NEXT_PUBLIC_ROYALTY_CONTRACT: process.env.NEXT_PUBLIC_ROYALTY_CONTRACT,
  },
  webpack: (config) => {
    config.resolve.fallback = {
      ...config.resolve.fallback,
      fs: false,
      net: false,
      tls: false,
    };
    return config;
  },
};

module.exports = nextConfig;
