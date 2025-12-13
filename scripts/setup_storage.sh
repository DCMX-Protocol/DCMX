#!/bin/bash
# Setup script for DCMX decentralized storage

set -e

echo "=================================================="
echo "DCMX Decentralized Storage Setup"
echo "=================================================="
echo

# Step 1: Check Python version
echo "Step 1: Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "  ✓ Python $python_version"
echo

# Step 2: Install dependencies
echo "Step 2: Installing Python dependencies..."
pip install -q boto3 botocore aiofiles aiohttp
echo "  ✓ Dependencies installed"
echo

# Step 3: Create .env file
echo "Step 3: Creating .env configuration..."
if [ ! -f .env ]; then
    cp .env.storage.example .env
    echo "  ✓ Created .env file (please fill in your API keys)"
else
    echo "  ℹ .env file already exists"
fi
echo

# Step 4: API Key Setup Instructions
echo "Step 4: Obtain API Keys"
echo "=================================================="
echo
echo "STORJ DCS (150GB free):"
echo "  1. Sign up: https://www.storj.io/signup"
echo "  2. Create an account and verify email"
echo "  3. Create Access Grant:"
echo "     - Dashboard → Access → Create S3 Credentials"
echo "     - Name: DCMX Music Storage"
echo "     - Permissions: All"
echo "  4. Save Access Key and Secret Key to .env"
echo
echo "WEB3.STORAGE (10GB free):"
echo "  1. Sign up: https://web3.storage"
echo "  2. Create account with email/GitHub"
echo "  3. Get API Token:"
echo "     - Account → API Tokens → Create Token"
echo "     - Name: DCMX IPFS Storage"
echo "  4. Save token to .env"
echo
echo "NFT.STORAGE (Unlimited free):"
echo "  1. Sign up: https://nft.storage"
echo "  2. Create account with email/GitHub"
echo "  3. Get API Token:"
echo "     - Account → API Keys → New Key"
echo "     - Name: DCMX NFT Metadata"
echo "  4. Save token to .env"
echo
echo "=================================================="
echo

# Step 5: Verify configuration
echo "Step 5: Verifying configuration..."
if grep -q "your_storj_access_key_here" .env 2>/dev/null; then
    echo "  ⚠ WARNING: .env still contains placeholder values"
    echo "  Please edit .env and add your real API keys"
else
    echo "  ✓ Configuration looks good"
fi
echo

# Step 6: Test connection
echo "Step 6: Test storage connection (optional)"
echo "  Run: python3 -c 'from dcmx.storage.decentralized_storage import DecentralizedStorageManager; import asyncio; asyncio.run(DecentralizedStorageManager.from_env().cleanup())'"
echo

# Complete
echo "=================================================="
echo "Setup Complete!"
echo "=================================================="
echo
echo "Next steps:"
echo "  1. Edit .env with your API keys"
echo "  2. Run: python examples/storage_upload_examples.py"
echo "  3. Upload your music library!"
echo
echo "For batch upload of 150+ songs:"
echo "  python -c 'from dcmx.storage.batch_uploader import upload_music_library; import asyncio; asyncio.run(upload_music_library(\"/path/to/music\"))'"
echo
