import { useState, useCallback } from 'react';
import { tronWebManager } from '@/lib/tronweb';
import { useWallet } from '@/context/WalletContext';
import toast from 'react-hot-toast';

export function useNFT() {
  const { wallet } = useWallet();
  const [isLoading, setIsLoading] = useState(false);

  const mintNFT = useCallback(
    async (
      tokenId: number,
      tokenUri: string,
      royaltyRecipient: string,
      royaltyBps: number
    ) => {
      if (!wallet) {
        toast.error('Please connect your wallet');
        return null;
      }

      setIsLoading(true);

      try {
        const contractAddress = process.env.NEXT_PUBLIC_NFT_CONTRACT;
        if (!contractAddress) {
          throw new Error('NFT contract address not configured');
        }

        // Get contract instance
        const contract = tronWebManager.getContract([], contractAddress);

        // Call mint function
        const result = await contract.mint(
          wallet.address,
          tokenId,
          tokenUri,
          royaltyRecipient,
          royaltyBps
        ).send({
          feeLimit: 100_000_000,
          callValue: 0,
        });

        toast.success('NFT minted successfully!');
        return result;
      } catch (error) {
        console.error('NFT minting failed:', error);
        toast.error('Failed to mint NFT');
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [wallet]
  );

  const purchaseNFT = useCallback(
    async (tokenId: number, price: number) => {
      if (!wallet) {
        toast.error('Please connect your wallet');
        return null;
      }

      setIsLoading(true);

      try {
        const contractAddress = process.env.NEXT_PUBLIC_NFT_CONTRACT;
        if (!contractAddress) {
          throw new Error('NFT contract address not configured');
        }

        // Send TRX to purchase NFT
        const result = await tronWebManager.sendTransaction(
          contractAddress,
          price
        );

        await tronWebManager.waitForTransaction(result);

        toast.success('NFT purchased successfully!');
        return result;
      } catch (error) {
        console.error('NFT purchase failed:', error);
        toast.error('Failed to purchase NFT');
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [wallet]
  );

  const transferNFT = useCallback(
    async (to: string, tokenId: number) => {
      if (!wallet) {
        toast.error('Please connect your wallet');
        return null;
      }

      setIsLoading(true);

      try {
        const contractAddress = process.env.NEXT_PUBLIC_NFT_CONTRACT;
        if (!contractAddress) {
          throw new Error('NFT contract address not configured');
        }

        const contract = tronWebManager.getContract([], contractAddress);

        const result = await contract.transferFrom(
          wallet.address,
          to,
          tokenId
        ).send({
          feeLimit: 100_000_000,
          callValue: 0,
        });

        toast.success('NFT transferred successfully!');
        return result;
      } catch (error) {
        console.error('NFT transfer failed:', error);
        toast.error('Failed to transfer NFT');
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [wallet]
  );

  const getNFTOwner = useCallback(async (tokenId: number): Promise<string | null> => {
    try {
      const contractAddress = process.env.NEXT_PUBLIC_NFT_CONTRACT;
      if (!contractAddress) {
        throw new Error('NFT contract address not configured');
      }

      const contract = tronWebManager.getContract([], contractAddress);
      const owner = await contract.ownerOf(tokenId).call();
      return owner;
    } catch (error) {
      console.error('Failed to get NFT owner:', error);
      return null;
    }
  }, []);

  const getNFTMetadata = useCallback(async (tokenId: number): Promise<string | null> => {
    try {
      const contractAddress = process.env.NEXT_PUBLIC_NFT_CONTRACT;
      if (!contractAddress) {
        throw new Error('NFT contract address not configured');
      }

      const contract = tronWebManager.getContract([], contractAddress);
      const uri = await contract.tokenURI(tokenId).call();
      return uri;
    } catch (error) {
      console.error('Failed to get NFT metadata:', error);
      return null;
    }
  }, []);

  return {
    isLoading,
    mintNFT,
    purchaseNFT,
    transferNFT,
    getNFTOwner,
    getNFTMetadata,
  };
}
