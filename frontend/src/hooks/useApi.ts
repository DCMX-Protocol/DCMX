import { useState, useCallback } from 'react';
import { apiClient } from '@/lib/api-client';
import { ApiResponse } from '@/types';

interface UseApiOptions {
  onSuccess?: (data: any) => void;
  onError?: (error: any) => void;
}

export function useApi<T = any>(options?: UseApiOptions) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const execute = useCallback(
    async (apiCall: () => Promise<ApiResponse<T>>) => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await apiCall();
        
        if (response.success && response.data) {
          setData(response.data);
          options?.onSuccess?.(response.data);
          return response.data;
        } else {
          throw new Error(response.error || 'API request failed');
        }
      } catch (err) {
        const error = err as Error;
        setError(error);
        options?.onError?.(error);
        throw error;
      } finally {
        setIsLoading(false);
      }
    },
    [options]
  );

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setIsLoading(false);
  }, []);

  return {
    data,
    error,
    isLoading,
    execute,
    reset,
  };
}

// Specific API hooks

export function useWalletApi() {
  const { execute, ...rest } = useApi();

  const createWallet = useCallback(
    (walletAddress: string, username: string) =>
      execute(() =>
        apiClient.post('/api/v1/wallet/create', { wallet_address: walletAddress, username })
      ),
    [execute]
  );

  const getBalance = useCallback(
    (walletAddress: string) =>
      execute(() => apiClient.get(`/api/v1/wallet/${walletAddress}/balance`)),
    [execute]
  );

  return {
    ...rest,
    createWallet,
    getBalance,
  };
}

export function useNFTApi() {
  const { execute, ...rest } = useApi();

  const mintNFT = useCallback(
    (data: any) => execute(() => apiClient.post('/api/v1/nft/mint', data)),
    [execute]
  );

  const getNFT = useCallback(
    (tokenId: string) => execute(() => apiClient.get(`/api/v1/nft/${tokenId}`)),
    [execute]
  );

  const listNFTs = useCallback(
    (params?: any) => execute(() => apiClient.get('/api/v1/nft/list', params)),
    [execute]
  );

  return {
    ...rest,
    mintNFT,
    getNFT,
    listNFTs,
  };
}

export function useRewardsApi() {
  const { execute, ...rest } = useApi();

  const getRewards = useCallback(
    (walletAddress: string) =>
      execute(() => apiClient.get(`/api/v1/rewards/${walletAddress}`)),
    [execute]
  );

  const claimReward = useCallback(
    (rewardId: string) => execute(() => apiClient.post(`/api/v1/rewards/${rewardId}/claim`)),
    [execute]
  );

  return {
    ...rest,
    getRewards,
    claimReward,
  };
}
