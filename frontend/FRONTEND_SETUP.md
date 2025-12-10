# DCMX Frontend Setup Guide

## Prerequisites

- Node.js 18+ and npm 9+
- TronLink browser extension
- Git

## Installation

### 1. Navigate to Frontend Directory

```bash
cd frontend
```

### 2. Install Dependencies

```bash
npm install
```

This will install all required packages including:
- Next.js 15
- React 19
- TypeScript
- Tailwind CSS
- TronWeb
- Zustand
- Axios
- And more...

### 3. Environment Configuration

Copy the example environment file:

```bash
cp .env.example .env.local
```

Edit `.env.local` and configure the following variables:

```env
# Backend API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# TRON Network Configuration
NEXT_PUBLIC_TRON_NETWORK=shasta  # shasta (testnet) or mainnet
NEXT_PUBLIC_TRON_RPC=https://api.shasta.trongrid.io

# Smart Contract Addresses (TRON)
NEXT_PUBLIC_NFT_CONTRACT=YOUR_NFT_CONTRACT_ADDRESS
NEXT_PUBLIC_TOKEN_CONTRACT=YOUR_TOKEN_CONTRACT_ADDRESS
NEXT_PUBLIC_GOVERNANCE_CONTRACT=YOUR_GOVERNANCE_CONTRACT_ADDRESS
NEXT_PUBLIC_REWARD_DISTRIBUTOR=YOUR_REWARD_DISTRIBUTOR_ADDRESS
NEXT_PUBLIC_ROYALTY_CONTRACT=YOUR_ROYALTY_CONTRACT_ADDRESS

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_EXPIRES_IN=7d

# Feature Flags
NEXT_PUBLIC_ENABLE_KYC=true
NEXT_PUBLIC_ENABLE_REWARDS=true
NEXT_PUBLIC_ENABLE_VOTING=true
```

### 4. Start Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## Development Commands

### Run Development Server
```bash
npm run dev
```

### Build for Production
```bash
npm run build
```

### Start Production Server
```bash
npm start
```

### Lint Code
```bash
npm run lint
```

### Type Check
```bash
npm run type-check
```

## Browser Extensions

### TronLink

1. Install TronLink extension from:
   - Chrome: https://chrome.google.com/webstore
   - Firefox: https://addons.mozilla.org

2. Create or import a wallet
3. Switch to Shasta Testnet (for development)
4. Get testnet TRX from faucet: https://www.trongrid.io/faucet

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js 15 App Router
│   │   ├── api/               # API routes (middleware)
│   │   │   ├── auth/         # Authentication endpoints
│   │   │   └── proxy/        # Backend proxy
│   │   ├── dashboard/        # Dashboard pages
│   │   ├── artist/           # Artist hub
│   │   ├── marketplace/      # NFT marketplace
│   │   ├── layout.tsx        # Root layout
│   │   └── page.tsx          # Landing page
│   ├── components/            # React components
│   │   ├── common/           # Reusable components
│   │   ├── layout/           # Layout components
│   │   ├── music/            # Music player components
│   │   ├── nft/              # NFT components
│   │   ├── wallet/           # Wallet components
│   │   ├── rewards/          # Rewards components
│   │   └── auth/             # Auth components
│   ├── context/               # React Context providers
│   │   ├── AuthContext.tsx
│   │   ├── WalletContext.tsx
│   │   └── ThemeContext.tsx
│   ├── hooks/                 # Custom React hooks
│   │   ├── useApi.ts
│   │   ├── useWallet.ts
│   │   ├── useMusicPlayer.ts
│   │   ├── useNFT.ts
│   │   └── useRewards.ts
│   ├── lib/                   # Library utilities
│   │   ├── api-client.ts     # Axios client
│   │   └── tronweb.ts        # TronWeb manager
│   ├── types/                 # TypeScript types
│   ├── utils/                 # Utility functions
│   └── styles/                # Global styles
├── public/                    # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── next.config.js
```

## Troubleshooting

### TronLink Not Detected

1. Make sure TronLink extension is installed and enabled
2. Refresh the page after installing TronLink
3. Check browser console for errors

### Cannot Connect to Backend API

1. Verify backend server is running on `http://localhost:8000`
2. Check `NEXT_PUBLIC_API_BASE_URL` in `.env.local`
3. Check CORS configuration in backend

### Build Errors

1. Delete `.next` directory and `node_modules`
2. Run `npm install` again
3. Run `npm run build`

### Type Errors

1. Run `npm run type-check` to see all type errors
2. Ensure all TypeScript packages are installed
3. Check `tsconfig.json` configuration

## Next Steps

- Read [FRONTEND_ARCHITECTURE.md](./FRONTEND_ARCHITECTURE.md) to understand the architecture
- Read [API_INTEGRATION.md](./API_INTEGRATION.md) for backend integration details
- Read [WALLET_INTEGRATION.md](./WALLET_INTEGRATION.md) for TronWeb integration

## Support

For issues or questions:
- Check existing documentation
- Review GitHub Issues: https://github.com/DCMX-Protocol/DCMX/issues
- Contact: support@dcmx.io
