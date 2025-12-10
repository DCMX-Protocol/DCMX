import { useState, useCallback, useEffect } from 'react';
import { Reward } from '@/types';
import { useWallet } from '@/context/WalletContext';
import { useRewardsApi } from './useApi';
import { tronWebManager } from '@/lib/tronweb';
import toast from 'react-hot-toast';

export function useRewards() {
  const { wallet } = useWallet();
  const rewardsApi = useRewardsApi();
  const [rewards, setRewards] = useState<Reward[]>([]);
  const [totalClaimable, setTotalClaimable] = useState(0);
  const [isClaimingReward, setIsClaimingReward] = useState(false);

  const loadRewards = useCallback(async () => {
    if (!wallet) return;

    try {
      const data = await rewardsApi.getRewards(wallet.address);
      if (data?.rewards) {
        setRewards(data.rewards);
        
        // Calculate total claimable
        const claimable = data.rewards
          .filter((r: Reward) => r.status === 'claimable')
          .reduce((sum: number, r: Reward) => sum + r.amount, 0);
        
        setTotalClaimable(claimable);
      }
    } catch (error) {
      console.error('Failed to load rewards:', error);
    }
  }, [wallet, rewardsApi]);

  useEffect(() => {
    loadRewards();
  }, [loadRewards]);

  const claimReward = useCallback(
    async (rewardId: string) => {
      if (!wallet) {
        toast.error('Please connect your wallet');
        return false;
      }

      setIsClaimingReward(true);

      try {
        const contractAddress = process.env.NEXT_PUBLIC_REWARD_DISTRIBUTOR;
        if (!contractAddress) {
          throw new Error('Reward distributor contract not configured');
        }

        // Call smart contract to claim reward
        const contract = tronWebManager.getContract([], contractAddress);
        
        const result = await contract.claimReward(rewardId).send({
          feeLimit: 100_000_000,
          callValue: 0,
        });

        await tronWebManager.waitForTransaction(result);

        // Update backend
        await rewardsApi.claimReward(rewardId);

        // Reload rewards
        await loadRewards();

        toast.success('Reward claimed successfully!');
        return true;
      } catch (error) {
        console.error('Failed to claim reward:', error);
        toast.error('Failed to claim reward');
        return false;
      } finally {
        setIsClaimingReward(false);
      }
    },
    [wallet, rewardsApi, loadRewards]
  );

  const claimAllRewards = useCallback(async () => {
    const claimableRewards = rewards.filter((r) => r.status === 'claimable');

    if (claimableRewards.length === 0) {
      toast.error('No rewards to claim');
      return false;
    }

    let successCount = 0;

    for (const reward of claimableRewards) {
      const success = await claimReward(reward.id);
      if (success) successCount++;
    }

    if (successCount > 0) {
      toast.success(`Claimed ${successCount} reward(s)`);
      return true;
    }

    return false;
  }, [rewards, claimReward]);

  const getRewardsByType = useCallback(
    (type: Reward['rewardType']) => {
      return rewards.filter((r) => r.rewardType === type);
    },
    [rewards]
  );

  return {
    rewards,
    totalClaimable,
    isLoading: rewardsApi.isLoading,
    isClaimingReward,
    loadRewards,
    claimReward,
    claimAllRewards,
    getRewardsByType,
  };
}
