// TRON Smart Contract Types

export interface ContractConfig {
  address: string;
  abi: any[];
}

export interface NFTContractMethods {
  mint: (to: string, tokenId: number, tokenUri: string, royaltyRecipient: string, royaltyBps: number) => Promise<any>;
  ownerOf: (tokenId: number) => Promise<string>;
  tokenURI: (tokenId: number) => Promise<string>;
  royaltyInfo: (tokenId: number, salePrice: number) => Promise<[string, number]>;
  transferFrom: (from: string, to: string, tokenId: number) => Promise<any>;
}

export interface TokenContractMethods {
  balanceOf: (address: string) => Promise<number>;
  transfer: (to: string, amount: number) => Promise<any>;
  approve: (spender: string, amount: number) => Promise<any>;
  allowance: (owner: string, spender: string) => Promise<number>;
}

export interface GovernanceContractMethods {
  propose: (description: string, targets: string[], values: number[], calldatas: string[]) => Promise<any>;
  castVote: (proposalId: string, support: number) => Promise<any>;
  getProposal: (proposalId: string) => Promise<any>;
  execute: (proposalId: string) => Promise<any>;
}

export interface RewardDistributorMethods {
  claimReward: (rewardId: string, amount: number, proof: string[]) => Promise<any>;
  getClaimableRewards: (address: string) => Promise<any[]>;
  distributeRewards: (recipients: string[], amounts: number[]) => Promise<any>;
}

export interface RoyaltyContractMethods {
  setRoyalty: (tokenId: number, recipient: string, bps: number) => Promise<any>;
  getRoyaltyInfo: (tokenId: number, salePrice: number) => Promise<[string, number]>;
  distributeRoyalty: (tokenId: number, salePrice: number) => Promise<any>;
}
