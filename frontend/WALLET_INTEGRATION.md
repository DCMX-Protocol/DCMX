# DCMX Wallet Integration Guide

## Overview

DCMX uses TronLink wallet for blockchain interactions. This guide covers wallet connection, transaction signing, and smart contract interactions.

## TronLink Setup

### Installation

1. Install TronLink browser extension:
   - Chrome: https://chrome.google.com/webstore
   - Firefox: https://addons.mozilla.org

2. Create a new wallet or import existing
3. Switch to Shasta Testnet for development
4. Get testnet TRX from faucet: https://www.trongrid.io/faucet

### Configuration

In `.env.local`:

```env
NEXT_PUBLIC_TRON_NETWORK=shasta  # or mainnet
NEXT_PUBLIC_TRON_RPC=https://api.shasta.trongrid.io

# Smart Contract Addresses
NEXT_PUBLIC_NFT_CONTRACT=TRXxxx...
NEXT_PUBLIC_TOKEN_CONTRACT=TRXxxx...
NEXT_PUBLIC_GOVERNANCE_CONTRACT=TRXxxx...
NEXT_PUBLIC_REWARD_DISTRIBUTOR=TRXxxx...
NEXT_PUBLIC_ROYALTY_CONTRACT=TRXxxx...
```

## TronWeb Manager

Located in `src/lib/tronweb.ts`, this manager handles all TronLink interactions.

### Initialization

```typescript
import { tronWebManager } from '@/lib/tronweb';

// Initialize TronWeb
const initialized = await tronWebManager.initialize();

if (initialized) {
  console.log('TronWeb ready');
} else {
  console.log('TronWeb not available');
}
```

### Getting Wallet Address

```typescript
const address = await tronWebManager.getAddress();
console.log('Wallet address:', address);
```

### Getting Balance

```typescript
// Get TRX balance (in TRX, not SUN)
const balance = await tronWebManager.getBalance();
console.log('Balance:', balance, 'TRX');

// Get balance for specific address
const otherBalance = await tronWebManager.getBalance('TRXxxx...');
```

## Wallet Context

Use `WalletContext` for managing wallet state across the application.

### Using Wallet Context

```typescript
import { useWallet } from '@/context/WalletContext';

function MyComponent() {
  const {
    wallet,
    isConnecting,
    connect,
    disconnect,
    refreshBalance,
    signMessage,
  } = useWallet();

  if (!wallet) {
    return (
      <button onClick={connect} disabled={isConnecting}>
        {isConnecting ? 'Connecting...' : 'Connect Wallet'}
      </button>
    );
  }

  return (
    <div>
      <p>Address: {wallet.address}</p>
      <p>Balance: {wallet.balance.trx} TRX</p>
      <button onClick={disconnect}>Disconnect</button>
    </div>
  );
}
```

### Wallet State

```typescript
interface Wallet {
  address: string;
  balance: {
    trx: number;
    dcmx: number;
  };
  network: 'mainnet' | 'shasta' | 'nile';
  isConnected: boolean;
}
```

## Smart Contract Interactions

### Getting Contract Instance

```typescript
import { tronWebManager } from '@/lib/tronweb';

// NFT Contract ABI (simplified)
const nftAbi = [
  {
    "outputs": [],
    "inputs": [
      {"name": "to", "type": "address"},
      {"name": "tokenId", "type": "uint256"},
      {"name": "tokenUri", "type": "string"}
    ],
    "name": "mint",
    "stateMutability": "nonpayable",
    "type": "function"
  }
];

const contractAddress = process.env.NEXT_PUBLIC_NFT_CONTRACT;
const contract = tronWebManager.getContract(nftAbi, contractAddress);
```

### Calling Contract Methods

#### Read-Only Calls (No Gas)

```typescript
// Get NFT owner
const owner = await contract.ownerOf(tokenId).call();
console.log('Owner:', owner);

// Get token URI
const uri = await contract.tokenURI(tokenId).call();
console.log('URI:', uri);

// Get royalty info
const [recipient, amount] = await contract.royaltyInfo(tokenId, salePrice).call();
console.log('Royalty:', recipient, amount);
```

#### State-Changing Calls (Requires Gas)

```typescript
// Mint NFT
const result = await contract.mint(
  toAddress,
  tokenId,
  tokenUri
).send({
  feeLimit: 100_000_000,  // 100 TRX in SUN
  callValue: 0,            // Amount of TRX to send (0 for non-payable)
});

console.log('Transaction:', result);

// Wait for confirmation
const confirmed = await tronWebManager.waitForTransaction(result);
console.log('Confirmed:', confirmed);
```

### Transaction Examples

#### Sending TRX

```typescript
import { tronWebManager } from '@/lib/tronweb';

// Send 10 TRX
const result = await tronWebManager.sendTransaction(
  'TRXxxx...',  // To address
  10            // Amount in TRX
);

console.log('Transaction hash:', result);
```

#### Minting NFT

```typescript
import { useNFT } from '@/hooks/useNFT';

function MintNFTButton() {
  const { mintNFT, isLoading } = useNFT();

  const handleMint = async () => {
    const result = await mintNFT(
      123,              // token ID
      'ipfs://xxx...',  // token URI
      'TRXxxx...',      // royalty recipient
      1000              // royalty BPS (10%)
    );

    if (result) {
      console.log('NFT minted successfully');
    }
  };

  return (
    <button onClick={handleMint} disabled={isLoading}>
      {isLoading ? 'Minting...' : 'Mint NFT'}
    </button>
  );
}
```

