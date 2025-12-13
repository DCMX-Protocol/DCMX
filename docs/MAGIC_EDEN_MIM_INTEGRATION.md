# Magic Eden and Magic Internet Money Integration

This guide explains how to use Magic Eden marketplace and MIM stablecoin payments in DCMX.

## Table of Contents

1. [Magic Eden NFT Marketplace](#magic-eden)
2. [Magic Internet Money (MIM) Stablecoin](#mim-stablecoin)
3. [Configuration](#configuration)
4. [Usage Examples](#usage-examples)
5. [Multi-Chain Support](#multi-chain-support)

---

## Magic Eden NFT Marketplace

Magic Eden is a leading NFT marketplace supporting multiple blockchains.

### Features

- **Cross-chain support**: Solana, Ethereum, Polygon, Bitcoin
- **Artist royalties**: Automatic enforcement on secondary sales
- **Collection analytics**: Track floor price, volume, sales
- **Limited editions**: Support for numbered editions

### Supported Chains

- Solana (primary)
- Ethereum
- Polygon
- Bitcoin (Ordinals)

### Integration

```python
from dcmx.payments.processor import UnifiedPaymentGateway

# Initialize gateway
gateway = UnifiedPaymentGateway()

# Configure Magic Eden
gateway.configure_magic_eden(
    api_key="your_magic_eden_api_key",
    chain="solana",
    collection_symbol="dcmx_music",
)

# List NFT
result = await gateway.list_nft_on_magic_eden(
    nft_address="NFT_CONTRACT_ADDRESS",
    token_id="1",
    artist="Artist Name",
    track_title="Song Title",
    price_usd=100.0,
    seller_address="SELLER_WALLET",
    royalty_percentage=10.0,
    edition_number=1,
    max_editions=100,
)
```

### API Key

Get your Magic Eden API key:
1. Visit https://magiceden.io/developers
2. Create developer account
3. Generate API key
4. Set in environment: `MAGIC_EDEN_API_KEY`

---

## MIM Stablecoin

Magic Internet Money (MIM) is a USD-pegged stablecoin by Abracadabra.money.

### Features

- **USD-pegged**: 1 MIM ≈ 1 USD
- **Multi-chain**: Ethereum, Avalanche, Arbitrum, Fantom, BSC, Polygon, Optimism
- **Low fees**: Especially on L2s (Arbitrum, Optimism)
- **DeFi integration**: Used across many DeFi protocols

### Supported Chains

- Ethereum (mainnet)
- Avalanche
- Arbitrum (L2, low fees)
- Fantom
- Binance Smart Chain
- Polygon
- Optimism (L2, low fees)

### Integration

```python
from dcmx.payments.processor import UnifiedPaymentGateway, PaymentMethod

# Initialize gateway
gateway = UnifiedPaymentGateway()

# Configure MIM
gateway.configure_mim(
    chain="ethereum",
    merchant_address="0xYOUR_WALLET_ADDRESS",
)

# Get payment instructions for buyer
instructions = gateway.get_mim_payment_instructions(
    amount_usd=50.0,
    order_id="ORDER_123",
)

# Process payment
result = await gateway.process_payment(
    user_wallet="0xBUYER_WALLET",
    amount_usd=50.0,
    payment_method=PaymentMethod.CRYPTO_MIM,
    nft_id="NFT_ID",
)
```

---

## Configuration

### Environment Variables

```bash
# Magic Eden
export MAGIC_EDEN_API_KEY="your_api_key_here"
export MAGIC_EDEN_CHAIN="solana"  # or ethereum, polygon, bitcoin
export DCMX_COLLECTION_SYMBOL="dcmx_music"

# MIM Stablecoin
export MIM_CHAIN="ethereum"  # or avalanche, arbitrum, fantom, etc.
export MIM_MERCHANT_WALLET="0xYourMerchantWalletAddress"
export MIM_PRIVATE_KEY="your_private_key_for_sending_payments"  # Optional
```

### Python Configuration

```python
import os
from dcmx.payments.processor import UnifiedPaymentGateway

gateway = UnifiedPaymentGateway()

# Configure from environment variables
gateway.configure_magic_eden(
    api_key=os.getenv("MAGIC_EDEN_API_KEY"),
    chain=os.getenv("MAGIC_EDEN_CHAIN", "solana"),
    collection_symbol=os.getenv("DCMX_COLLECTION_SYMBOL", "dcmx_music"),
)

gateway.configure_mim(
    chain=os.getenv("MIM_CHAIN", "ethereum"),
    merchant_address=os.getenv("MIM_MERCHANT_WALLET"),
    private_key=os.getenv("MIM_PRIVATE_KEY"),  # Optional
)
```

---

## Usage Examples

### Example 1: List Music NFT on Magic Eden

```python
async def list_music_nft():
    gateway = UnifiedPaymentGateway()
    gateway.configure_magic_eden(
        api_key="your_api_key",
        chain="solana",
    )
    
    result = await gateway.list_nft_on_magic_eden(
        nft_address="7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
        token_id="1",
        artist="DCMX Artist",
        track_title="Blockchain Beats Vol. 1",
        price_usd=75.0,
        seller_address="YourSolanaWalletAddress",
        royalty_percentage=10.0,
        edition_number=1,
        max_editions=100,
    )
    
    print(f"Listed: {result['listing_id']}")
```

### Example 2: Accept MIM Payment

```python
async def accept_mim_payment():
    gateway = UnifiedPaymentGateway()
    gateway.configure_mim(
        chain="arbitrum",  # Low fees!
        merchant_address="0xYourWallet",
    )
    
    # Process payment
    result = await gateway.process_payment(
        user_wallet="0xBuyerWallet",
        amount_usd=75.0,
        payment_method=PaymentMethod.CRYPTO_MIM,
        nft_id="NFT_123",
    )
    
    if result['success']:
        print(f"Payment received: {result['price_mim']} MIM")
        print(f"Artist royalty: {result['artist_royalty']} MIM")
```

### Example 3: Check Collection Stats

```python
async def check_stats():
    gateway = UnifiedPaymentGateway()
    gateway.configure_magic_eden(
        api_key="your_api_key",
        chain="solana",
    )
    
    stats = await gateway.get_magic_eden_stats()
    
    print(f"Floor Price: {stats['floor_price']} SOL")
    print(f"24h Volume: {stats['volume_24h']} SOL")
    print(f"Total Volume: {stats['total_volume']} SOL")
```

### Example 4: Send MIM Royalty to Artist

```python
from dcmx.payments.magic_internet_money import MIMPaymentProcessor, MIMChain
from decimal import Decimal

async def send_royalty():
    processor = MIMPaymentProcessor(
        chain=MIMChain.ETHEREUM,
        private_key="your_private_key",
    )
    
    # Secondary sale royalty
    royalty_amount = Decimal("10.0")  # 10 MIM
    artist_wallet = "0xArtistWallet"
    
    tx_hash = processor.send_payment(
        to_address=artist_wallet,
        amount_mim=royalty_amount,
    )
    
    print(f"Royalty sent: {tx_hash}")
```

---

## Multi-Chain Support

### Magic Eden Chains

| Chain | Best For | Fees |
|-------|----------|------|
| **Solana** | High-speed NFTs | Very Low |
| **Ethereum** | Largest market | High |
| **Polygon** | Low-cost NFTs | Low |
| **Bitcoin** | Ordinals/Inscriptions | Medium |

### MIM Stablecoin Chains

| Chain | Best For | Fees | Speed |
|-------|----------|------|-------|
| **Ethereum** | Maximum security | High | Medium |
| **Arbitrum** | Low-cost payments | Very Low | Fast |
| **Optimism** | Low-cost payments | Very Low | Fast |
| **Avalanche** | Fast finality | Low | Very Fast |
| **Polygon** | Cheap transactions | Very Low | Fast |
| **Fantom** | Low fees | Very Low | Fast |
| **BSC** | Alternative to ETH | Low | Fast |

### Recommended Setup

**For NFT Marketplace (Magic Eden):**
- Primary: Solana (low fees, fast)
- Secondary: Polygon (Ethereum compatibility, low fees)

**For Payments (MIM):**
- Primary: Arbitrum (L2, very low fees, Ethereum security)
- Secondary: Polygon (cheap, fast, wide adoption)

---

## Payment Flow

### Scenario 1: Direct Sale with MIM

```
1. Artist lists NFT → DCMX database
2. Buyer selects MIM payment → Get payment instructions
3. Buyer sends MIM → Merchant wallet
4. System verifies transaction → Blockchain check
5. NFT transferred to buyer → Smart contract
6. Artist royalty calculated → 10% of sale
7. Platform fee deducted → 2.5% fee
```

### Scenario 2: Magic Eden Marketplace

```
1. Artist lists NFT → Magic Eden API
2. NFT appears on Magic Eden → Public listing
3. Buyer purchases → Magic Eden handles payment
4. Magic Eden transfers NFT → Automatic
5. Artist receives royalty → Automatic (via smart contract)
6. Sale appears in DCMX → Webhook notification
```

---

## API Reference

### UnifiedPaymentGateway

```python
class UnifiedPaymentGateway:
    def configure_magic_eden(api_key, chain, collection_symbol)
    def configure_mim(chain, private_key, merchant_address)
    async def process_payment(user_wallet, amount_usd, payment_method, ...)
    async def list_nft_on_magic_eden(nft_address, token_id, artist, ...)
    def get_mim_payment_instructions(amount_usd, order_id)
    async def get_magic_eden_stats()
```

### MIMPaymentProcessor

```python
class MIMPaymentProcessor:
    def get_balance(address) -> Decimal
    def convert_usd_to_mim(usd_amount) -> Decimal
    def send_payment(to_address, amount_mim) -> str
    def verify_payment(tx_hash, expected_amount, expected_recipient) -> bool
    def estimate_gas_cost(to_address, amount_mim) -> Dict
```

### DCMXMagicEdenIntegration

```python
class DCMXMagicEdenIntegration:
    async def list_music_nft(nft_address, token_id, artist, track_title, ...)
    async def get_collection_floor_price() -> float
    async def get_collection_volume() -> Dict
```

---

## Security Notes

### API Keys
- Store Magic Eden API key in environment variables
- Never commit API keys to version control
- Rotate keys periodically

### Private Keys
- Use separate wallet for automated payments
- Keep minimal balance in hot wallet
- Store private keys in secure vault (AWS Secrets Manager, etc.)
- Use hardware wallet for large amounts

### Payment Verification
- Always verify MIM transactions on-chain
- Check transaction status before transferring NFT
- Implement webhook validation for Magic Eden
- Set up monitoring for failed transactions

---

## Troubleshooting

### Magic Eden Issues

**Problem**: "Listing failed: Invalid API key"
**Solution**: Verify API key is correct and not expired

**Problem**: "NFT not appearing on marketplace"
**Solution**: Check collection is verified on Magic Eden

### MIM Payment Issues

**Problem**: "Insufficient balance"
**Solution**: Buyer needs to acquire MIM tokens on the specified chain

**Problem**: "Transaction failed"
**Solution**: Check gas price, wallet balance, and MIM contract address

**Problem**: "Wrong chain"
**Solution**: Ensure buyer is on same chain as configured (Ethereum, Arbitrum, etc.)

---

## Support

- Magic Eden: https://docs.magiceden.io/
- MIM (Abracadabra): https://docs.abracadabra.money/
- DCMX GitHub: https://github.com/DCMX-Protocol/DCMX

---

## License

DCMX Payment Integration - MIT License
