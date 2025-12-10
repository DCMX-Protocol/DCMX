# DCMX API Integration Guide

## Overview

The DCMX frontend communicates with the FastAPI backend through a combination of direct API calls and Next.js API routes acting as middleware.

## API Client Configuration

### Base Configuration

Located in `src/lib/api-client.ts`:

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
```

### Axios Interceptors

#### Request Interceptor
- Automatically adds JWT token to Authorization header
- Configures request headers
- Logs requests in development

#### Response Interceptor
- Handles token refresh on 401 errors
- Global error handling
- Response transformation

## API Endpoints

### Authentication Endpoints

#### POST /api/auth/nonce
Generate a nonce for wallet signature authentication.

**Request:**
```json
{
  "walletAddress": "TRX..."
}
```

**Response:**
```json
{
  "success": true,
  "nonce": "abc123...",
  "message": "Sign this message to authenticate: abc123..."
}
```

#### POST /api/auth/login
Authenticate user with wallet signature.

**Request:**
```json
{
  "walletAddress": "TRX...",
  "signature": "0x..."
}
```

**Response:**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "user_id",
    "walletAddress": "TRX...",
    "username": "user123",
    "kycVerified": false,
    "kycLevel": 0,
    "balanceDCMX": 0,
    "balanceTRX": 0
  }
}
```

#### GET /api/auth/profile
Get current user profile.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "user": {
    "id": "user_id",
    "walletAddress": "TRX...",
    "username": "user123",
    ...
  }
}
```

#### POST /api/auth/refresh
Refresh JWT token.

**Headers:**
```
Authorization: Bearer <old_token>
```

**Response:**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "message": "Token refreshed successfully"
}
```

### Wallet Endpoints (via Proxy)

#### POST /api/proxy/api/v1/wallet/create
Create or register a wallet.

**Request:**
```json
{
  "wallet_address": "TRX...",
  "username": "user123"
}
```

**Response:**
```json
{
  "success": true,
  "wallet": {
    "id": "wallet_id",
    "address": "TRX...",
    "username": "user123",
    "balance_dcmx": 0.0,
    "kyc_verified": false,
    "kyc_level": 0
  }
}
```

#### GET /api/proxy/api/v1/wallet/{address}
Get wallet details.

**Response:**
```json
{
  "success": true,
  "wallet": {
    "address": "TRX...",
    "username": "user123",
    "balance_dcmx": 1000.5,
    "balance_trx": 50.25,
    "kyc_verified": true,
    "kyc_level": 2
  }
}
```

#### GET /api/proxy/api/v1/wallet/{address}/balance
Get wallet balance.

**Response:**
```json
{
  "success": true,
  "balance": {
    "dcmx": 1000.5,
    "trx": 50.25
  }
}
```

### NFT Endpoints (via Proxy)

#### POST /api/proxy/api/v1/nft/mint
Mint a new NFT.

**Request:**
```json
{
  "title": "My Song",
  "artist": "Artist Name",
  "description": "Song description",
  "track_hash": "QmXxx...",
  "edition_number": 1,
  "max_editions": 100,
  "royalty_bps": 1000,
  "price": 100.0
}
```

**Response:**
```json
{
  "success": true,
  "nft": {
    "id": "nft_id",
    "token_id": 123,
    "contract_address": "TRX...",
    "owner": "TRX...",
    "title": "My Song",
    "edition_number": 1,
    "max_editions": 100
  }
}
```

#### GET /api/proxy/api/v1/nft/list
List all NFTs.

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20)
- `sort`: Sort field (created_at, price, title)
- `order`: Sort order (asc, desc)

**Response:**
```json
{
  "success": true,
  "nfts": [...],
  "total": 100,
  "page": 1,
  "per_page": 20
}
```

#### GET /api/proxy/api/v1/nft/{token_id}
Get NFT details.

**Response:**
```json
{
  "success": true,
  "nft": {
    "id": "nft_id",
    "token_id": 123,
    "contract_address": "TRX...",
    "owner": "TRX...",
    "creator": "TRX...",
    "title": "My Song",
    "description": "...",
    "metadata": {...}
  }
}
```

### Rewards Endpoints (via Proxy)

#### GET /api/proxy/api/v1/rewards/{wallet_address}
Get user rewards.

**Response:**
```json
{
  "success": true,
  "rewards": [
    {
      "id": "reward_id",
      "user_id": "user_id",
      "reward_type": "energy",
      "amount": 10.5,
      "status": "claimable",
      "description": "Network participation reward",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total_claimable": 50.5
}
```

#### POST /api/proxy/api/v1/rewards/{reward_id}/claim
Claim a reward.

**Response:**
```json
{
  "success": true,
  "message": "Reward claimed successfully",
  "transaction_hash": "0x..."
}
```

