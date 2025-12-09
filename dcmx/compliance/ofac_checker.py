"""OFAC sanctions checking for DCMX compliance."""

import logging
import hashlib
import json
import os
from typing import Set, Optional, List, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path
import aiohttp
import asyncio

logger = logging.getLogger(__name__)


class BloomFilter:
    """
    Simple bloom filter for O(1) membership checking.
    
    Used for fast preliminary OFAC lookups before exact matching.
    """
    
    def __init__(self, size: int = 100000, hash_count: int = 7):
        """
        Initialize bloom filter.
        
        Args:
            size: Number of bits in the filter
            hash_count: Number of hash functions to use
        """
        self.size = size
        self.hash_count = hash_count
        self.bit_array = [False] * size
    
    def _hashes(self, item: str) -> List[int]:
        """Generate multiple hash values for an item."""
        hashes = []
        for i in range(self.hash_count):
            h = hashlib.sha256(f"{item}{i}".encode()).hexdigest()
            hashes.append(int(h, 16) % self.size)
        return hashes
    
    def add(self, item: str) -> None:
        """Add an item to the bloom filter."""
        for h in self._hashes(item.lower()):
            self.bit_array[h] = True
    
    def might_contain(self, item: str) -> bool:
        """
        Check if item might be in the filter.
        
        Returns:
            True if item might be present (may have false positives)
            False if item is definitely not present
        """
        return all(self.bit_array[h] for h in self._hashes(item.lower()))
    
    def clear(self) -> None:
        """Clear all entries from the filter."""
        self.bit_array = [False] * self.size


@dataclass
class SDNEntry:
    """Represents an entry from the OFAC SDN list."""
    uid: str
    name: str
    entry_type: str  # Individual, Entity, Vessel, Aircraft
    programs: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    addresses: List[str] = field(default_factory=list)
    ids: List[str] = field(default_factory=list)  # Passport, Tax ID, etc.
    crypto_addresses: List[str] = field(default_factory=list)