#### Claiming Rewards

```typescript
import { useRewards } from '@/hooks/useRewards';

function ClaimRewardsButton() {
  const { claimReward, isClaimingReward } = useRewards();

  const handleClaim = async (rewardId: string) => {
    const success = await claimReward(rewardId);
    
    if (success) {
      console.log('Reward claimed successfully');
    }
  };

  return (
    <button onClick={() => handleClaim('reward_id')} disabled={isClaimingReward}>
      {isClaimingReward ? 'Claiming...' : 'Claim Reward'}
    </button>
  );
}
```

## Signing Messages

### Message Signing

```typescript
import { useWallet } from '@/context/WalletContext';

function SignMessageExample() {
  const { signMessage } = useWallet();

  const handleSign = async () => {
    try {
      const message = 'Sign this message to authenticate';
      const signature = await signMessage(message);
      console.log('Signature:', signature);
    } catch (error) {
      console.error('Signing failed:', error);
    }
  };

  return <button onClick={handleSign}>Sign Message</button>;
}
```

### Authentication with Signature

```typescript
import { useAuth } from '@/context/AuthContext';
import { useWallet } from '@/context/WalletContext';
import { apiClient } from '@/lib/api-client';

async function authenticateWithWallet() {
  const { wallet, signMessage } = useWallet();
  const { login } = useAuth();

  // 1. Get nonce from backend
  const { nonce } = await apiClient.post('/api/auth/nonce', {
    walletAddress: wallet.address,
  });

  // 2. Sign nonce
  const signature = await signMessage(nonce);

  // 3. Login with signature
  const success = await login(wallet.address, signature);

  return success;
}
```

## Event Listeners

### Account Change

```typescript
import { tronWebManager } from '@/lib/tronweb';

tronWebManager.on('accountsChanged', (accounts) => {
  console.log('Account changed:', accounts);
  // Refresh wallet state
  refreshWalletData();
});
```

### Network Change

```typescript
tronWebManager.on('chainChanged', (chainId) => {
  console.log('Network changed:', chainId);
  // Update network state
  updateNetwork(chainId);
});
```

## Error Handling

### Common Errors

#### User Rejected Transaction

```typescript
try {
  await contract.mint(...).send({...});
} catch (error) {
  if (error.message.includes('User rejected')) {
    console.log('User rejected transaction');
    toast.error('Transaction cancelled');
  }
}
```

#### Insufficient Balance

```typescript
try {
  await tronWebManager.sendTransaction(to, amount);
} catch (error) {
  if (error.message.includes('insufficient')) {
    console.log('Insufficient balance');
    toast.error('Not enough TRX');
  }
}
```

#### Contract Revert

```typescript
try {
  await contract.mint(...).send({...});
} catch (error) {
  if (error.message.includes('revert')) {
    console.log('Contract reverted:', error.message);
    toast.error('Transaction failed');
  }
}
```

## Best Practices

1. **Always Check Wallet Connection**: Verify wallet is connected before transactions

2. **Handle User Rejection**: Gracefully handle when users reject transactions

3. **Show Gas Estimates**: Display estimated fees before transactions

4. **Confirm Before Sending**: Show confirmation dialog for important transactions

5. **Wait for Confirmation**: Don't assume immediate success, wait for blockchain confirmation

6. **Handle Network Switches**: Account for users switching between mainnet/testnet

7. **Cache Contract Instances**: Don't recreate contract instances unnecessarily

8. **Error Messages**: Provide clear, user-friendly error messages

## Testing

### Testnet Testing

1. Switch TronLink to Shasta Testnet
2. Get testnet TRX from faucet
3. Deploy contracts to testnet
4. Update `.env.local` with testnet contract addresses

### Manual Testing Checklist

- [ ] Wallet connection
- [ ] Wallet disconnection
- [ ] Balance refresh
- [ ] Message signing
- [ ] NFT minting
- [ ] NFT transfer
- [ ] Reward claiming
- [ ] Transaction waiting
- [ ] Error handling
- [ ] Account switching
- [ ] Network switching

## Troubleshooting

### TronLink Not Detected

```typescript
if (!window.tronWeb && !window.tronLink) {
  // Show install prompt
  window.open('https://www.tronlink.org/', '_blank');
}
```

### Transaction Timeout

```typescript
try {
  const result = await tronWebManager.waitForTransaction(txId, 30);
} catch (error) {
  console.log('Transaction timeout');
  // Retry or ask user to check blockchain explorer
}
```

### Wrong Network

```typescript
const expectedNetwork = process.env.NEXT_PUBLIC_TRON_NETWORK;
const currentNetwork = wallet.network;

if (currentNetwork !== expectedNetwork) {
  toast.error(`Please switch to ${expectedNetwork} network`);
}
```

## Resources

- [TronWeb Documentation](https://developers.tron.network/docs/tronweb-introduction)
- [TronLink Documentation](https://docs.tronlink.org/)
- [TRON Developer Hub](https://developers.tron.network/)
- [Shasta Testnet Faucet](https://www.trongrid.io/faucet)
- [TronScan (Block Explorer)](https://tronscan.org/)