### Track Endpoints (via Proxy)

#### POST /api/proxy/api/v1/track/upload
Upload a track.

**Request (multipart/form-data):**
- `file`: Audio file
- `title`: Track title
- `artist`: Artist name
- `album`: Album name (optional)
- `duration`: Duration in seconds
- `metadata`: Additional metadata (JSON)

**Response:**
```json
{
  "success": true,
  "track": {
    "id": "track_id",
    "content_hash": "QmXxx...",
    "title": "My Song",
    "artist": "Artist Name",
    "duration": 180,
    "audio_url": "https://..."
  }
}
```

## Using the API Client

### Basic Usage

```typescript
import { apiClient } from '@/lib/api-client';

// GET request
const data = await apiClient.get('/api/v1/wallet/TRX...');

// POST request
const result = await apiClient.post('/api/v1/nft/mint', {
  title: 'My Song',
  artist: 'Artist',
});

// With query parameters
const nfts = await apiClient.get('/api/v1/nft/list', {
  page: 1,
  per_page: 20,
});
```

### Using Custom Hooks

```typescript
import { useWalletApi, useNFTApi, useRewardsApi } from '@/hooks/useApi';

function MyComponent() {
  const walletApi = useWalletApi();
  const nftApi = useNFTApi();
  const rewardsApi = useRewardsApi();

  const handleMintNFT = async () => {
    try {
      const nft = await nftApi.mintNFT({
        title: 'My Song',
        artist: 'Artist',
        // ...
      });
      console.log('NFT minted:', nft);
    } catch (error) {
      console.error('Minting failed:', error);
    }
  };

  return (
    <div>
      {nftApi.isLoading ? 'Minting...' : (
        <button onClick={handleMintNFT}>Mint NFT</button>
      )}
    </div>
  );
}
```

## Error Handling

### API Client Errors

The API client automatically handles common errors:

```typescript
try {
  const data = await apiClient.get('/api/v1/wallet/invalid');
} catch (error) {
  // Error is already logged and toast notification shown
  // You can add additional error handling here
  if (error.response?.status === 404) {
    console.log('Wallet not found');
  }
}
```

### Custom Error Handling with Hooks

```typescript
const { execute, error, isLoading } = useApi({
  onSuccess: (data) => {
    console.log('Success:', data);
    toast.success('Operation successful');
  },
  onError: (error) => {
    console.error('Error:', error);
    toast.error('Operation failed');
  },
});

await execute(() => apiClient.post('/api/v1/nft/mint', data));
```

## Authentication Flow

### Initial Authentication

```typescript
import { useAuth } from '@/context/AuthContext';
import { useWallet } from '@/context/WalletContext';

function LoginFlow() {
  const { login } = useAuth();
  const { wallet, signMessage } = useWallet();

  const handleLogin = async () => {
    // 1. Get nonce
    const nonceResponse = await apiClient.post('/api/auth/nonce', {
      walletAddress: wallet.address,
    });

    // 2. Sign nonce
    const signature = await signMessage(nonceResponse.nonce);

    // 3. Login
    const success = await login(wallet.address, signature);

    if (success) {
      // Redirect to dashboard
      router.push('/dashboard');
    }
  };

  return <button onClick={handleLogin}>Login</button>;
}
```

### Authenticated Requests

All authenticated requests automatically include the JWT token:

```typescript
// Token is automatically added by axios interceptor
const profile = await apiClient.get('/api/auth/profile');
```

### Token Refresh

Token refresh is handled automatically on 401 errors:

```typescript
// If token expires, it will be refreshed automatically
// and the original request will be retried
const data = await apiClient.get('/api/v1/wallet/TRX...');
```

## Best Practices

1. **Use Custom Hooks**: Use `useApi`, `useWalletApi`, etc. for better error handling and loading states

2. **Handle Loading States**: Always show loading indicators during API calls

3. **Error Recovery**: Implement retry logic for transient failures

4. **Caching**: Cache frequently accessed data to reduce API calls

5. **Optimistic Updates**: Update UI immediately, rollback on error

6. **Rate Limiting**: Implement client-side rate limiting for heavy operations

7. **Request Cancellation**: Cancel pending requests on component unmount

## Troubleshooting

### CORS Issues
- Ensure backend allows `http://localhost:3000` origin
- Check CORS configuration in FastAPI

### 401 Unauthorized
- Check JWT token validity
- Verify token is being sent in headers
- Check token expiration

### Network Errors
- Verify backend is running
- Check `NEXT_PUBLIC_API_BASE_URL` configuration
- Check network connectivity

### Type Errors
- Ensure response types match TypeScript interfaces
- Update types when API changes
- Use type guards for runtime validation
