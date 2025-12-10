'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Wallet } from '@/types';
import { tronWebManager } from '@/lib/tronweb';
import toast from 'react-hot-toast';

interface WalletContextType {
  wallet: Wallet | null;
  isConnecting: boolean;
  connect: () => Promise<boolean>;
  disconnect: () => void;
  refreshBalance: () => Promise<void>;
  signMessage: (message: string) => Promise<string>;
}

const WalletContext = createContext<WalletContextType | undefined>(undefined);

export function WalletProvider({ children }: { children: ReactNode }) {
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);

  useEffect(() => {
    // Check if already connected
    const checkConnection = async () => {
      try {
        const initialized = await tronWebManager.initialize();
        if (initialized) {
          const address = await tronWebManager.getAddress();
          if (address) {
            await loadWallet(address);
          }
        }
      } catch (error) {
        console.error('Failed to check wallet connection:', error);
      }
    };

    checkConnection();

    // Listen for account changes
    if (typeof window !== 'undefined' && window.tronLink) {
      const handleAccountChanged = () => {
        checkConnection();
      };

      tronWebManager.on('accountsChanged', handleAccountChanged);

      return () => {
        tronWebManager.off('accountsChanged', handleAccountChanged);
      };
    }
  }, []);

  const loadWallet = async (address: string) => {
    try {
      const balance = await tronWebManager.getBalance(address);
      
      // Determine network
      const network = process.env.NEXT_PUBLIC_TRON_NETWORK as 'mainnet' | 'shasta' | 'nile' || 'shasta';

      setWallet({
        address,
        balance: {
          trx: balance,
          dcmx: 0, // Will be updated by calling the token contract
        },
        network,
        isConnected: true,
      });
    } catch (error) {
      console.error('Failed to load wallet:', error);
      throw error;
    }
  };

  const connect = async (): Promise<boolean> => {
    if (typeof window === 'undefined') {
      toast.error('Wallet connection only available in browser');
      return false;
    }

    setIsConnecting(true);

    try {
      // Check if TronLink is installed
      if (!window.tronWeb && !window.tronLink) {
        toast.error('Please install TronLink extension');
        window.open('https://www.tronlink.org/', '_blank');
        return false;
      }

      // Request account access
      const granted = await tronWebManager.requestAccountAccess();
      
      if (!granted) {
        toast.error('Wallet access denied');
        return false;
      }

      // Initialize TronWeb
      const initialized = await tronWebManager.initialize();
      
      if (!initialized) {
        toast.error('Failed to initialize TronWeb');
        return false;
      }

      // Get wallet address
      const address = await tronWebManager.getAddress();
      
      if (!address) {
        toast.error('Failed to get wallet address');
        return false;
      }

      // Load wallet data
      await loadWallet(address);
      
      toast.success('Wallet connected successfully!');
      return true;
    } catch (error) {
      console.error('Wallet connection failed:', error);
      toast.error('Failed to connect wallet');
      return false;
    } finally {
      setIsConnecting(false);
    }
  };

  const disconnect = () => {
    setWallet(null);
    toast.success('Wallet disconnected');
  };

  const refreshBalance = async () => {
    if (!wallet) return;

    try {
      const balance = await tronWebManager.getBalance(wallet.address);
      setWallet((prev) => prev ? {
        ...prev,
        balance: {
          ...prev.balance,
          trx: balance,
        },
      } : null);
    } catch (error) {
      console.error('Failed to refresh balance:', error);
    }
  };

  const signMessage = async (message: string): Promise<string> => {
    if (!wallet) {
      throw new Error('Wallet not connected');
    }

    try {
      return await tronWebManager.signMessage(message);
    } catch (error) {
      console.error('Failed to sign message:', error);
      throw error;
    }
  };

  return (
    <WalletContext.Provider
      value={{
        wallet,
        isConnecting,
        connect,
        disconnect,
        refreshBalance,
        signMessage,
      }}
    >
      {children}
    </WalletContext.Provider>
  );
}

export function useWallet() {
  const context = useContext(WalletContext);
  if (context === undefined) {
    throw new Error('useWallet must be used within a WalletProvider');
  }
  return context;
}
