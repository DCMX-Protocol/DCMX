"""
Tests for OFAC SDN List Checker

Tests:
- Bloom filter functionality
- SDN list loading and caching
- Wallet address checking
- Name fuzzy matching
- Network error handling with cache fallback
"""

import pytest
import tempfile
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from dcmx.compliance.ofac_checker import (
    OFACChecker,
    BloomFilter,
    SDNEntry,
)


class TestBloomFilter:
    """Test bloom filter for O(1) lookups."""

    def test_create_bloom_filter(self):
        """Test creating bloom filter."""
        bf = BloomFilter(size=1000, hash_count=5)
        assert bf.size == 1000
        assert bf.hash_count == 5
        assert len(bf.bit_array) == 1000

    def test_add_and_check(self):
        """Test adding items and checking membership."""
        bf = BloomFilter(size=10000, hash_count=7)
        
        bf.add("0x1234567890abcdef")
        bf.add("0xdeadbeefcafe1234")
        
        assert bf.might_contain("0x1234567890abcdef") is True
        assert bf.might_contain("0xdeadbeefcafe1234") is True

    def test_definitely_not_present(self):
        """Test that missing items return False."""
        bf = BloomFilter(size=10000, hash_count=7)
        
        bf.add("0x1234567890abcdef")
        
        assert bf.might_contain("0xnotinfilter12345") is False

    def test_case_insensitive(self):
        """Test case insensitive matching."""
        bf = BloomFilter()
        
        bf.add("0xABCDEF")
        
        assert bf.might_contain("0xabcdef") is True
        assert bf.might_contain("0xABCDEF") is True

    def test_clear(self):
        """Test clearing bloom filter."""
        bf = BloomFilter(size=1000)
        bf.add("test")
        assert bf.might_contain("test") is True
        
        bf.clear()
        assert bf.might_contain("test") is False


class TestSDNEntry:
    """Test SDN entry dataclass."""

    def test_create_sdn_entry(self):
        """Test creating SDN entry."""
        entry = SDNEntry(
            uid="12345",
            name="Test Entity",
            entry_type="Entity",
            programs=["CYBER2"],
            crypto_addresses=["0x1234abcd"]
        )
        
        assert entry.uid == "12345"
        assert entry.name == "Test Entity"
        assert "0x1234abcd" in entry.crypto_addresses

    def test_default_values(self):
        """Test SDN entry default values."""
        entry = SDNEntry(uid="1", name="Test", entry_type="Individual")
        
        assert entry.programs == []
        assert entry.aliases == []
        assert entry.addresses == []
        assert entry.crypto_addresses == []


