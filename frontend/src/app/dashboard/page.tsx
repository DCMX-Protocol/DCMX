'use client';

import React from 'react';
import { Music, Wallet, TrendingUp, Award } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import { useAuth } from '@/context/AuthContext';
import { useWallet } from '@/context/WalletContext';
import { formatCurrency } from '@/utils/format';
import Link from 'next/link';
import { Button } from '@/components/common/Button';

export default function DashboardPage() {
  const { user } = useAuth();
  const { wallet } = useWallet();

  const stats = [
    {
      label: 'DCMX Balance',
      value: formatCurrency(user?.balanceDCMX || 0, 'DCMX'),
      icon: Wallet,
      change: '+12.5%',
      color: 'text-blue-600',
    },
    {
      label: 'TRX Balance',
      value: formatCurrency(wallet?.balance.trx || 0, 'TRX'),
      icon: TrendingUp,
      change: '+5.2%',
      color: 'text-green-600',
    },
    {
      label: 'Owned NFTs',
      value: '0',
      icon: Music,
      change: '0',
      color: 'text-purple-600',
    },
    {
      label: 'Total Rewards',
      value: '0 DCMX',
      icon: Award,
      change: '0',
      color: 'text-orange-600',
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-dark-bg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Welcome back{user?.username ? `, ${user.username}` : ''}!
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Here's what's happening with your music today.
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat) => {
            const Icon = stat.icon;
            return (
              <Card key={stat.label}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className={`p-2 rounded-lg bg-gray-100 dark:bg-gray-800 ${stat.color}`}>
                      <Icon className="w-6 h-6" />
                    </div>
                    <span className="text-sm text-green-600">{stat.change}</span>
                  </div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white mb-1">
                    {stat.value}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">{stat.label}</div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Quick Actions */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <Link href="/marketplace">
                  <Button fullWidth variant="outline">
                    Browse Marketplace
                  </Button>
                </Link>
                <Link href="/artist">
                  <Button fullWidth variant="outline">
                    Create NFT
                  </Button>
                </Link>
                <Link href="/dashboard/rewards">
                  <Button fullWidth variant="outline">
                    Claim Rewards
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                No recent activity
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Music Library Preview */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>My Music Library</CardTitle>
              <Link href="/dashboard/library">
                <Button variant="ghost" size="sm">
                  View All
                </Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              <Music className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p className="mb-4">Your music library is empty</p>
              <Link href="/marketplace">
                <Button>Explore Marketplace</Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
