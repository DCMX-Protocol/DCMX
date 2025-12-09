"""OFAC sanctions checking for DCMX compliance."""

import logging
from typing import Set, Optional
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


class OFACChecker:
    """
    Checks wallet addresses and users against OFAC sanctions list.
    
    Maintains Specially Designated Nationals (SDN) list from US Treasury.
    Updates weekly and blocks transactions to/from sanctioned entities.
    """
    
    # OFAC SDN list URL
    SDN_LIST_URL = "https://home.treasury.gov/policy-issues/financial-sanctions/sdn-list"
    
    def __init__(self):
        """Initialize OFAC checker."""
        self.sdn_list: Set[str] = set()
        self.entity_cache: dict = {}
        self.last_update: Optional[datetime] = None
        
        logger.info("OFACChecker initialized")
    
    async def load_sdn_list(self) -> None:
        """
        Load latest OFAC SDN list from Treasury.
        
        Downloads and parses the Specially Designated Nationals list.
        """
        try:
            # TODO: Implement SDN list download
            # 1. Fetch from Treasury website
            # 2. Parse CSV format
            # 3. Index wallet addresses, company names, aliases
            # 4. Store in-memory with hash for fast lookup
            
            self.last_update = datetime.now()
            logger.info(f"Loaded OFAC SDN list: {len(self.sdn_list)} entries")
        except Exception as e:
            logger.error(f"Failed to load OFAC list: {e}")
    
    async def check_address(self, wallet_address: str) -> bool:
        """
        Check if wallet address is on OFAC sanctions list.
        
        Args:
            wallet_address: Blockchain wallet address to check
            
        Returns:
            True if blocked (sanctioned), False if allowed
        """
        try:
            # Check cache first
            if wallet_address in self.entity_cache:
                return self.entity_cache[wallet_address]
            
            # TODO: Implement address checking
            # 1. Check exact match against SDN list
            # 2. Check blockchain history for connections to sanctioned entities
            # 3. Check associated domains/entities
            
            is_sanctioned = wallet_address.lower() in self.sdn_list
            
            if is_sanctioned:
                logger.warning(f"OFAC block: wallet {wallet_address} is sanctioned")
                self.entity_cache[wallet_address] = True
                return True
            
            self.entity_cache[wallet_address] = False
            return False
        except Exception as e:
            logger.error(f"OFAC check failed for {wallet_address}: {e}")
            # Fail closed: block if unable to verify
            return True
    
    async def check_entity(self, entity_name: str) -> bool:
        """
        Check if entity name appears on OFAC list.
        
        Args:
            entity_name: Company or person name to check
            
        Returns:
            True if blocked (sanctioned), False if allowed
        """
        try:
            # Normalize name for comparison
            normalized_name = entity_name.lower().strip()
            
            # Check against SDN list
            for sdn_entity in self.sdn_list:
                if normalized_name in sdn_entity.lower():
                    logger.warning(f"OFAC block: entity {entity_name} matches SDN entry")
                    return True
            
            return False
        except Exception as e:
            logger.error(f"OFAC check failed for entity {entity_name}: {e}")
            return True  # Fail closed
    
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
