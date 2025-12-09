"""
DCMX Tracing Integration Example

Demonstrates how to integrate OpenTelemetry tracing into DCMX operations
for visualization in Jaeger.
"""

import asyncio
import logging
from typing import Optional

from dcmx.observability import (
    DCMXTracer,
    DCMXTracingConfig,
    traced,
    traced_method,
    start_span,
    record_counter,
    record_histogram,
)
from dcmx.blockchain.artist_nft_minter import ArtistNFTMinter


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@traced(operation_name="artist_onboarding_workflow")
async def artist_onboarding_workflow():
    """
    Example: Complete artist onboarding with tracing
    
    This demonstrates how tracing captures:
    - Multiple sequential operations
    - Operation timing and duration
    - Success/failure status
    - Operation attributes and context
    """

    with start_span("artist_onboarding") as span:
        span.set_attribute("workflow.type", "artist_onboarding")
        span.set_attribute("workflow.version", "1.0")

        # Step 1: Verify artist
        with start_span("verify_artist") as verify_span:
            verify_span.set_attribute("step", "1_verify")
            logger.info("Verifying artist identity...")
            await asyncio.sleep(0.1)  # Simulate work
            record_counter("artist.verification.attempts", 1)
            verify_span.set_attribute("artist.verified", True)

        # Step 2: Connect wallet
        with start_span("connect_wallet") as wallet_span:
            wallet_span.set_attribute("step", "2_connect_wallet")
            logger.info("Connecting wallet...")
            await asyncio.sleep(0.1)
            wallet_span.set_attribute("wallet.type", "metamask")
            wallet_span.set_attribute("wallet.connected", True)
            record_counter("wallet.connections.total", 1)

        # Step 3: Check KYC
        with start_span("check_kyc") as kyc_span:
            kyc_span.set_attribute("step", "3_check_kyc")
            logger.info("Checking KYC status...")
            await asyncio.sleep(0.1)
            kyc_span.set_attribute("kyc.status", "verified")
            kyc_span.set_attribute("kyc.level", 2)
            record_counter("kyc.verifications.total", 1)

        # Step 4: Award DCMX badge
        with start_span("award_dcmx_badge") as badge_span:
            badge_span.set_attribute("step", "4_award_badge")
            logger.info("Awarding DCMX verified badge...")
            await asyncio.sleep(0.05)
            badge_span.set_attribute("badge.awarded", True)
            badge_span.set_attribute("badge.type", "verified_artist")
            record_counter("badges.awarded.total", 1)

    logger.info("✅ Artist onboarding workflow completed with tracing")


@traced(operation_name="nft_minting_workflow")
async def nft_minting_workflow():
    """
    Example: NFT minting workflow with detailed tracing
    
    Shows how to trace:
    - Multi-step minting process
    - Watermark verification
    - Blockchain operations
    - Royalty calculations
    """

    with start_span("nft_minting_flow") as span:
        span.set_attribute("workflow.type", "nft_minting")
        span.set_attribute("track.title", "My Song")
        span.set_attribute("artist.id", "artist_123")

        # Step 1: Verify watermark
        with start_span("verify_watermark") as watermark_span:
            watermark_span.set_attribute("step", "1_verify_watermark")
            logger.info("Verifying watermark...")
            await asyncio.sleep(0.1)
            watermark_span.set_attribute("watermark.status", "valid")
            watermark_span.set_attribute("watermark.confidence", 0.98)
            record_counter("watermark.verifications.total", 1)
            record_histogram("watermark.confidence_score", 0.98)

        # Step 2: Verify ZK proof
        with start_span("verify_zk_proof") as proof_span:
            proof_span.set_attribute("step", "2_verify_zk_proof")
            logger.info("Verifying zero-knowledge proof...")
            await asyncio.sleep(0.15)
            proof_span.set_attribute("proof.valid", True)
            proof_span.set_attribute("proof.cascade_level", 3)
            record_counter("zk_proofs.verified.total", 1)

        # Step 3: Create NFT metadata
        with start_span("create_nft_metadata") as metadata_span:
            metadata_span.set_attribute("step", "3_create_metadata")
            logger.info("Creating NFT metadata...")
            await asyncio.sleep(0.05)
            metadata_span.set_attribute("metadata.size_bytes", 2048)
            metadata_span.set_attribute("metadata.format", "json")
            record_counter("nft.metadata.created.total", 1)

        # Step 4: Mint on blockchain
        with start_span("blockchain_mint") as mint_span:
            mint_span.set_attribute("step", "4_blockchain_mint")
            logger.info("Minting NFT on blockchain...")
            await asyncio.sleep(0.2)  # Simulate blockchain call
            mint_span.set_attribute("nft.token_id", "0x123abc")
            mint_span.set_attribute("nft.contract", "0xMusicNFT")
            mint_span.set_attribute("tx.hash", "0x456def")
            mint_span.set_attribute("tx.gas_used", 180000)
            record_counter("nft.mints.total", 1)
            record_histogram("nft.mint.gas_used", 180000)

        # Step 5: Calculate royalties
        with start_span("calculate_royalties") as royalty_span:
            royalty_span.set_attribute("step", "5_calculate_royalties")
            logger.info("Calculating royalty distribution...")
            await asyncio.sleep(0.08)
            royalty_span.set_attribute("royalty.platform_fee_bps", 250)
            royalty_span.set_attribute("royalty.artist_pct", 97.5)
            royalty_span.set_attribute("royalty.secondary_market_pct", 5.0)
            record_counter("royalties.calculated.total", 1)

    logger.info("✅ NFT minting workflow completed with tracing")


