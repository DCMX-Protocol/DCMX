'use client';

import React from 'react';
import Link from 'next/link';
import { Music, Users, Shield, Zap, ArrowRight, Play } from 'lucide-react';
import { Button } from '@/components/common/Button';
import { Card, CardContent } from '@/components/common/Card';
import { useWallet } from '@/context/WalletContext';

const features = [
  {
    icon: Music,
    title: 'Decentralized Music',
    description: 'Own your music as NFTs. Artists retain full control and rights over their content.',
  },
  {
    icon: Users,
    title: 'Direct Artist Support',
    description: 'Support artists directly without intermediaries. 85% of revenue goes to creators.',
  },
  {
    icon: Shield,
    title: 'Blockchain Security',
    description: 'Built on TRON blockchain for secure, transparent, and immutable transactions.',
  },
  {
    icon: Zap,
    title: 'Rewards System',
    description: 'Earn DCMX tokens by participating in the network, voting, and supporting artists.',
  },
];

const stats = [
  { label: 'Artists', value: '10K+' },
  { label: 'NFTs Minted', value: '50K+' },
  { label: 'Active Users', value: '100K+' },
  { label: 'Total Volume', value: '$5M+' },
];

export default function LandingPage() {
  const { wallet, connect, isConnecting } = useWallet();

  return (
    <div className="bg-white dark:bg-dark-bg">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-primary-600 to-primary-800 text-white">
        <div className="absolute inset-0 bg-black/10" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 md:py-32">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold mb-6 animate-fade-in">
              Decentralized Music Network
            </h1>
            <p className="text-xl md:text-2xl mb-8 text-primary-100 max-w-3xl mx-auto animate-slide-up">
              Create, discover, and trade music NFTs on the blockchain. Powered by TRON and built
              for artists.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center animate-slide-up">
              {wallet ? (
                <Link href="/dashboard">
                  <Button size="lg" className="min-w-[200px]">
                    Go to Dashboard
                    <ArrowRight className="ml-2 w-5 h-5" />
                  </Button>
                </Link>
              ) : (
                <Button size="lg" onClick={connect} isLoading={isConnecting} className="min-w-[200px]">
                  Connect Wallet
                </Button>
              )}
              <Link href="/marketplace">
                <Button size="lg" variant="outline" className="min-w-[200px] border-white text-white hover:bg-white/10">
                  Explore Marketplace
                  <Play className="ml-2 w-5 h-5" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="bg-gray-50 dark:bg-dark-card border-y border-gray-200 dark:border-dark-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="text-3xl md:text-4xl font-bold text-primary-600 mb-2">
                  {stat.value}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Why Choose DCMX?</h2>
            <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
              The future of music distribution is here. Join the revolution.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <Card key={feature.title} className="text-center hover:shadow-lg transition-shadow">
                  <CardContent className="p-6">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 dark:bg-primary-900/20 rounded-full mb-4">
                      <Icon className="w-8 h-8 text-primary-600" />
                    </div>
                    <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                    <p className="text-gray-600 dark:text-gray-400">{feature.description}</p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-primary-600 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">Ready to Get Started?</h2>
          <p className="text-xl text-primary-100 mb-8 max-w-2xl mx-auto">
            Join thousands of artists and music lovers on the DCMX platform.
          </p>
          {wallet ? (
            <Link href="/dashboard">
              <Button size="lg" variant="outline" className="border-white text-white hover:bg-white hover:text-primary-600">
                Go to Dashboard
                <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
            </Link>
          ) : (
            <Button size="lg" onClick={connect} isLoading={isConnecting} variant="outline" className="border-white text-white hover:bg-white hover:text-primary-600">
              Connect Wallet to Start
            </Button>
          )}
        </div>
      </section>
    </div>
  );
}
