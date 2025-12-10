# DCMX Frontend Application

## Overview

This is the frontend application for DCMX (Decentralized Music Network), built with Next.js 15, React 19, and TypeScript. It provides a modern, responsive interface for interacting with the DCMX platform, including music NFT marketplace, artist tools, and rewards system.

## Features

- 🎵 **Music NFT Marketplace**: Browse, buy, and sell music NFTs
- 🎨 **Artist Hub**: Upload music, mint NFTs, and manage royalties
- 💰 **Rewards System**: Earn DCMX tokens through network participation
- 👛 **Wallet Integration**: Connect with TronLink for blockchain interactions
- 🌙 **Dark Mode**: Full dark theme support
- 📱 **Responsive Design**: Optimized for mobile, tablet, and desktop

## Tech Stack

- **Framework**: Next.js 15 with App Router
- **UI Library**: React 19
- **Language**: TypeScript 5.3+
- **Styling**: Tailwind CSS
- **State Management**: React Context + Zustand
- **Blockchain**: TronWeb for TRON integration
- **API Client**: Axios with interceptors
- **Forms**: React Hook Form + Zod validation
- **Notifications**: React Hot Toast
- **Charts**: Recharts
- **Audio**: WaveSurfer.js

## Quick Start

### Prerequisites

- Node.js 18+ and npm 9+
- TronLink browser extension
- DCMX backend running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local

# Edit .env.local with your configuration
```

### Development

```bash
# Start development server
npm run dev

# Open http://localhost:3000
```

### Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js pages
│   │   ├── api/               # API routes (middleware)
│   │   ├── dashboard/        # Dashboard pages
│   │   ├── artist/           # Artist hub
│   │   ├── marketplace/      # Marketplace
│   │   └── ...
│   ├── components/            # React components
│   │   ├── common/           # Reusable components
│   │   ├── layout/           # Layout components
│   │   ├── music/            # Music components
│   │   ├── nft/              # NFT components
│   │   ├── wallet/           # Wallet components
│   │   └── rewards/          # Rewards components
│   ├── context/               # React Context
│   ├── hooks/                 # Custom hooks
│   ├── lib/                   # Libraries
│   ├── types/                 # TypeScript types
│   ├── utils/                 # Utilities
│   └── styles/                # Global styles
├── public/                    # Static assets
└── ...config files
```

## Documentation

- [**FRONTEND_SETUP.md**](./FRONTEND_SETUP.md) - Installation and setup guide
- [**FRONTEND_ARCHITECTURE.md**](./FRONTEND_ARCHITECTURE.md) - Architecture overview
- [**API_INTEGRATION.md**](./API_INTEGRATION.md) - Backend API integration
- [**WALLET_INTEGRATION.md**](./WALLET_INTEGRATION.md) - TronWeb wallet integration

## Key Pages

### Landing Page (`/`)
- Hero section with platform overview
- Feature highlights
- Platform statistics
- Call-to-action buttons

### Dashboard (`/dashboard`)
- User overview and statistics
- Quick actions
- Recent activity
- Music library preview

### Marketplace (`/marketplace`)
- Browse music NFTs
- Search and filters
- NFT details and purchasing

### Artist Hub (`/artist`)
- Upload music tracks
- Mint NFTs with metadata
- Set royalty percentages
- Track sales and earnings

### Rewards (`/dashboard/rewards`)
- View available rewards
- Claim rewards
- Rewards history
- Earnings breakdown

## Authentication Flow

1. User clicks "Connect Wallet"
2. TronLink prompts for connection
3. Frontend requests nonce from backend
4. User signs nonce with TronLink
5. Frontend sends signature to backend
6. Backend verifies and issues JWT
7. User is authenticated

## Smart Contract Integration

The frontend integrates with 5 TRON smart contracts:

1. **NFT Contract**: ERC-721 for music NFTs
2. **Token Contract**: ERC-20 for DCMX tokens
3. **Governance Contract**: DAO voting
4. **Reward Distributor**: Token rewards
5. **Royalty Contract**: Royalty management

## Environment Variables

Required in `.env.local`:

```env
# Backend API
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# TRON Network
NEXT_PUBLIC_TRON_NETWORK=shasta
NEXT_PUBLIC_TRON_RPC=https://api.shasta.trongrid.io

# Smart Contracts
NEXT_PUBLIC_NFT_CONTRACT=TRX...
NEXT_PUBLIC_TOKEN_CONTRACT=TRX...
NEXT_PUBLIC_GOVERNANCE_CONTRACT=TRX...
NEXT_PUBLIC_REWARD_DISTRIBUTOR=TRX...
NEXT_PUBLIC_ROYALTY_CONTRACT=TRX...

# JWT Secret (for API routes)
JWT_SECRET=your-secret-key

# Feature Flags
NEXT_PUBLIC_ENABLE_KYC=true
NEXT_PUBLIC_ENABLE_REWARDS=true
NEXT_PUBLIC_ENABLE_VOTING=true
```

## Development Commands

```bash
# Development server
npm run dev

# Production build
npm run build

# Start production server
npm start

# Lint code
npm run lint

# Type check
npm run type-check

# Format code
npm run format
```

## Testing (Future)

```bash
# Unit tests
npm run test

# E2E tests
npm run test:e2e

# Test coverage
npm run test:coverage
```

## Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel
```

### Docker

```bash
# Build image
docker build -t dcmx-frontend .

# Run container
docker run -p 3000:3000 dcmx-frontend
```

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

MIT License - see [LICENSE](../LICENSE) for details

## Support

- Documentation: See `/docs` folder
- Issues: https://github.com/DCMX-Protocol/DCMX/issues
- Email: support@dcmx.io

## Acknowledgments

- Next.js team for the amazing framework
- TRON Foundation for blockchain infrastructure
- Open source community for various libraries

---

Built with ❤️ by the DCMX team
