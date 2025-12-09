"""DCMX Legal Documents Module.

This module provides:
- Terms and Conditions document
- Privacy Policy document  
- Legal document validation
- User acceptance tracking
- UI components for legal documents
"""

from .validator import LegalDocumentValidator, validate_legal_docs
from .acceptance import (
    DocumentType,
    AcceptanceRecord,
    AcceptanceTracker,
    AcceptanceRequirement,
)
from .ui import (
    LegalDocumentUI,
    LegalDocumentStyles,
    LegalDocumentScript,
)

__version__ = "1.0.0"
__all__ = [
    "LegalDocumentValidator",
    "validate_legal_docs",
    "DocumentType",
    "AcceptanceRecord",
    "AcceptanceTracker",
    "AcceptanceRequirement",
    "LegalDocumentUI",
    "LegalDocumentStyles",
    "LegalDocumentScript",
]
