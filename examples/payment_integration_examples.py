"""
DCMX Payment Integration Examples

Demonstrates Magic Eden and Magic Internet Money (MIM) integration.
"""

import asyncio
from dcmx.payments.processor import UnifiedPaymentGateway, PaymentMethod
from dcmx.payments.magic_eden import MagicEdenChain
from dcmx.payments.magic_internet_money import MIMChain


async def example_magic_eden_listing():
    """Example: List a music NFT on Magic Eden."""
    
    # Initialize unified payment gateway
    gateway = UnifiedPaymentGateway()
    
    # Configure Magic Eden (use your API key)
    gateway.configure_magic_eden(
        api_key="your_magic_eden_api_key",
        chain="solana",  # or "ethereum", "polygon", "bitcoin"
        collection_symbol="dcmx_music",
    )
    
    # List an NFT
    result = await gateway.list_nft_on_magic_eden(
        nft_address="7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
        token_id="1",
        artist="Artist Name",
        track_title="My Amazing Song",
        price_usd=100.0,  # $100 USD
        seller_address="SellerWalletAddress123...",
        royalty_percentage=10.0,  # 10% artist royalty
        edition_number=1,
        max_editions=100,
    )
    
    print("NFT Listed on Magic Eden:")
    print(f"  Listing ID: {result['listing_id']}")
    print(f"  Price: {result['price']} {result['currency']}")
    print(f"  Chain: {result['chain']}")
    print(f"  Status: {result['status']}")
    
    # Get collection stats
    stats = await gateway.get_magic_eden_stats()
    print("\nCollection Stats:")
    print(f"  Floor Price: {stats['floor_price']}")
    print(f"  24h Volume: {stats['volume_24h']}")
    print(f"  Total Volume: {stats['total_volume']}")
    
    await gateway.cleanup()


async def example_mim_payment():
    """Example: Process MIM stablecoin payment."""
    
    # Initialize unified payment gateway
    gateway = UnifiedPaymentGateway()
    
    # Configure MIM (use your wallet details)
    gateway.configure_mim(
        chain="ethereum",  # or "avalanche", "arbitrum", "fantom", etc.
        merchant_address="0xYourMerchantWalletAddress...",
        # private_key="your_private_key_if_sending_payments",
    )
    
    # Get payment instructions for buyer
    instructions = gateway.get_mim_payment_instructions(
        amount_usd=50.0,  # $50 USD
        order_id="ORDER_12345",
    )
    
    print("MIM Payment Instructions:")
    print(f"  Amount: {instructions['amount_mim']} MIM (~${instructions['amount_usd']} USD)")
    print(f"  Send to: {instructions['recipient_address']}")
    print(f"  Chain: {instructions['chain']}")
    print(f"  MIM Contract: {instructions['mim_contract']}")
    print("\nInstructions:")
    for step in instructions['instructions']:
        print(f"  {step}")
    print("\nNotes:")
    for note in instructions['notes']:
        print(f"  - {note}")
    
    # Process NFT purchase with MIM
    payment_result = await gateway.process_payment(
        user_wallet="0xBuyerWalletAddress...",
        amount_usd=50.0,
        payment_method=PaymentMethod.CRYPTO_MIM,
        nft_id="NFT_789",
    )
    
    print("\nPayment Result:")
    print(f"  Success: {payment_result['success']}")
    if payment_result['success']:
        print(f"  NFT ID: {payment_result['nft_id']}")
        print(f"  Price: {payment_result['price_mim']} MIM")
        print(f"  Artist Royalty: {payment_result['artist_royalty']} MIM")
        print(f"  Platform Fee: {payment_result['platform_fee']} MIM")
        print(f"  Seller Proceeds: {payment_result['seller_proceeds']} MIM")
    
    await gateway.cleanup()


async def example_multi_chain_support():
    """Example: Multi-chain payment options."""
    
    print("DCMX Multi-Chain Payment Support\n")
    
    # Magic Eden chains
    print("Magic Eden NFT Marketplace:")
    for chain in MagicEdenChain:
        print(f"  - {chain.value}")
    
    # MIM stablecoin chains
    print("\nMagic Internet Money (MIM) Stablecoin:")
    for chain in MIMChain:
        print(f"  - {chain.value}")
    
    print("\nYou can accept payments on any of these chains!")


