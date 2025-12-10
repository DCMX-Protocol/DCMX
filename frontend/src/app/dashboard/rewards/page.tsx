'use client';

import React from 'react';
import { Award, TrendingUp, Users, Zap } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { useRewards } from '@/hooks/useRewards';
import { formatCurrency } from '@/utils/format';

export default function RewardsPage() {
  const { rewards, totalClaimable, isLoading, claimAllRewards, isClaimingReward } = useRewards();

  const rewardTypes = [
    {
      type: 'energy' as const,
      label: 'Network Energy',
      description: 'Rewards for running a node and serving content',
      icon: Zap,
      color: 'text-yellow-600',
    },
    {
      type: 'voting' as const,
      label: 'Voting Participation',
      description: 'Rewards for participating in governance',
      icon: Users,
      color: 'text-blue-600',
    },
    {
      type: 'referral' as const,
      label: 'Referral Bonus',
      description: 'Rewards for bringing new users to the platform',
      icon: TrendingUp,
      color: 'text-green-600',
    },
    {
      type: 'creator' as const,
      label: 'Creator Rewards',
      description: 'Rewards for creating and minting NFTs',
      icon: Award,
      color: 'text-purple-600',
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-dark-bg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Rewards Center
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Earn DCMX tokens by participating in the network
          </p>
        </div>

        {/* Total Claimable */}
        <Card className="mb-8 bg-gradient-to-br from-primary-600 to-primary-800 text-white border-0">
          <CardContent className="p-8">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm opacity-90 mb-2">Total Claimable Rewards</div>
                <div className="text-4xl font-bold mb-4">
                  {formatCurrency(totalClaimable, 'DCMX')}
                </div>
                <Button
                  onClick={claimAllRewards}
                  isLoading={isClaimingReward}
                  disabled={totalClaimable === 0}
                  variant="outline"
                  className="border-white text-white hover:bg-white hover:text-primary-600"
                >
                  Claim All Rewards
                </Button>
              </div>
              <Award className="w-24 h-24 opacity-20" />
            </div>
          </CardContent>
        </Card>

        {/* Reward Types */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          {rewardTypes.map((type) => {
            const Icon = type.icon;
            const typeRewards = rewards.filter((r) => r.rewardType === type.type);
            const typeTotal = typeRewards.reduce((sum, r) => sum + r.amount, 0);

            return (
              <Card key={type.type}>
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg bg-gray-100 dark:bg-gray-800 ${type.color}`}>
                      <Icon className="w-6 h-6" />
                    </div>
                    <CardTitle>{type.label}</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                    {type.description}
                  </p>
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">Available</div>
                      <div className="text-2xl font-bold text-gray-900 dark:text-white">
                        {formatCurrency(typeTotal, 'DCMX')}
                      </div>
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {typeRewards.length} reward{typeRewards.length !== 1 ? 's' : ''}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Recent Rewards */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Rewards</CardTitle>
          </CardHeader>
          <CardContent>
            {rewards.length === 0 ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                <Award className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No rewards available yet</p>
                <p className="text-sm mt-2">
                  Participate in the network to start earning rewards
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {rewards.slice(0, 5).map((reward) => (
                  <div
                    key={reward.id}
                    className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
                  >
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">
                        {reward.description}
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400 capitalize">
                        {reward.rewardType.replace('_', ' ')} • {reward.status}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold text-primary-600">
                        +{formatCurrency(reward.amount, 'DCMX')}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
