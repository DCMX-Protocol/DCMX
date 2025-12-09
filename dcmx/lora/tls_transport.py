"""TLS 1.3 transport wrapper for LoRa mesh network."""

import ssl
import socket
import logging
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class TLSConfig:
    """Configuration for TLS 1.3 transport.
    
    Attributes:
        cert_path: Path to the certificate file (PEM format).
        key_path: Path to the private key file (PEM format).
        ca_path: Path to the CA certificate file for peer verification.
        min_version: Minimum TLS version (default: TLS 1.3).
        verify_mode: SSL verification mode (default: CERT_REQUIRED).
        check_hostname: Whether to verify hostname in certificate.
        ciphers: Optional cipher suite specification.
    """
    cert_path: Path
    key_path: Path
    ca_path: Path
    min_version: ssl.TLSVersion = field(default=ssl.TLSVersion.TLSv1_3)
    verify_mode: ssl.VerifyMode = field(default=ssl.CERT_REQUIRED)
    check_hostname: bool = True
    ciphers: Optional[str] = None

    def validate(self) -> bool:
        """Validate that all required files exist.
        
        Returns:
            True if all files exist, False otherwise.
        """
        if not self.cert_path.exists():
            logger.error(f"Certificate file not found: {self.cert_path}")
            return False
        if not self.key_path.exists():
            logger.error(f"Key file not found: {self.key_path}")
            return False
        if not self.ca_path.exists():
            logger.error(f"CA file not found: {self.ca_path}")
            return False
        return True


class TLSTransport:
    """TLS 1.3 transport wrapper for secure LoRa communication.
    
    Provides secure socket wrapping with TLS 1.3, certificate validation,
    and peer authentication for the LoRa mesh network.
    """

    def __init__(self, config: TLSConfig):
        """Initialize TLS transport with configuration.
        
        Args:
            config: TLS configuration containing certificates and settings.
        """
        self.config = config
        self._server_context: Optional[ssl.SSLContext] = None
        self._client_context: Optional[ssl.SSLContext] = None

    def create_server_context(self) -> ssl.SSLContext:
        """Create SSL context for server-side connections.
        
        Returns:
            Configured SSLContext for accepting TLS connections.
            
        Raises:
            ssl.SSLError: If context creation fails.
            FileNotFoundError: If certificate files are missing.
        """
        if self._server_context is not None:
            return self._server_context

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = self.config.min_version
        context.maximum_version = ssl.TLSVersion.TLSv1_3
        
        context.load_cert_chain(
            certfile=str(self.config.cert_path),
            keyfile=str(self.config.key_path)
        )
        
        context.load_verify_locations(cafile=str(self.config.ca_path))
        context.verify_mode = self.config.verify_mode
        
        if self.config.ciphers:
            context.set_ciphers(self.config.ciphers)
        
        context.check_hostname = False
        
        self._server_context = context
        logger.info("Server TLS 1.3 context created")
        return context

    def create_client_context(self) -> ssl.SSLContext:
        """Create SSL context for client-side connections.
        
        Returns:
            Configured SSLContext for initiating TLS connections.
            
        Raises:
            ssl.SSLError: If context creation fails.
            FileNotFoundError: If certificate files are missing.
        """
        if self._client_context is not None:
            return self._client_context

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.minimum_version = self.config.min_version
        context.maximum_version = ssl.TLSVersion.TLSv1_3
        
        context.load_cert_chain(
            certfile=str(self.config.cert_path),
            keyfile=str(self.config.key_path)
        )
        
        context.load_verify_locations(cafile=str(self.config.ca_path))
        context.verify_mode = self.config.verify_mode
        context.check_hostname = self.config.check_hostname
        
        if self.config.ciphers:
            context.set_ciphers(self.config.ciphers)
        
        self._client_context = context
        logger.info("Client TLS 1.3 context created")
        return context

    def wrap_socket(
        self,
        sock: socket.socket,
        server_side: bool,
        server_hostname: Optional[str] = None
    ) -> ssl.SSLSocket:
        """Wrap a socket with TLS 1.3 encryption.
        
        Args:
            sock: Plain socket to wrap.
            server_side: True for server-side, False for client-side.
            server_hostname: Hostname for SNI (client-side only).
            
        Returns:
            TLS-wrapped socket.
            
        Raises:
            ssl.SSLError: If TLS handshake fails.
        """
        if server_side:
            context = self.create_server_context()
            ssl_socket = context.wrap_socket(
                sock,
                server_side=True
            )
        else:
            context = self.create_client_context()
            ssl_socket = context.wrap_socket(
                sock,
                server_side=False,
                server_hostname=server_hostname
            )
        
        logger.debug(
            f"Socket wrapped with TLS {ssl_socket.version()}, "
            f"cipher: {ssl_socket.cipher()}"
        )
        return ssl_socket

    def validate_peer_certificate(self, ssl_socket: ssl.SSLSocket) -> bool:
        """Validate the peer's certificate.
        
        Performs additional validation beyond standard TLS verification,
        including certificate expiration and subject checks.
        
        Args:
            ssl_socket: Connected TLS socket.
            
        Returns:
            True if certificate is valid, False otherwise.
        """
        try:
            cert = ssl_socket.getpeercert()
            if not cert:
                logger.warning("No peer certificate received")
                return False

            not_after = cert.get('notAfter')
            if not_after:
                expiry = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                if expiry < datetime.utcnow():
                    logger.warning("Peer certificate has expired")
                    return False

            not_before = cert.get('notBefore')
            if not_before:
                valid_from = datetime.strptime(not_before, '%b %d %H:%M:%S %Y %Z')
                if valid_from > datetime.utcnow():
                    logger.warning("Peer certificate is not yet valid")
                    return False

            subject = dict(x[0] for x in cert.get('subject', ()))
            if not subject.get('commonName'):
                logger.warning("Peer certificate missing Common Name")
                return False

            logger.debug(f"Peer certificate validated: CN={subject.get('commonName')}")
            return True

        except Exception as e:
            logger.error(f"Certificate validation error: {e}")
            return False

    def get_peer_common_name(self, ssl_socket: ssl.SSLSocket) -> Optional[str]:
        """Extract the Common Name from peer's certificate.
        
        Args:
            ssl_socket: Connected TLS socket.
            
        Returns:
            Common Name string or None if not found.
        """
        try:
            cert = ssl_socket.getpeercert()
            if cert:
                subject = dict(x[0] for x in cert.get('subject', ()))
                return subject.get('commonName')
        except Exception as e:
            logger.error(f"Failed to get peer CN: {e}")
        return None

    def get_connection_info(self, ssl_socket: ssl.SSLSocket) -> dict:
        """Get information about the TLS connection.
        
        Args:
            ssl_socket: Connected TLS socket.
            
        Returns:
            Dictionary containing connection details.
        """
        return {
            'version': ssl_socket.version(),
            'cipher': ssl_socket.cipher(),
            'peer_cn': self.get_peer_common_name(ssl_socket),
            'compression': ssl_socket.compression(),
        }
