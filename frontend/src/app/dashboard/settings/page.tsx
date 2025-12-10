'use client';

import React, { useState } from 'react';
import { User, Bell, Shield, Palette } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';

export default function SettingsPage() {
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [username, setUsername] = useState(user?.username || '');

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-dark-bg">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Settings
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage your account settings and preferences
          </p>
        </div>

        {/* Profile Settings */}
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-center gap-3">
              <User className="w-5 h-5 text-primary-600" />
              <CardTitle>Profile</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Username
                </label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-dark-border rounded-lg bg-white dark:bg-dark-card text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="Enter username"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Wallet Address
                </label>
                <input
                  type="text"
                  value={user?.walletAddress || ''}
                  disabled
                  className="w-full px-3 py-2 border border-gray-300 dark:border-dark-border rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400"
                />
              </div>
              <Button>Save Changes</Button>
            </div>
          </CardContent>
        </Card>

        {/* Theme Settings */}
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-center gap-3">
              <Palette className="w-5 h-5 text-primary-600" />
              <CardTitle>Appearance</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-gray-900 dark:text-white">Theme</div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Current theme: {theme === 'dark' ? 'Dark' : 'Light'}
                </div>
              </div>
              <Button onClick={toggleTheme}>
                Toggle Theme
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Notifications */}
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-center gap-3">
              <Bell className="w-5 h-5 text-primary-600" />
              <CardTitle>Notifications</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-gray-900 dark:text-white">NFT Sales</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    Get notified when your NFTs are sold
                  </div>
                </div>
                <input type="checkbox" className="w-5 h-5 text-primary-600 rounded" />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-gray-900 dark:text-white">New Rewards</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">
                    Get notified when you earn new rewards
                  </div>
                </div>
                <input type="checkbox" className="w-5 h-5 text-primary-600 rounded" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* KYC Status */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <Shield className="w-5 h-5 text-primary-600" />
              <CardTitle>KYC Verification</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-gray-900 dark:text-white">
                  Verification Status
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  {user?.kycVerified ? 'Verified' : 'Not Verified'}
                </div>
              </div>
              {!user?.kycVerified && (
                <Button variant="outline">Start Verification</Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
