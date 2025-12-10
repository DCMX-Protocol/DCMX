// Core type definitions for DCMX Frontend

export interface User {
  id: string;
  walletAddress: string;
  username: string;
  email?: string;
  kycVerified: boolean;
  kycLevel: number;
  balanceDCMX: number;
  balanceTRX: number;
  createdAt: string;
  updatedAt: string;
}

export interface Track {
  id: string;
  title: string;
  artist: string;
  album?: string;
  duration: number;
  size: number;
  contentHash: string;
  watermarkHash?: string;
  perceptualFingerprint?: string;
  nftContract?: string;
  tokenId?: number;
  coverArt?: string;
  audioUrl: string;
  createdAt: string;
}

export interface NFT {
  id: string;
  contractAddress: string;
  tokenId: number;
  owner: string;
  creator: string;
  title: string;
  description: string;
  imageUrl: string;
  audioUrl?: string;
  editionNumber: number;
  maxEditions: number;
  royaltyBps: number;
  royaltyRecipient: string;
  price: number;
  currency: 'TRX' | 'DCMX';
  metadata: Record<string, any>;
  createdAt: string;
  lastSaleAt?: string;
}

export interface Wallet {
  address: string;
  balance: {
    trx: number;
    dcmx: number;
  };
  network: 'mainnet' | 'shasta' | 'nile';
  isConnected: boolean;
}

export interface Reward {
  id: string;
  userId: string;
  rewardType: 'energy' | 'voting' | 'referral' | 'creator';
  amount: number;
  currency: 'DCMX';
  status: 'pending' | 'claimable' | 'claimed';
  claimedAt?: string;
  description: string;
  metadata?: Record<string, any>;
  createdAt: string;
}

export interface Transaction {
  id: string;
  hash: string;
  from: string;
  to: string;
  amount: number;
  currency: 'TRX' | 'DCMX';
  type: 'transfer' | 'nft_purchase' | 'reward_claim' | 'royalty_payment';
  status: 'pending' | 'confirmed' | 'failed';
  blockNumber?: number;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface Playlist {
  id: string;
  name: string;
  description?: string;
  owner: string;
  tracks: Track[];
  coverArt?: string;
  isPublic: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface Vote {
  id: string;
  userId: string;
  proposalId: string;
  choice: 'for' | 'against' | 'abstain';
  votingPower: number;
  timestamp: string;
}

export interface Proposal {
  id: string;
  title: string;
  description: string;
  proposer: string;
  status: 'pending' | 'active' | 'succeeded' | 'defeated' | 'executed';
  votesFor: number;
  votesAgainst: number;
  votesAbstain: number;
  startTime: string;
  endTime: string;
  executionTime?: string;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T = any> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

export interface MusicPlayerState {
  currentTrack: Track | null;
  isPlaying: boolean;
  volume: number;
  currentTime: number;
  duration: number;
  playlist: Track[];
  repeat: 'off' | 'one' | 'all';
  shuffle: boolean;
}

export interface TronWebInstance {
  ready: boolean;
  contract: (abi: any[], address: string) => any;
  trx: {
    getBalance: (address: string) => Promise<number>;
    sendTransaction: (to: string, amount: number) => Promise<any>;
    sign: (message: string) => Promise<string>;
  };
  address: {
    fromHex: (hex: string) => string;
    toHex: (address: string) => string;
  };
  defaultAddress: {
    base58: string;
    hex: string;
  };
}
