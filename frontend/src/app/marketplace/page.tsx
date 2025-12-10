'use client';

import React, { useState } from 'react';
import { Search, Filter, Music } from 'lucide-react';
import { Card, CardContent } from '@/components/common/Card';
import { Button } from '@/components/common/Button';

export default function MarketplacePage() {
  const [searchQuery, setSearchQuery] = useState('');

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-dark-bg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            NFT Marketplace
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Discover and collect unique music NFTs from artists around the world
          </p>
        </div>

        {/* Search and Filters */}
        <div className="flex flex-col sm:flex-row gap-4 mb-8">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search NFTs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-dark-border rounded-lg bg-white dark:bg-dark-card text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          <Button variant="outline">
            <Filter className="w-5 h-5 mr-2" />
            Filters
          </Button>
        </div>

        {/* Empty State */}
        <Card>
          <CardContent className="py-16">
            <div className="text-center">
              <Music className="w-20 h-20 mx-auto mb-4 text-gray-400 dark:text-gray-600" />
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                No NFTs available yet
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Be the first to mint and sell music NFTs on DCMX
              </p>
              <Button>Create Your First NFT</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
