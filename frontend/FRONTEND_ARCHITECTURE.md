# DCMX Frontend Architecture

## Overview

The DCMX frontend is built with Next.js 15, React 19, and TypeScript, following modern web development best practices with a focus on performance, type safety, and user experience.

## Technology Stack

### Core Framework
- **Next.js 15**: App Router with Server Components
- **React 19**: Latest features including Server Components
- **TypeScript 5.3+**: Full type safety across the application

### Styling
- **Tailwind CSS**: Utility-first CSS framework
- **Dark Mode**: Full dark theme support with system preference detection
- **Responsive Design**: Mobile-first approach

### State Management
- **React Context**: Global state (Auth, Wallet, Theme)
- **Zustand**: Complex state management (optional)
- **React Hooks**: Local component state

### Blockchain Integration
- **TronWeb**: TRON blockchain interaction
- **TronLink**: Wallet connection and authentication

### API Communication
- **Axios**: HTTP client with interceptors
- **Next.js API Routes**: Middleware layer for authentication and proxying

## Architecture Layers

### 1. Presentation Layer (Pages & Components)

#### Pages (`src/app/`)
- **Landing Page** (`/`): Hero, features, CTA
- **Dashboard** (`/dashboard`): User overview, stats, quick actions
- **Library** (`/dashboard/library`): Music collection
- **Rewards** (`/dashboard/rewards`): Rewards center
- **Settings** (`/dashboard/settings`): User preferences
- **Artist Hub** (`/artist`): NFT creation and management
- **Marketplace** (`/marketplace`): NFT browsing and trading

#### Components (`src/components/`)

**Common Components**
- `Button`: Reusable button with variants
- `Card`: Content container with variants
- `Modal`: Overlay dialog
- `LoadingSpinner`: Loading indicator
- `Toast`: Notification system

**Layout Components**
- `Navigation`: Top navigation bar
- `Footer`: Footer with links
- `Sidebar`: Collapsible sidebar (when needed)

**Feature Components**
- Music: Player, TrackCard, Playlist, WaveformVisualizer
- NFT: NFTCard, MintDialog, RoyaltyInfo, EditionViewer
- Wallet: WalletConnect, BalanceDisplay, TransactionHistory
- Rewards: RewardCard, ClaimDialog, RewardChart
- Auth: LoginModal, SignupForm, KYCForm

### 2. State Management Layer

#### React Context Providers

**AuthContext** (`src/context/AuthContext.tsx`)
- User authentication state
- Login/logout functions
- JWT token management
- Profile refresh

**WalletContext** (`src/context/WalletContext.tsx`)
- Wallet connection state
- TronLink integration
- Balance tracking
- Message signing

**ThemeContext** (`src/context/ThemeContext.tsx`)
- Dark/light mode toggle
- Theme persistence
- System preference detection

### 3. Business Logic Layer

#### Custom Hooks (`src/hooks/`)

**useApi**
- Generic API request hook
- Error handling
- Loading states
- Specific API hooks (useWalletApi, useNFTApi, useRewardsApi)

**useMusicPlayer**
- Audio playback control
- Playlist management
- Volume, seek, repeat, shuffle
- Track navigation

**useNFT**
- NFT minting
- NFT purchasing
- NFT transfers
- Metadata fetching

**useRewards**
- Rewards loading
- Reward claiming
- Type-based filtering
- Total calculations

### 4. Data Access Layer

#### API Client (`src/lib/api-client.ts`)
- Axios instance configuration
- Request/response interceptors
- JWT token injection
- Automatic token refresh
- Error handling

#### TronWeb Manager (`src/lib/tronweb.ts`)
- TronLink detection
- Wallet initialization
- Contract interaction
- Transaction signing
- Event listening

### 5. Middleware Layer (Next.js API Routes)

#### Authentication Routes (`src/app/api/auth/`)

**POST /api/auth/nonce**
- Generate nonce for wallet signature
- Nonce storage (in-memory or Redis)
- 5-minute expiration

**POST /api/auth/login**
- Verify wallet signature
- Create JWT token
- Forward to backend API
- Return user profile

**POST /api/auth/logout**
- Clear authentication
- Token invalidation (optional)

**GET /api/auth/profile**
- Verify JWT token
- Fetch user profile from backend
- Return user data