class OFACChecker:
    """
    Checks wallet addresses and users against OFAC sanctions list.

    Maintains Specially Designated Nationals (SDN) list from US Treasury.
    Updates weekly and blocks transactions to/from sanctioned entities.
    """

    SDN_CSV_URL = "https://www.treasury.gov/ofac/downloads/sdn.csv"
    SDN_ADD_URL = "https://www.treasury.gov/ofac/downloads/add.csv"
    CONS_CSV_URL = "https://www.treasury.gov/ofac/downloads/consolidated/cons_prim.csv"
    
    CACHE_DIR = Path.home() / ".dcmx" / "compliance"
    CACHE_FILE = CACHE_DIR / "sdn_cache.json"
    CACHE_MAX_AGE_DAYS = 7

    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize OFAC checker."""
        self.sdn_entries: Dict[str, SDNEntry] = {}
        self.crypto_addresses: Set[str] = set()
        self.names_index: Dict[str, List[str]] = {}  # normalized name -> UIDs
        self.entity_cache: Dict[str, bool] = {}
        self.last_update: Optional[datetime] = None
        
        self.bloom_filter = BloomFilter(size=100000, hash_count=7)
        
        if cache_dir:
            self.CACHE_DIR = Path(cache_dir)
            self.CACHE_FILE = self.CACHE_DIR / "sdn_cache.json"

        logger.info("OFACChecker initialized")

    async def load_sdn_list(self, force_refresh: bool = False) -> None:
        """
        Load latest OFAC SDN list from Treasury.

        Downloads and parses the Specially Designated Nationals list.
        Uses cached version if available and not stale.
        
        Args:
            force_refresh: Force download even if cache is valid
        """
        try:
            if not force_refresh and await self._load_from_cache():
                logger.info(f"Loaded OFAC SDN list from cache: {len(self.sdn_entries)} entries")
                return
            
            await self._download_and_parse_sdn()
            await self._save_to_cache()
            
            self.last_update = datetime.now()
            logger.info(f"Loaded OFAC SDN list: {len(self.sdn_entries)} entries, "
                       f"{len(self.crypto_addresses)} crypto addresses")
        except Exception as e:
            logger.error(f"Failed to load OFAC list: {e}")
            if await self._load_from_cache(ignore_expiry=True):
                logger.warning("Using stale cache as fallback")
            else:
                raise RuntimeError(f"Cannot load OFAC list and no cache available: {e}")

    async def _download_and_parse_sdn(self) -> None:
        """Download and parse SDN list from Treasury."""
        timeout = aiohttp.ClientTimeout(total=60)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            sdn_data = await self._fetch_csv(session, self.SDN_CSV_URL)
            add_data = await self._fetch_csv(session, self.SDN_ADD_URL)
        
        self._parse_sdn_csv(sdn_data, add_data)
        self._build_indexes()

    async def _fetch_csv(self, session: aiohttp.ClientSession, url: str) -> str:
        """Fetch CSV data from URL with error handling."""
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"Failed to fetch {url}: HTTP {response.status}")
                    return ""
        except aiohttp.ClientError as e:
            logger.warning(f"Network error fetching {url}: {e}")
            return ""

    def _parse_sdn_csv(self, sdn_csv: str, add_csv: str) -> None:
        """
        Parse SDN CSV files.
        
        SDN.CSV format (pipe-delimited):
        ent_num, SDN_Name, SDN_Type, Program, Title, Call_Sign, Vess_type, Tonnage, GRT, 
        Vess_flag, Vess_owner, Remarks
        
        ADD.CSV format:
        ent_num, Add_num, Address, City/State/Province/Postal Code, Country, Add_remarks
        """
        self.sdn_entries.clear()
        self.crypto_addresses.clear()
        
        entries_by_id: Dict[str, SDNEntry] = {}
        
        for line in sdn_csv.strip().split('\n'):
            if not line.strip():
                continue
            
            parts = line.split('"')
            if len(parts) >= 3:
                fields = []
                in_quotes = False
                current = ""
                for char in line:
                    if char == '"':
                        in_quotes = not in_quotes
                    elif char == ',' and not in_quotes:
                        fields.append(current.strip())
                        current = ""
                    else:
                        current += char
                fields.append(current.strip())
            else:
                fields = [f.strip().strip('"') for f in line.split(',')]
            
            if len(fields) < 4:
                continue
            
            ent_num = fields[0].strip()
            name = fields[1].strip() if len(fields) > 1 else ""
            sdn_type = fields[2].strip() if len(fields) > 2 else ""
            program = fields[3].strip() if len(fields) > 3 else ""
            remarks = fields[-1] if len(fields) > 4 else ""
            
            if not ent_num or not name:
                continue
            
            crypto_addrs = self._extract_crypto_addresses(remarks)
            
            entry = SDNEntry(
                uid=ent_num,
                name=name,
                entry_type=sdn_type,
                programs=[program] if program else [],
                crypto_addresses=crypto_addrs
            )
            
            entries_by_id[ent_num] = entry
            self.crypto_addresses.update(addr.lower() for addr in crypto_addrs)
        
        for line in add_csv.strip().split('\n'):
            if not line.strip():
                continue
            
            fields = [f.strip().strip('"') for f in line.split(',')]
            if len(fields) < 2:
                continue
            
            ent_num = fields[0].strip()
            if ent_num in entries_by_id:
                address = ', '.join(f for f in fields[2:5] if f.strip())
                if address:
                    entries_by_id[ent_num].addresses.append(address)
        
        self.sdn_entries = entries_by_id

    def _extract_crypto_addresses(self, remarks: str) -> List[str]:
        """Extract cryptocurrency addresses from SDN remarks field."""
        addresses = []
        
        import re
        eth_pattern = r'0x[a-fA-F0-9]{40}'
        btc_pattern = r'[13][a-km-zA-HJ-NP-Z1-9]{25,34}'
        btc_bech32_pattern = r'bc1[a-zA-HJ-NP-Z0-9]{39,59}'
        
        addresses.extend(re.findall(eth_pattern, remarks))
        addresses.extend(re.findall(btc_pattern, remarks))
        addresses.extend(re.findall(btc_bech32_pattern, remarks))
        
        if "Digital Currency Address" in remarks or "alt. Digital Currency Address" in remarks:
            parts = remarks.split(';')
            for part in parts:
                if "Digital Currency Address" in part:
                    addr_parts = part.split()
                    for ap in addr_parts:
                        ap = ap.strip('();,')
                        if len(ap) > 20 and ap.isalnum():
                            addresses.append(ap)
        
        return list(set(addresses))

    def _build_indexes(self) -> None:
        """Build search indexes for fast lookup."""
        self.bloom_filter.clear()
        self.names_index.clear()

        # Add all addresses from crypto_addresses set to bloom filter
        for addr in self.crypto_addresses:
            self.bloom_filter.add(addr.lower())

        for uid, entry in self.sdn_entries.items():
            for addr in entry.crypto_addresses:
                self.bloom_filter.add(addr.lower())

            normalized = self._normalize_name(entry.name)
            if normalized not in self.names_index:
                self.names_index[normalized] = []
            self.names_index[normalized].append(uid)

            for alias in entry.aliases:
                normalized_alias = self._normalize_name(alias)
                if normalized_alias not in self.names_index:
                    self.names_index[normalized_alias] = []
                self.names_index[normalized_alias].append(uid)

    def _normalize_name(self, name: str) -> str:
        """Normalize name for matching."""
        import re
        name = name.lower().strip()
        name = re.sub(r'[^\w\s]', '', name)
        name = ' '.join(name.split())
        return name

    async def _load_from_cache(self, ignore_expiry: bool = False) -> bool:
        """Load SDN list from cache file."""
        if not self.CACHE_FILE.exists():
            return False
        
        try:
            with open(self.CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
            
            cached_time = datetime.fromisoformat(cache_data.get('timestamp', '1970-01-01'))
            age = datetime.now() - cached_time
            
            if not ignore_expiry and age > timedelta(days=self.CACHE_MAX_AGE_DAYS):
                logger.info("Cache is stale, will refresh")
                return False
            
            self.sdn_entries = {
                uid: SDNEntry(**entry_data)
                for uid, entry_data in cache_data.get('entries', {}).items()
            }
            self.crypto_addresses = set(cache_data.get('crypto_addresses', []))
            self.last_update = cached_time
            
            self._build_indexes()
            return True
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Cache file corrupted: {e}")
            return False

    async def _save_to_cache(self) -> None:
        """Save SDN list to cache file."""
        try:
            self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
            
            cache_data = {
                'timestamp': (self.last_update or datetime.now()).isoformat(),
                'entries': {
                    uid: {
                        'uid': entry.uid,
                        'name': entry.name,
                        'entry_type': entry.entry_type,
                        'programs': entry.programs,
                        'aliases': entry.aliases,
                        'addresses': entry.addresses,
                        'ids': entry.ids,
                        'crypto_addresses': entry.crypto_addresses,
                    }
                    for uid, entry in self.sdn_entries.items()
                },
                'crypto_addresses': list(self.crypto_addresses),
            }
            
            with open(self.CACHE_FILE, 'w') as f:
                json.dump(cache_data, f)
            
            logger.info(f"Saved OFAC cache to {self.CACHE_FILE}")
            
        except OSError as e:
            logger.warning(f"Failed to save cache: {e}")

    async def check_address(self, wallet_address: str) -> bool:
        """
        Check if wallet address is on OFAC sanctions list.

        Uses bloom filter for fast O(1) preliminary check, then exact matching.

        Args:
            wallet_address: Blockchain wallet address to check

        Returns:
            True if blocked (sanctioned), False if allowed
        """
        if not wallet_address:
            return False
        
        try:
            normalized = wallet_address.lower().strip()
            
            if normalized in self.entity_cache:
                return self.entity_cache[normalized]
            
            if not self.bloom_filter.might_contain(normalized):
                self.entity_cache[normalized] = False
                return False
            
            is_sanctioned = normalized in self.crypto_addresses
            
            if is_sanctioned:
                logger.warning(f"OFAC block: wallet {wallet_address[:10]}... is sanctioned")
            
            self.entity_cache[normalized] = is_sanctioned
            return is_sanctioned
            
        except Exception as e:
            logger.error(f"OFAC check failed for {wallet_address}: {e}")
            return True

    async def check_name(
        self, 
        name: str, 
        fuzzy_threshold: float = 0.85
    ) -> Dict[str, Any]:
        """
        Check if a name matches SDN entries with fuzzy matching.

        Args:
            name: Name to check against SDN list
            fuzzy_threshold: Similarity threshold (0.0-1.0) for fuzzy matching

        Returns:
            {
                "blocked": bool,
                "matches": List of matching SDN entries,
                "score": highest match score
            }
        """
        if not name:
            return {"blocked": False, "matches": [], "score": 0.0}
        
        try:
            normalized = self._normalize_name(name)
            
            if normalized in self.names_index:
                matches = [
                    self.sdn_entries[uid] 
                    for uid in self.names_index[normalized]
                    if uid in self.sdn_entries
                ]
                if matches:
                    logger.warning(f"OFAC block: name '{name}' matches SDN entry (exact)")
                    return {
                        "blocked": True,
                        "matches": [{"uid": m.uid, "name": m.name} for m in matches],
                        "score": 1.0
                    }
            
            best_score = 0.0
            best_matches = []
            
            for index_name, uids in self.names_index.items():
                score = self._fuzzy_similarity(normalized, index_name)
                if score >= fuzzy_threshold:
                    if score > best_score:
                        best_score = score
                        best_matches = uids
                    elif score == best_score:
                        best_matches.extend(uids)
            
            if best_matches and best_score >= fuzzy_threshold:
                matches = [
                    self.sdn_entries[uid]
                    for uid in set(best_matches)
                    if uid in self.sdn_entries
                ]
                logger.warning(f"OFAC block: name '{name}' fuzzy matches SDN (score: {best_score:.2f})")
                return {
                    "blocked": True,
                    "matches": [{"uid": m.uid, "name": m.name} for m in matches],
                    "score": best_score
                }
            
            return {"blocked": False, "matches": [], "score": best_score}
            
        except Exception as e:
            logger.error(f"OFAC name check failed for '{name}': {e}")
            return {"blocked": True, "matches": [], "score": 0.0}

    def _fuzzy_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate similarity between two strings using Levenshtein distance.
        
        Returns a score between 0.0 (no match) and 1.0 (exact match).
        """
        if not s1 or not s2:
            return 0.0
        
        if s1 == s2:
            return 1.0
        
        len1, len2 = len(s1), len(s2)
        if abs(len1 - len2) > max(len1, len2) * 0.5:
            return 0.0
        
        if len1 > len2:
            s1, s2 = s2, s1
            len1, len2 = len2, len1
        
        previous_row = list(range(len1 + 1))
        for i, c2 in enumerate(s2):
            current_row = [i + 1]
            for j, c1 in enumerate(s1):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        distance = previous_row[-1]
        max_len = max(len1, len2)
        return 1.0 - (distance / max_len)

    async def check_entity(self, entity_name: str) -> bool:
        """
        Check if entity name appears on OFAC list.

        Args:
            entity_name: Company or person name to check

        Returns:
            True if blocked (sanctioned), False if allowed
        """
        result = await self.check_name(entity_name)
        return result["blocked"]

    async def is_list_stale(self, max_age_days: int = 7) -> bool:
        """
        Check if OFAC list needs updating.

        Args:
            max_age_days: Maximum age before update required

        Returns:
            True if list is stale and needs update
        """
        if not self.last_update:
            return True

        age = datetime.now() - self.last_update
        return age > timedelta(days=max_age_days)

    async def refresh_if_stale(self) -> bool:
        """
        Refresh SDN list if it's stale.
        
        Returns:
            True if list was refreshed, False if still fresh
        """
        if await self.is_list_stale():
            await self.load_sdn_list(force_refresh=True)
            return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the loaded SDN list."""
        return {
            "total_entries": len(self.sdn_entries),
            "crypto_addresses": len(self.crypto_addresses),
            "cached_lookups": len(self.entity_cache),
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "is_stale": asyncio.get_event_loop().run_until_complete(self.is_list_stale())
            if self.last_update else True
        }