@traced(operation_name="secondary_market_detection")
async def secondary_market_detection():
    """
    Example: Secondary market sale detection and royalty distribution with tracing
    
    Demonstrates tracing for:
    - Marketplace detection
    - Sale verification
    - Royalty calculation and payment
    """

    with start_span("secondary_market_flow") as span:
        span.set_attribute("marketplace.name", "opensea")
        span.set_attribute("nft.token_id", "0x123abc")
        span.set_attribute("sale.price_eth", 2.5)

        # Step 1: Detect sale
        with start_span("detect_marketplace_sale") as detect_span:
            detect_span.set_attribute("step", "1_detect_sale")
            logger.info("Detecting marketplace sale...")
            await asyncio.sleep(0.1)
            detect_span.set_attribute("sale.detected", True)
            detect_span.set_attribute("marketplace.confirmed", True)
            record_counter("marketplace.sales.detected.total", 1)

        # Step 2: Verify NFT ownership
        with start_span("verify_nft_ownership") as verify_span:
            verify_span.set_attribute("step", "2_verify_ownership")
            logger.info("Verifying NFT ownership...")
            await asyncio.sleep(0.08)
            verify_span.set_attribute("ownership.verified", True)
            verify_span.set_attribute("owner.current", "0xbuyer")
            verify_span.set_attribute("owner.previous", "0xseller")
            record_counter("nft.ownership.verifications.total", 1)

        # Step 3: Calculate royalty
        with start_span("calculate_royalty") as calc_span:
            calc_span.set_attribute("step", "3_calculate_royalty")
            logger.info("Calculating royalty...")
            await asyncio.sleep(0.05)
            royalty_amount = 2.5 * 0.05  # 5% royalty
            calc_span.set_attribute("royalty.amount_eth", royalty_amount)
            calc_span.set_attribute("royalty.percentage", 5.0)
            record_histogram("royalty.payment_eth", royalty_amount)

        # Step 4: Distribute royalty
        with start_span("distribute_royalty") as dist_span:
            dist_span.set_attribute("step", "4_distribute_royalty")
            logger.info("Distributing royalty...")
            await asyncio.sleep(0.15)
            dist_span.set_attribute("royalty.recipient", "0xartist")
            dist_span.set_attribute("tx.hash", "0x789ghi")
            dist_span.set_attribute("tx.status", "confirmed")
            record_counter("royalties.distributed.total", 1)

    logger.info("✅ Secondary market workflow completed with tracing")


class TracedArtistNFTMinter:
    """
    Wrapper for ArtistNFTMinter with enhanced tracing
    """

    def __init__(self, rpc_url: str, private_key: str):
        self.rpc_url = rpc_url
        self.private_key = private_key
        self.minter = ArtistNFTMinter(
            rpc_url=rpc_url,
            private_key=private_key,
            music_nft_contract="0x" + "0" * 40,
            dcmx_token_contract="0x" + "1" * 40,
        )

    @traced_method(operation_name="traced_mint_nft", include_args=True)
    async def mint_with_tracing(self, artist_id: str, track_title: str):
        """Mint NFT with comprehensive tracing"""
        logger.info(f"Minting NFT for artist: {artist_id}")
        
        # Actual minting would happen here
        # For demo, we just trace the operation
        record_counter("traced_mint.attempts", 1)
        logger.info(f"✅ NFT mint traced for {track_title}")


async def run_examples():
    """Run all tracing examples"""

    # Initialize tracer
    config = DCMXTracingConfig(
        service_name="dcmx",
        service_version="1.0.0",
        otlp_endpoint="http://localhost:4318",
        enable_console=True,
    )
    tracer = DCMXTracer.init(config)

    print("\n" + "=" * 80)
    print("  DCMX Distributed Tracing Examples")
    print("=" * 80)
    print()

    # Run example workflows
    print("📝 Running artist onboarding workflow...")
    await artist_onboarding_workflow()
    await asyncio.sleep(0.5)

    print("\n📝 Running NFT minting workflow...")
    await nft_minting_workflow()
    await asyncio.sleep(0.5)

    print("\n📝 Running secondary market detection workflow...")
    await secondary_market_detection()
    await asyncio.sleep(0.5)

    print("\n📝 Running traced minter example...")
    minter = TracedArtistNFTMinter(
        rpc_url="http://localhost:8545",
        private_key="0x" + "0" * 64,
    )
    await minter.mint_with_tracing("artist_123", "My Awesome Song")

    print("\n" + "=" * 80)
    print("✅ All examples completed!")
    print("=" * 80)
    print()
    print("📊 View traces in Jaeger UI: http://localhost:16686")
    print()

    # Shutdown tracer
    await tracer.shutdown()


if __name__ == "__main__":
    asyncio.run(run_examples())
