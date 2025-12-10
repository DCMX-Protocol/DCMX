import React from 'react';
import Link from 'next/link';
import { Music, Github, Twitter, Mail } from 'lucide-react';

export function Footer() {
  return (
    <footer className="bg-white dark:bg-dark-card border-t border-gray-200 dark:border-dark-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="col-span-1">
            <div className="flex items-center space-x-2 mb-4">
              <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <Music className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900 dark:text-white">DCMX</span>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Decentralized music network powered by blockchain technology.
            </p>
          </div>

          {/* Platform */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">Platform</h3>
            <ul className="space-y-2">
              <li>
                <Link href="/marketplace" className="text-sm text-gray-600 dark:text-gray-400 hover:text-primary-600">
                  Marketplace
                </Link>
              </li>
              <li>
                <Link href="/artist" className="text-sm text-gray-600 dark:text-gray-400 hover:text-primary-600">
                  For Artists
                </Link>
              </li>
              <li>
                <Link href="/dashboard/rewards" className="text-sm text-gray-600 dark:text-gray-400 hover:text-primary-600">
                  Rewards
                </Link>
              </li>
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">Resources</h3>
            <ul className="space-y-2">
              <li>
                <a href="#" className="text-sm text-gray-600 dark:text-gray-400 hover:text-primary-600">
                  Documentation
                </a>
              </li>
              <li>
                <a href="#" className="text-sm text-gray-600 dark:text-gray-400 hover:text-primary-600">
                  White Paper
                </a>
              </li>
              <li>
                <a href="#" className="text-sm text-gray-600 dark:text-gray-400 hover:text-primary-600">
                  API Reference
                </a>
              </li>
            </ul>
          </div>

          {/* Social */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-4">Connect</h3>
            <div className="flex space-x-4">
              <a href="#" className="text-gray-600 dark:text-gray-400 hover:text-primary-600">
                <Github className="w-5 h-5" />
              </a>
              <a href="#" className="text-gray-600 dark:text-gray-400 hover:text-primary-600">
                <Twitter className="w-5 h-5" />
              </a>
              <a href="#" className="text-gray-600 dark:text-gray-400 hover:text-primary-600">
                <Mail className="w-5 h-5" />
              </a>
            </div>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-gray-200 dark:border-dark-border">
          <p className="text-sm text-gray-600 dark:text-gray-400 text-center">
            © {new Date().getFullYear()} DCMX. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
