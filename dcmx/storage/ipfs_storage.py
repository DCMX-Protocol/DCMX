"""
Web3.Storage IPFS Integration

Free tier: 10GB storage + 10GB bandwidth/month
IPFS + Filecoin redundancy for permanent storage
"""

import logging
import os
from typing import Optional, Dict, Any
from pathlib import Path
import aiohttp
import hashlib
import json

logger = logging.getLogger(__name__)


class Web3Storage:
    """
    Web3.Storage client for IPFS storage.
    
    Features:
    - 10GB free storage
    - IPFS + Filecoin backup
    - Content addressing
    - Permanent storage
    """
    
    API_ENDPOINT = "https://api.web3.storage"
    
    def __init__(self, api_token: str):
        """
        Initialize Web3.Storage client.
        
        Args:
            api_token: Web3.Storage API token
        """
        self.api_token = api_token
        self.session: Optional[aiohttp.ClientSession] = None
        
        logger.info("Web3.Storage initialized")
    
    async def _ensure_session(self) -> None:
        """Ensure aiohttp session exists."""
        if self.session is None:
            headers: Dict[str, str] = {
                "Authorization": f"Bearer {self.api_token}",
            }
            self.session = aiohttp.ClientSession(headers=headers)
    
    async def close(self) -> None:
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def upload_file(
        self,
        file_path: str,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload file to Web3.Storage (IPFS).
        
        Args:
            file_path: Local file path
            name: Optional name for the file
            
        Returns:
            Upload result with CID
        """
        await self._ensure_session()
        
        if name is None:
            name = Path(file_path).name
        
        try:
            # Read file
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Calculate content hash
            content_hash = hashlib.sha256(file_data).hexdigest()
            file_size = len(file_data)
            
            # Upload to Web3.Storage
            url = f"{self.API_ENDPOINT}/upload"
            
            # Create form data
            form = aiohttp.FormData()
            form.add_field(
                'file',
                file_data,
                filename=name,
                content_type='application/octet-stream',
            )
            
            if self.session is None:
                raise RuntimeError("Session not initialized")
            
            async with self.session.post(url, data=form) as response:
                if response.status == 200:
                    data = await response.json()
                    cid = data.get('cid')
                    
                    logger.info(
                        f"Uploaded to IPFS: {name} "
                        f"({file_size / 1024 / 1024:.2f} MB) -> {cid}"
                    )
                    
                    return {
                        "success": True,
                        "cid": cid,
                        "ipfs_url": f"ipfs://{cid}",
                        "gateway_url": f"https://{cid}.ipfs.w3s.link",
                        "content_hash": content_hash,
                        "size": file_size,
                        "name": name,
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Upload failed: {response.status} - {error_text}")
                    
                    return {
                        "success": False,
                        "error": error_text,
                    }
                    
        except Exception as e:
            logger.error(f"Error uploading to Web3.Storage: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def upload_bytes(
        self,
        data: bytes,
        name: str,
    ) -> Dict[str, Any]:
        """
        Upload bytes to Web3.Storage.
        
        Args:
            data: Binary data
            name: File name
            
        Returns:
            Upload result with CID
        """
        await self._ensure_session()
        
        try:
            # Calculate content hash
            content_hash = hashlib.sha256(data).hexdigest()
            
            url = f"{self.API_ENDPOINT}/upload"
            
            form = aiohttp.FormData()
            form.add_field(
                'file',
                data,
                filename=name,
                content_type='application/octet-stream',
            )
            
            if self.session is None:
                raise RuntimeError("Session not initialized")
            
            async with self.session.post(url, data=form) as response:
                if response.status == 200:
                    result = await response.json()
                    cid = result.get('cid')
                    
                    return {
                        "success": True,
                        "cid": cid,
                        "ipfs_url": f"ipfs://{cid}",
                        "gateway_url": f"https://{cid}.ipfs.w3s.link",
                        "content_hash": content_hash,
                        "size": len(data),
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": error_text,
                    }
                    
        except Exception as e:
            logger.error(f"Error uploading bytes: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def get_file_info(self, cid: str) -> Dict[str, Any]:
        """
        Get file information by CID.
        
        Args:
            cid: IPFS CID
            
        Returns:
            File information
        """
        await self._ensure_session()
        
        try:
            url = f"{self.API_ENDPOINT}/status/{cid}"
            
            if self.session is None:
                raise RuntimeError("Session not initialized")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return {
                        "cid": data.get('cid'),
                        "created": data.get('created'),
                        "pins": data.get('pins', []),
                        "deals": data.get('deals', []),
                    }
                else:
                    return {}
                    
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return {}
    
    async def list_uploads(self, limit: int = 100) -> list[Dict[str, Any]]:
        """
        List uploaded files.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of uploads
        """
        await self._ensure_session()
        
        try:
            url = f"{self.API_ENDPOINT}/user/uploads"
            params = {"size": limit}
            
            if self.session is None:
                raise RuntimeError("Session not initialized")
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    return []
                    
        except Exception as e:
            logger.error(f"Error listing uploads: {e}")
            return []
    
    def get_gateway_url(self, cid: str) -> str:
        """
        Get gateway URL for CID.
        
        Args:
            cid: IPFS CID
            
        Returns:
            Gateway URL
        """
        return f"https://{cid}.ipfs.w3s.link"
    
    def get_ipfs_url(self, cid: str) -> str:
        """
        Get IPFS URL for CID.
        
        Args:
            cid: IPFS CID
            
        Returns:
            IPFS URL
        """
        return f"ipfs://{cid}"


class NFTStorage:
    """
    NFT.Storage client for NFT metadata storage.
    
    Free forever, 100GB/month uploads.
    """
    
    API_ENDPOINT = "https://api.nft.storage"
    
    def __init__(self, api_token: str):
        """
        Initialize NFT.Storage client.
        
        Args:
            api_token: NFT.Storage API token
        """
        self.api_token = api_token
        self.session: Optional[aiohttp.ClientSession] = None
        
        logger.info("NFT.Storage initialized")
    
    async def _ensure_session(self) -> None:
        """Ensure aiohttp session exists."""
        if self.session is None:
            headers: Dict[str, str] = {
                "Authorization": f"Bearer {self.api_token}",
            }
            self.session = aiohttp.ClientSession(headers=headers)
    
    async def close(self) -> None:
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def upload_nft_metadata(
        self,
        name: str,
        description: str,
        image_cid: str,
        attributes: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Upload NFT metadata to NFT.Storage.
        
        Args:
            name: NFT name
            description: NFT description
            image_cid: IPFS CID of image
            attributes: NFT attributes
            
        Returns:
            Upload result with metadata CID
        """
        await self._ensure_session()
        
        # Construct NFT metadata (ERC-721 standard)
        metadata = {
            "name": name,
            "description": description,
            "image": f"ipfs://{image_cid}",
            "attributes": attributes,
        }
        
        try:
            url = f"{self.API_ENDPOINT}/upload"
            
            # Convert metadata to JSON bytes
            metadata_bytes = json.dumps(metadata).encode('utf-8')
            
            form = aiohttp.FormData()
            form.add_field(
                'file',
                metadata_bytes,
                filename='metadata.json',
                content_type='application/json',
            )
            
            if self.session is None:
                raise RuntimeError("Session not initialized")
            
            async with self.session.post(url, data=form) as response:
                if response.status == 200:
                    data = await response.json()
                    cid = data.get('value', {}).get('cid')
                    
                    logger.info(f"NFT metadata uploaded: {cid}")
                    
                    return {
                        "success": True,
                        "cid": cid,
                        "ipfs_url": f"ipfs://{cid}",
                        "gateway_url": f"https://{cid}.ipfs.nftstorage.link",
                        "metadata": metadata,
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": error_text,
                    }
                    
        except Exception as e:
            logger.error(f"Error uploading NFT metadata: {e}")
            return {
                "success": False,
                "error": str(e),
            }
