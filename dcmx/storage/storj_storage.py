"""
Storj DCS (Decentralized Cloud Storage) Integration

Free tier: 150GB storage + 150GB bandwidth/month
S3-compatible API for easy integration
"""

import logging
import os
from typing import Optional, Dict, Any, BinaryIO
from pathlib import Path
import hashlib
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config

logger = logging.getLogger(__name__)


class StorjStorage:
    """
    Storj DCS storage client.
    
    Features:
    - S3-compatible API
    - 150GB free storage
    - 150GB free bandwidth/month
    - Encrypted by default
    - Distributed globally
    """
    
    # Storj DCS S3 gateway endpoint
    STORJ_ENDPOINT = "https://gateway.storjshare.io"
    
    def __init__(
        self,
        access_key: str,
        secret_key: str,
        bucket_name: str = "dcmx-music",
        endpoint_url: Optional[str] = None,
    ):
        """
        Initialize Storj storage client.
        
        Args:
            access_key: Storj access key
            secret_key: Storj secret key
            bucket_name: Bucket name (default: dcmx-music)
            endpoint_url: Custom endpoint (default: Storj gateway)
        """
        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url or self.STORJ_ENDPOINT
        
        # Configure S3 client for Storj
        self.s3_client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(
                signature_version='s3v4',
                s3={'addressing_style': 'path'},
            ),
        )
        
        # Ensure bucket exists
        self._ensure_bucket()
        
        logger.info(f"Storj storage initialized: bucket={bucket_name}")
    
    def _ensure_bucket(self) -> None:
        """Create bucket if it doesn't exist."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket '{self.bucket_name}' exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Bucket doesn't exist, create it
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"Created bucket: {self.bucket_name}")
                except ClientError as create_error:
                    logger.error(f"Failed to create bucket: {create_error}")
                    raise
            else:
                logger.error(f"Error checking bucket: {e}")
                raise
    
    def upload_file(
        self,
        file_path: str,
        object_name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upload file to Storj.
        
        Args:
            file_path: Local file path
            object_name: Object name in bucket (default: filename)
            metadata: Custom metadata
            content_type: MIME type (default: auto-detect)
            
        Returns:
            Upload result with URL and metadata
        """
        if object_name is None:
            object_name = Path(file_path).name
        
        # Detect content type if not provided
        if content_type is None:
            if file_path.endswith('.mp3'):
                content_type = 'audio/mpeg'
            elif file_path.endswith('.flac'):
                content_type = 'audio/flac'
            elif file_path.endswith('.wav'):
                content_type = 'audio/wav'
            elif file_path.endswith('.m4a'):
                content_type = 'audio/mp4'
            else:
                content_type = 'application/octet-stream'
        
        # Calculate content hash
        content_hash = self._compute_file_hash(file_path)
        
        # Prepare metadata
        upload_metadata = metadata or {}
        upload_metadata['content-hash'] = content_hash
        
        try:
            # Upload file
            extra_args = {
                'ContentType': content_type,
                'Metadata': upload_metadata,
            }
            
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                object_name,
                ExtraArgs=extra_args,
            )
            
            # Generate public URL
            url = f"{self.endpoint_url}/{self.bucket_name}/{object_name}"
            
            file_size = Path(file_path).stat().st_size
            
            logger.info(
                f"Uploaded to Storj: {object_name} "
                f"({file_size / 1024 / 1024:.2f} MB)"
            )
            
            return {
                "success": True,
                "url": url,
                "object_name": object_name,
                "content_hash": content_hash,
                "size": file_size,
                "content_type": content_type,
                "bucket": self.bucket_name,
            }
            
        except ClientError as e:
            logger.error(f"Failed to upload file: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    def upload_bytes(
        self,
        data: bytes,
        object_name: str,
        metadata: Optional[Dict[str, str]] = None,
        content_type: str = 'application/octet-stream',
    ) -> Dict[str, Any]:
        """
        Upload bytes to Storj.
        
        Args:
            data: Binary data
            object_name: Object name in bucket
            metadata: Custom metadata
            content_type: MIME type
            
        Returns:
            Upload result
        """
        # Calculate content hash
        content_hash = hashlib.sha256(data).hexdigest()
        
        # Prepare metadata
        upload_metadata = metadata or {}
        upload_metadata['content-hash'] = content_hash
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_name,
                Body=data,
                ContentType=content_type,
                Metadata=upload_metadata,
            )
            
            url = f"{self.endpoint_url}/{self.bucket_name}/{object_name}"
            
            logger.info(f"Uploaded bytes to Storj: {object_name}")
            
            return {
                "success": True,
                "url": url,
                "object_name": object_name,
                "content_hash": content_hash,
                "size": len(data),
                "content_type": content_type,
            }
            
        except ClientError as e:
            logger.error(f"Failed to upload bytes: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    def download_file(
        self,
        object_name: str,
        download_path: str,
    ) -> bool:
        """
        Download file from Storj.
        
        Args:
            object_name: Object name in bucket
            download_path: Local path to save file
            
        Returns:
            Success status
        """
        try:
            self.s3_client.download_file(
                self.bucket_name,
                object_name,
                download_path,
            )
            
            logger.info(f"Downloaded from Storj: {object_name}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to download file: {e}")
            return False
    
    def get_file_url(self, object_name: str) -> str:
        """
        Get public URL for file.
        
        Args:
            object_name: Object name in bucket
            
        Returns:
            Public URL
        """
        return f"{self.endpoint_url}/{self.bucket_name}/{object_name}"
    
    def get_signed_url(
        self,
        object_name: str,
        expiration: int = 3600,
    ) -> str:
        """
        Generate presigned URL for private access.
        
        Args:
            object_name: Object name in bucket
            expiration: URL expiration in seconds (default: 1 hour)
            
        Returns:
            Signed URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_name,
                },
                ExpiresIn=expiration,
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate signed URL: {e}")
            return ""
    
    def delete_file(self, object_name: str) -> bool:
        """
        Delete file from Storj.
        
        Args:
            object_name: Object name in bucket
            
        Returns:
            Success status
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_name,
            )
            
            logger.info(f"Deleted from Storj: {object_name}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete file: {e}")
            return False
    
    def list_files(
        self,
        prefix: str = "",
        max_keys: int = 1000,
    ) -> list[Dict[str, Any]]:
        """
        List files in bucket.
        
        Args:
            prefix: Filter by prefix
            max_keys: Maximum number of results
            
        Returns:
            List of file metadata
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys,
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'etag': obj['ETag'].strip('"'),
                })
            
            return files
            
        except ClientError as e:
            logger.error(f"Failed to list files: {e}")
            return []
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage usage statistics.
        
        Returns:
            Storage stats
        """
        try:
            files = self.list_files(max_keys=10000)
            
            total_size = sum(f['size'] for f in files)
            total_count = len(files)
            
            return {
                "total_files": total_count,
                "total_size_bytes": total_size,
                "total_size_mb": total_size / 1024 / 1024,
                "total_size_gb": total_size / 1024 / 1024 / 1024,
                "bucket": self.bucket_name,
                "free_tier_limit_gb": 150,
                "usage_percentage": (total_size / 1024 / 1024 / 1024) / 150 * 100,
            }
            
        except ClientError as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {}
    
    def _compute_file_hash(self, file_path: str) -> str:
        """Compute SHA-256 hash of file."""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
