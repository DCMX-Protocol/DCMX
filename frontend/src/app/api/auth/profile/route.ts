import { NextRequest, NextResponse } from 'next/server';
import { jwtVerify } from 'jose';

const JWT_SECRET = new TextEncoder().encode(
  process.env.JWT_SECRET || 'your-super-secret-jwt-key-change-this-in-production'
);

export async function GET(request: NextRequest) {
  try {
    // Get token from Authorization header
    const authHeader = request.headers.get('Authorization');
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return NextResponse.json(
        { success: false, error: 'No token provided' },
        { status: 401 }
      );
    }

    const token = authHeader.substring(7);

    // Verify JWT token
    try {
      const { payload } = await jwtVerify(token, JWT_SECRET);
      
      const walletAddress = payload.walletAddress as string;
      
      // Fetch user data from backend
      const backendUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      
      try {
        const backendResponse = await fetch(`${backendUrl}/api/v1/wallet/${walletAddress}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        const backendData = await backendResponse.json();
        
        if (backendData.success && backendData.wallet) {
          const user = {
            id: backendData.wallet.id || walletAddress,
            walletAddress: walletAddress,
            username: backendData.wallet.username || walletAddress.slice(0, 8),
            email: backendData.wallet.email,
            kycVerified: backendData.wallet.kyc_verified || false,
            kycLevel: backendData.wallet.kyc_level || 0,
            balanceDCMX: parseFloat(backendData.wallet.balance_dcmx || '0'),
            balanceTRX: 0,
            createdAt: backendData.wallet.created_at || new Date().toISOString(),
            updatedAt: backendData.wallet.updated_at || new Date().toISOString(),
          };

          return NextResponse.json({
            success: true,
            user,
          });
        }
      } catch (backendError) {
        console.error('Backend API error:', backendError);
      }

      // Fallback: Return basic user info from token
      const user = {
        id: payload.userId as string || walletAddress,
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
        user,
      });
    } catch (jwtError) {
      return NextResponse.json(
        { success: false, error: 'Invalid token' },
        { status: 401 }
      );
    }
  } catch (error) {
    console.error('Profile fetch error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to fetch profile' },
      { status: 500 }
    );
  }
}
