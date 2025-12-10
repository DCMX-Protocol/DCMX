import { NextRequest, NextResponse } from 'next/server';
import { SignJWT } from 'jose';

const JWT_SECRET = new TextEncoder().encode(
  process.env.JWT_SECRET || 'your-super-secret-jwt-key-change-this-in-production'
);

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { walletAddress, signature } = body;

    if (!walletAddress || !signature) {
      return NextResponse.json(
        { success: false, error: 'Wallet address and signature are required' },
        { status: 400 }
      );
    }

    // In a real implementation, verify the signature here
    // For now, we'll trust the client verification
    
    // Forward to backend API for user creation/retrieval
    const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
    
    try {
      const backendResponse = await fetch(`${backendUrl}/api/v1/wallet/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          wallet_address: walletAddress,
          username: walletAddress.slice(0, 8),
        }),
      });

      const backendData = await backendResponse.json();
      
      if (!backendData.success) {
        throw new Error(backendData.error || 'Backend authentication failed');
      }

      // Generate JWT token
      const token = await new SignJWT({
        walletAddress,
        userId: backendData.wallet?.id || walletAddress,
      })
        .setProtectedHeader({ alg: 'HS256' })
        .setIssuedAt()
        .setExpirationTime('7d')
        .sign(JWT_SECRET);

      // Prepare user object
      const user = {
        id: backendData.wallet?.id || walletAddress,
        walletAddress: walletAddress,
        username: backendData.wallet?.username || walletAddress.slice(0, 8),
        email: backendData.wallet?.email,
        kycVerified: backendData.wallet?.kyc_verified || false,
        kycLevel: backendData.wallet?.kyc_level || 0,
        balanceDCMX: parseFloat(backendData.wallet?.balance_dcmx || '0'),
        balanceTRX: 0,
        createdAt: backendData.wallet?.created_at || new Date().toISOString(),
        updatedAt: backendData.wallet?.updated_at || new Date().toISOString(),
      };

      return NextResponse.json({
        success: true,
        token,
        user,
        message: 'Authentication successful',
      });
    } catch (backendError) {
      console.error('Backend API error:', backendError);
      
      // Fallback: Create token without backend validation
      const token = await new SignJWT({
        walletAddress,
        userId: walletAddress,
      })
        .setProtectedHeader({ alg: 'HS256' })
        .setIssuedAt()
        .setExpirationTime('7d')
        .sign(JWT_SECRET);

      const user = {
        id: walletAddress,
        walletAddress: walletAddress,
        username: walletAddress.slice(0, 8),
        kycVerified: false,
        kycLevel: 0,
        balanceDCMX: 0,
        balanceTRX: 0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };

      return NextResponse.json({
        success: true,
        token,
        user,
        message: 'Authentication successful (offline mode)',
      });
    }
  } catch (error) {
    console.error('Login error:', error);
    return NextResponse.json(
      { success: false, error: 'Authentication failed' },
      { status: 500 }
    );
  }
}
