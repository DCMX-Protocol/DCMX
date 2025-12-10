import { NextRequest, NextResponse } from 'next/server';
import { randomBytes } from 'crypto';

// Store nonces in memory (in production, use Redis)
const nonces = new Map<string, { nonce: string; timestamp: number }>();

// Clean up old nonces every minute
setInterval(() => {
  const now = Date.now();
  const FIVE_MINUTES = 5 * 60 * 1000;
  
  for (const [address, data] of nonces.entries()) {
    if (now - data.timestamp > FIVE_MINUTES) {
      nonces.delete(address);
    }
  }
}, 60000);

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { walletAddress } = body;

    if (!walletAddress) {
      return NextResponse.json(
        { success: false, error: 'Wallet address is required' },
        { status: 400 }
      );
    }

    // Generate a random nonce
    const nonce = randomBytes(32).toString('hex');
    const timestamp = Date.now();

    // Store nonce
    nonces.set(walletAddress, { nonce, timestamp });

    return NextResponse.json({
      success: true,
      nonce,
      message: `Sign this message to authenticate: ${nonce}`,
    });
  } catch (error) {
    console.error('Nonce generation error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to generate nonce' },
      { status: 500 }
    );
  }
}