class TestOFACChecker:
    """Test OFAC checker functionality."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def checker(self, temp_cache_dir):
        """Create OFAC checker with temp cache."""
        return OFACChecker(cache_dir=temp_cache_dir)

    def test_initialization(self, checker):
        """Test checker initialization."""
        assert checker.sdn_entries == {}
        assert checker.crypto_addresses == set()
        assert checker.last_update is None

    @pytest.mark.asyncio
    async def test_check_address_not_sanctioned(self, checker):
        """Test checking clean address."""
        checker.crypto_addresses = {"0xsanctioned123"}
        checker._build_indexes()
        
        result = await checker.check_address("0xcleanaddress456")
        assert result is False

    @pytest.mark.asyncio
    async def test_check_address_sanctioned(self, checker):
        """Test checking sanctioned address."""
        checker.crypto_addresses = {"0xsanctioned123"}
        checker._build_indexes()
        
        result = await checker.check_address("0xsanctioned123")
        assert result is True

    @pytest.mark.asyncio
    async def test_check_address_case_insensitive(self, checker):
        """Test case insensitive address checking."""
        checker.crypto_addresses = {"0xabcdef123456"}
        checker._build_indexes()
        
        result = await checker.check_address("0xABCDEF123456")
        assert result is True

    @pytest.mark.asyncio
    async def test_check_address_empty(self, checker):
        """Test checking empty address."""
        result = await checker.check_address("")
        assert result is False
        
        result = await checker.check_address(None)
        assert result is False

    @pytest.mark.asyncio
    async def test_check_address_caching(self, checker):
        """Test that address checks are cached."""
        checker.crypto_addresses = {"0xtest123"}
        checker._build_indexes()
        
        await checker.check_address("0xtest123")
        assert "0xtest123" in checker.entity_cache
        assert checker.entity_cache["0xtest123"] is True

    @pytest.mark.asyncio
    async def test_check_name_exact_match(self, checker):
        """Test exact name matching."""
        checker.sdn_entries = {
            "123": SDNEntry(uid="123", name="Bad Actor Corp", entry_type="Entity")
        }
        checker._build_indexes()
        
        result = await checker.check_name("Bad Actor Corp")
        assert result["blocked"] is True
        assert result["score"] == 1.0

    @pytest.mark.asyncio
    async def test_check_name_fuzzy_match(self, checker):
        """Test fuzzy name matching."""
        checker.sdn_entries = {
            "123": SDNEntry(uid="123", name="Bad Actor Corp", entry_type="Entity")
        }
        checker._build_indexes()
        
        # Fuzzy match: small typo/variation (within threshold)
        result = await checker.check_name("Bad Acctor Corp", fuzzy_threshold=0.7)
        assert result["blocked"] is True
        assert result["score"] >= 0.7

    @pytest.mark.asyncio
    async def test_check_name_no_match(self, checker):
        """Test name with no match."""
        checker.sdn_entries = {
            "123": SDNEntry(uid="123", name="Evil Corp", entry_type="Entity")
        }
        checker._build_indexes()
        
        result = await checker.check_name("Good Company Inc")
        assert result["blocked"] is False

    @pytest.mark.asyncio
    async def test_check_name_empty(self, checker):
        """Test checking empty name."""
        result = await checker.check_name("")
        assert result["blocked"] is False
        assert result["matches"] == []

    @pytest.mark.asyncio
    async def test_check_entity(self, checker):
        """Test check_entity wrapper."""
        checker.sdn_entries = {
            "123": SDNEntry(uid="123", name="Sanctioned Entity", entry_type="Entity")
        }
        checker._build_indexes()
        
        result = await checker.check_entity("Sanctioned Entity")
        assert result is True

    @pytest.mark.asyncio
    async def test_is_list_stale_no_update(self, checker):
        """Test stale check with no update."""
        assert await checker.is_list_stale() is True

    @pytest.mark.asyncio
    async def test_is_list_stale_fresh(self, checker):
        """Test stale check with fresh data."""
        checker.last_update = datetime.now()
        assert await checker.is_list_stale() is False

    @pytest.mark.asyncio
    async def test_is_list_stale_old(self, checker):
        """Test stale check with old data."""
        checker.last_update = datetime.now() - timedelta(days=10)
        assert await checker.is_list_stale() is True

    def test_fuzzy_similarity_exact(self, checker):
        """Test fuzzy similarity with exact match."""
        score = checker._fuzzy_similarity("test string", "test string")
        assert score == 1.0

    def test_fuzzy_similarity_similar(self, checker):
        """Test fuzzy similarity with similar strings."""
        score = checker._fuzzy_similarity("test string", "test strng")
        assert 0.8 < score < 1.0

    def test_fuzzy_similarity_different(self, checker):
        """Test fuzzy similarity with different strings."""
        score = checker._fuzzy_similarity("hello world", "xyz abc")
        assert score < 0.5

    def test_fuzzy_similarity_empty(self, checker):
        """Test fuzzy similarity with empty strings."""
        assert checker._fuzzy_similarity("", "test") == 0.0
        assert checker._fuzzy_similarity("test", "") == 0.0

    def test_normalize_name(self, checker):
        """Test name normalization."""
        assert checker._normalize_name("  John  DOE  ") == "john doe"
        assert checker._normalize_name("O'Brien, Inc.") == "obrien inc"
        assert checker._normalize_name("Test-Corp!") == "testcorp"

    def test_extract_crypto_addresses(self, checker):
        """Test extracting crypto addresses from remarks."""
        remarks = "Digital Currency Address - ETH 0x1234567890abcdef1234567890abcdef12345678;"
        addresses = checker._extract_crypto_addresses(remarks)
        assert "0x1234567890abcdef1234567890abcdef12345678" in addresses

    def test_extract_btc_addresses(self, checker):
        """Test extracting Bitcoin addresses."""
        remarks = "Digital Currency Address - BTC 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa;"
        addresses = checker._extract_crypto_addresses(remarks)
        assert "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa" in addresses

    @pytest.mark.asyncio
    async def test_cache_save_and_load(self, checker, temp_cache_dir):
        """Test saving and loading cache."""
        checker.sdn_entries = {
            "123": SDNEntry(
                uid="123",
                name="Test Entity",
                entry_type="Entity",
                crypto_addresses=["0xtest123"]
            )
        }
        checker.crypto_addresses = {"0xtest123"}
        checker.last_update = datetime.now()
        
        await checker._save_to_cache()
        
        new_checker = OFACChecker(cache_dir=temp_cache_dir)
        result = await new_checker._load_from_cache()
        
        assert result is True
        assert "123" in new_checker.sdn_entries
        assert "0xtest123" in new_checker.crypto_addresses

    @pytest.mark.asyncio
    async def test_cache_expiry(self, checker, temp_cache_dir):
        """Test cache expiry detection."""
        checker.sdn_entries = {"1": SDNEntry(uid="1", name="Test", entry_type="Entity")}
        checker.last_update = datetime.now() - timedelta(days=10)
        await checker._save_to_cache()
        
        new_checker = OFACChecker(cache_dir=temp_cache_dir)
        result = await new_checker._load_from_cache(ignore_expiry=False)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_cache_fallback_on_network_error(self, checker, temp_cache_dir):
        """Test fallback to stale cache on network error."""
        checker.sdn_entries = {"1": SDNEntry(uid="1", name="Cached", entry_type="Entity")}
        checker.crypto_addresses = {"0xcached"}
        checker.last_update = datetime.now() - timedelta(days=10)
        await checker._save_to_cache()
        
        new_checker = OFACChecker(cache_dir=temp_cache_dir)
        
        with patch.object(new_checker, '_download_and_parse_sdn', 
                         side_effect=Exception("Network error")):
            await new_checker.load_sdn_list()
        
        assert "1" in new_checker.sdn_entries
        assert "0xcached" in new_checker.crypto_addresses

    def test_get_stats(self, checker):
        """Test getting statistics."""
        checker.sdn_entries = {"1": SDNEntry(uid="1", name="Test", entry_type="Entity")}
        checker.crypto_addresses = {"0x1", "0x2"}
        checker.entity_cache = {"0x1": True}
        checker.last_update = datetime.now()
        
        stats = checker.get_stats()
        
        assert stats["total_entries"] == 1
        assert stats["crypto_addresses"] == 2
        assert stats["cached_lookups"] == 1
        assert stats["last_update"] is not None

    @pytest.mark.asyncio
    async def test_refresh_if_stale(self, checker):
        """Test refresh_if_stale method."""
        checker.last_update = datetime.now()
        
        with patch.object(checker, 'load_sdn_list', new_callable=AsyncMock) as mock_load:
            result = await checker.refresh_if_stale()
            assert result is False
            mock_load.assert_not_called()

    @pytest.mark.asyncio
    async def test_refresh_if_stale_when_stale(self, checker):
        """Test refresh_if_stale when list is stale."""
        checker.last_update = datetime.now() - timedelta(days=10)
        
        with patch.object(checker, 'load_sdn_list', new_callable=AsyncMock) as mock_load:
            result = await checker.refresh_if_stale()
            assert result is True
            mock_load.assert_called_once()


class TestOFACCheckerIntegration:
    """Integration tests for OFAC checker."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.mark.asyncio
    async def test_full_workflow(self, temp_cache_dir):
        """Test complete OFAC checking workflow."""
        checker = OFACChecker(cache_dir=temp_cache_dir)
        
        mock_sdn_csv = '''12345,"EVIL CORP","Entity","CYBER2","","","","","","","",""
67890,"BAD ACTOR","Individual","SDGT","","","","","","","","Digital Currency Address - ETH 0x1234567890123456789012345678901234567890;"'''
        mock_add_csv = '''12345,1,"123 Evil Street","City","Country",""'''
        
        with patch.object(checker, '_fetch_csv', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = [mock_sdn_csv, mock_add_csv]
            await checker.load_sdn_list(force_refresh=True)
        
        assert len(checker.sdn_entries) == 2
        
        result = await checker.check_address("0x1234567890123456789012345678901234567890")
        assert result is True
        
        result = await checker.check_address("0xcleanaddress12345678901234567890123456")
        assert result is False
        
        result = await checker.check_name("Evil Corp")
        assert result["blocked"] is True
        
        result = await checker.check_name("Good Company")
        assert result["blocked"] is False
