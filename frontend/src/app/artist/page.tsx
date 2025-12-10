'use client';

import React from 'react';
import { Upload, Music, DollarSign, Users } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { useAuth } from '@/context/AuthContext';
import { useWallet } from '@/context/WalletContext';

export default function ArtistHubPage() {
  const { user } = useAuth();
  const { wallet } = useWallet();

  const features = [
    {
      icon: Upload,
      title: 'Upload Music',
      description: 'Upload your original music tracks with full metadata',
    },
    {
      icon: Music,
      title: 'Mint as NFT',
      description: 'Convert your tracks into limited edition NFTs',
    },
    {
      icon: DollarSign,
      title: 'Set Royalties',
      description: 'Configure royalty percentages for secondary sales',
    },
    {
      icon: Users,
      title: 'Build Audience',
      description: 'Connect with fans and grow your community',
    },
  ];

  if (!wallet) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-dark-bg flex items-center justify-center">
        <Card className="max-w-md mx-4">
          <CardContent className="p-8 text-center">
            <Music className="w-16 h-16 mx-auto mb-4 text-gray-400" />
            <h2 className="text-2xl font-bold mb-2">Connect Your Wallet</h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Please connect your wallet to access the Artist Hub
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-dark-bg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Artist Hub
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Create, manage, and monetize your music on the blockchain
          </p>
        </div>

        {/* Artist Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total NFTs</div>
              <div className="text-3xl font-bold text-gray-900 dark:text-white">0</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total Sales</div>
              <div className="text-3xl font-bold text-gray-900 dark:text-white">0 TRX</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total Fans</div>
              <div className="text-3xl font-bold text-gray-900 dark:text-white">0</div>
            </CardContent>
          </Card>
        </div>

        {/* Features */}
        <div className="grid md:grid-cols-2 gap-6 mb-8">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <Card key={feature.title}>
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    <div className="p-3 bg-primary-100 dark:bg-primary-900/20 rounded-lg">
                      <Icon className="w-6 h-6 text-primary-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
                        {feature.title}
                      </h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {feature.description}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Upload Section */}
        <Card>
          <CardHeader>
            <CardTitle>Create New NFT</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center py-12">
              <Upload className="w-16 h-16 mx-auto mb-4 text-gray-400 dark:text-gray-600" />
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Upload Your Music
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Drag and drop your audio file or click to browse
              </p>
              <Button>
                Select File
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