async def example_complete_nft_sale():
    """Example: Complete NFT sale workflow with Magic Eden and MIM."""
    
    # Step 1: List NFT on Magic Eden
    print("Step 1: Listing NFT on Magic Eden...")
    gateway = UnifiedPaymentGateway()
    
    gateway.configure_magic_eden(
        api_key="your_api_key",
        chain="solana",
    )
    
    listing_result = await gateway.list_nft_on_magic_eden(
        nft_address="NFTContractAddress",
        token_id="42",
        artist="DCMX Artist",
        track_title="Blockchain Symphony #1",
        price_usd=250.0,
        seller_address="SellerAddress",
        royalty_percentage=12.5,
        edition_number=1,
        max_editions=50,
    )
    
    print(f"✓ Listed on Magic Eden: {listing_result['listing_id']}\n")
    
    # Step 2: Accept MIM payment for direct sale (alternative to Magic Eden)
    print("Step 2: Alternative - Accept direct MIM payment...")
    gateway.configure_mim(
        chain="ethereum",
        merchant_address="0xMerchantAddress...",
    )
    
    # Buyer pays with MIM
    payment_result = await gateway.process_payment(
        user_wallet="0xBuyerAddress...",
        amount_usd=250.0,
        payment_method=PaymentMethod.CRYPTO_MIM,
        nft_id="NFT_42",
        artist="DCMX Artist",
        track_title="Blockchain Symphony #1",
    )
    
    if payment_result['success']:
        print("✓ Payment received in MIM stablecoin")
        print(f"  Artist receives: {payment_result['artist_royalty']} MIM")
        print(f"  Seller receives: {payment_result['seller_proceeds']} MIM")
        print(f"  Platform fee: {payment_result['platform_fee']} MIM")
    
    await gateway.cleanup()
    print("\n✓ NFT sale complete!")


async def example_royalty_distribution():
    """Example: Artist royalty distribution with MIM."""
    
    from dcmx.payments.magic_internet_money import MIMPaymentProcessor, MIMChain
    from decimal import Decimal
    
    # Initialize MIM processor
    processor = MIMPaymentProcessor(
        chain=MIMChain.ETHEREUM,
        private_key="your_private_key",  # For sending royalties
    )
    
    # Secondary sale occurs on Magic Eden
    sale_price_usd = 500.0  # NFT sold for $500
    artist_royalty_percentage = 10.0  # 10% royalty
    
    # Calculate royalty in MIM (1 MIM = 1 USD)
    royalty_mim = processor.convert_usd_to_mim(
        sale_price_usd * (artist_royalty_percentage / 100)
    )
    
    print(f"Secondary Sale: ${sale_price_usd}")
    print(f"Artist Royalty: {royalty_mim} MIM (${sale_price_usd * 0.1})")
    
    # Send royalty to artist
    artist_wallet = "0xArtistWalletAddress..."
    
    # Check balance first
    processor_balance = processor.get_balance(processor.account.address if processor.account else "")
    print(f"\nProcessor MIM Balance: {processor_balance} MIM")
    
    if processor_balance >= royalty_mim:
        # Send royalty payment
        tx_hash = processor.send_payment(
            to_address=artist_wallet,
            amount_mim=royalty_mim,
        )
        
        print(f"✓ Royalty sent to artist: {tx_hash}")
        print(f"  Amount: {royalty_mim} MIM")
        print(f"  Chain: {processor.chain.value}")
    else:
        print(f"⚠ Insufficient balance to send royalty")


if __name__ == "__main__":
    print("=" * 60)
    print("DCMX Payment Integration Examples")
    print("Magic Eden + Magic Internet Money (MIM)")
    print("=" * 60)
    print()
    
    # Run examples (comment out the ones you don't need)
    
    # Show multi-chain support
    asyncio.run(example_multi_chain_support())
    print()
    
    # Uncomment to run other examples:
    
    # asyncio.run(example_magic_eden_listing())
    # asyncio.run(example_mim_payment())
    # asyncio.run(example_complete_nft_sale())
    # asyncio.run(example_royalty_distribution())
    
    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)
