"""LoRa mesh network layer for DCMX - bandwidth incentives, distributed routing, and ZK security."""

from dcmx.lora.lora_node import LoRaNode, LoRaPeer, BandwidthStats
from dcmx.lora.zk_proofs import (
    ZKProofGenerator,
    ZKProofVerifier,
    BandwidthProof,
    UptimeProof,
    ProximityProof,
    FreshnessProof,
    UniquenessProof,
    ZKProofCommitment,
)
from dcmx.lora.secure_messaging import (
    SecureLoRaMessaging,
    SecureMessage,
    PeerSecurityContext,
)

__all__ = [
    # Core LoRa
    "LoRaNode",
    "LoRaPeer",
    "BandwidthStats",
    # ZK Proofs
    "ZKProofGenerator",
    "ZKProofVerifier",
    "BandwidthProof",
    "UptimeProof",
    "ProximityProof",
    "FreshnessProof",
    "UniquenessProof",
    "ZKProofCommitment",
    # Secure Messaging
    "SecureLoRaMessaging",
    "SecureMessage",
    "PeerSecurityContext",
]