**POST /api/auth/refresh**
- Verify old JWT token
- Generate new JWT token
- Extend session

#### Proxy Routes (`src/app/api/proxy/[...path]/`)
- Forward requests to backend API
- Add authentication headers
- Handle CORS
- Error transformation

## Data Flow

### Authentication Flow

```
User → Connect Wallet → TronLink → Sign Message
     ↓
Frontend → POST /api/auth/nonce → Generate Nonce
     ↓
TronWeb → Sign Nonce
     ↓
Frontend → POST /api/auth/login → Verify Signature
     ↓
Backend API → Create/Get User → Return User Data
     ↓
Frontend → Store JWT → Update AuthContext → Redirect to Dashboard
```

### API Request Flow

```
Component → useApi Hook → API Client
     ↓
Axios Interceptor → Add JWT Token
     ↓
Next.js API Route (Middleware) → Verify JWT → Add Headers
     ↓
Backend API → Process Request → Return Response
     ↓
API Client → Parse Response → Update Component State
```

### NFT Minting Flow

```
Artist → Upload Music → Fill Metadata → Preview
     ↓
Frontend → Validate Data → Upload to IPFS/Storage
     ↓
useNFT Hook → Call Smart Contract
     ↓
TronWeb → Sign Transaction → Submit to TRON
     ↓
Smart Contract → Mint NFT → Emit Event
     ↓
Frontend → Wait for Confirmation → Update Backend DB
     ↓
Backend API → Store NFT Metadata → Update Artist Profile
     ↓
Frontend → Show Success → Refresh NFT List
```

## Security Considerations

### Authentication
- JWT tokens stored in localStorage (client-side)
- Token refresh on expiration
- Signature verification for wallet auth
- No sensitive data in tokens

### API Communication
- HTTPS in production
- CORS properly configured
- JWT tokens in Authorization header
- Request/response validation

### Smart Contract Interaction
- Transaction confirmation before state updates
- Gas limit estimation
- User approval for all transactions
- Error handling for failed transactions

### Data Privacy
- No sensitive data in browser storage
- KYC data only sent to backend
- Wallet addresses only (no private keys)
- User consent for data collection

## Performance Optimizations

### Next.js Features
- Server Components for static content
- Image optimization with `next/image`
- Route prefetching
- Code splitting

### React Optimizations
- Memoization with `useMemo` and `useCallback`
- Lazy loading for heavy components
- Virtual scrolling for large lists
- Debouncing for search inputs

### Caching
- API response caching
- TronWeb contract instance caching
- Static asset caching
- Service Worker (PWA ready)

## Responsive Design

### Breakpoints (Tailwind CSS)
- `sm`: 640px (mobile landscape)
- `md`: 768px (tablet)
- `lg`: 1024px (desktop)
- `xl`: 1280px (large desktop)
- `2xl`: 1536px (extra large)

### Mobile-First Approach
- Base styles for mobile
- Progressive enhancement for larger screens
- Touch-friendly UI elements
- Optimized navigation for mobile

## Error Handling

### Levels
1. **Component Level**: Try-catch in async functions
2. **Hook Level**: Error state in custom hooks
3. **API Level**: Interceptors in axios client
4. **Global Level**: Error boundaries for React

### User Feedback
- Toast notifications for errors
- Inline validation messages
- Loading states during operations
- Retry mechanisms for failed requests

## Testing Strategy (Future)

### Unit Tests
- Utility functions
- Custom hooks
- API client

### Integration Tests
- Component interactions
- API endpoints
- Context providers

### E2E Tests
- Critical user flows
- Wallet connection
- NFT minting
- Reward claiming

## Deployment

### Build Process
```bash
npm run build
```

### Environment-Specific Configs
- Development: `.env.local`
- Staging: `.env.staging`
- Production: `.env.production`

### Hosting Options
- Vercel (recommended for Next.js)
- Netlify
- AWS Amplify
- Docker + Kubernetes

## Future Enhancements

### Features
- Real-time updates (WebSockets)
- Social features (likes, comments, shares)
- Advanced music player (equalizer, effects)
- Playlist sharing
- Artist collaboration

### Technical
- Progressive Web App (PWA)
- Offline support
- Push notifications
- Analytics integration
- A/B testing framework

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev)
- [TronWeb Documentation](https://tronweb.network)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
