"""Validator for legal documents (Terms, Privacy Policy)."""

import re
import logging
from typing import List, Dict, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class LegalDocumentValidator:
    """Validates legal documents for common errors and compliance issues."""
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize validator.
        
        Args:
            strict_mode: If True, treat warnings as errors
        """
        self.strict_mode = strict_mode
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def validate_terms_and_conditions(self, content: str) -> bool:
        """
        Validate Terms and Conditions document.
        
        Returns:
            True if valid, False if errors found
        """
        self.errors = []
        self.warnings = []
        
        # Check required sections
        required_sections = [
            "ACCEPTANCE OF TERMS",
            "SERVICE DESCRIPTION",
            "USER ELIGIBILITY",
            "INTELLECTUAL PROPERTY",
            "LIMITATION OF LIABILITY",
            "DISPUTE RESOLUTION",
            "TERMINATION",
            "CONTACT & SUPPORT",
        ]
        
        for section in required_sections:
            if section.lower() not in content.lower():
                self.errors.append(f"Missing required section: {section}")
        
        # Check for legal disclaimers
        if "as-is" not in content.lower() and "provided as is" not in content.lower():
            self.warnings.append("Missing 'AS-IS' disclaimer for Platform")
        
        if "arbitration" not in content.lower():
            self.warnings.append("Missing arbitration clause (recommended for blockchain)")
        
        if "blockchain" not in content.lower():
            self.warnings.append("Missing blockchain-specific disclosures")
        
        if "irreversible" not in content.lower() and "cannot be reversed" not in content.lower():
            self.warnings.append("Missing warning about blockchain immutability")
        
        # Check for legal terminology
        if "indemnif" not in content.lower():
            self.warnings.append("Missing indemnification clause")
        
        # Check for geographic restrictions
        if "jurisd" not in content.lower():
            self.warnings.append("Missing jurisdiction/governing law clause")
        
        # Check for contact information
        if "contact" not in content.lower() or "email" not in content.lower():
            self.errors.append("Missing contact information")
        
        return len(self.errors) == 0
    
    def validate_privacy_policy(self, content: str) -> bool:
        """
        Validate Privacy Policy document.
        
        Returns:
            True if valid, False if errors found
        """
        self.errors = []
        self.warnings = []
        
        # Check required sections per GDPR
        required_sections = [
            "INFORMATION WE COLLECT",
            "HOW WE USE YOUR INFORMATION",
            "DATA SECURITY",
            "YOUR PRIVACY RIGHTS",
            "DATA RETENTION",
            "CONTACT",
        ]
        
        for section in required_sections:
            if section.lower() not in content.lower():
                self.errors.append(f"Missing required section: {section}")
        
        # Check for GDPR compliance
        if "gdpr" not in content.lower():
            self.warnings.append("Missing GDPR-specific disclosures")
        
        if "right to access" not in content.lower() and "access" not in content.lower():
            self.warnings.append("Missing data access rights (GDPR requirement)")
        
        if "deletion" not in content.lower() and "right to be forgotten" not in content.lower():
            self.warnings.append("Missing right to deletion/be forgotten (GDPR requirement)")
        
        if "data breach" not in content.lower():
            self.warnings.append("Missing data breach notification policy")
        
        # Check for CCPA compliance
        if "ccpa" not in content.lower() and "california" not in content.lower():
            self.warnings.append("Missing CCPA-specific disclosures (if serving California)")
        
        # Check encryption mention
        if "encrypt" not in content.lower():
            self.warnings.append("Missing encryption disclosures")
        
        # Check retention period
        if "retention" not in content.lower() and "retai" not in content.lower():
            self.warnings.append("Missing data retention schedule")
        
        # Check for cookies/tracking
        if "cookie" not in content.lower() and "tracking" not in content.lower():
            self.warnings.append("Missing cookies/tracking policy")
        
        return len(self.errors) == 0
    
    def check_hyperlinks(self, content: str) -> Dict[str, int]:
        """
        Check for broken or suspicious hyperlinks.
        
        Returns:
            Dict with link statistics
        """
        # Find all links
        http_links = re.findall(r'https?://[^\s\)]+', content)
        mailto_links = re.findall(r'mailto:[^\s\)]+', content)
        
        suspicious = []
        
        # Check for suspicious patterns
        for link in http_links:
            if "bit.ly" in link or "tinyurl" in link or "short.link" in link:
                suspicious.append(link)
        
        if suspicious:
            self.warnings.append(f"Found shortened URLs (not recommended): {suspicious}")
        
        return {
            "http_links": len(http_links),
            "email_links": len(mailto_links),
            "suspicious": len(suspicious),
        }
    
    def check_legal_language(self, content: str) -> Dict[str, bool]:
        """Check for appropriate legal language."""
        checks = {
            "has_all_caps_disclaimer": "ALL CAPS" in content or "WARNING" in content,
            "has_acknowledgment": "ACKNOWLEDGE" in content.upper(),
            "uses_shall": "shall" in content.lower(),
            "uses_may_vs_must": "may" in content.lower(),
            "defines_key_terms": content.count('"') > 10,  # Quoted definitions
            "has_examples": "example" in content.lower() or "e.g." in content.lower(),
        }
        return checks
    
    def check_for_ambiguity(self, content: str) -> List[str]:
        """Find potentially ambiguous language."""
        ambiguous_terms = [
            (r'\bunfortunately\b', 'Avoid emotional language'),
            (r'\bmaybe\b', 'Replace "maybe" with specific conditions'),
            (r'\bshould\b', 'Use "shall" or "must" instead of "should"'),
            (r'\btry to\b', 'Avoid non-committal language'),
            (r'\bapproximately\b', 'Use specific numbers'),
            (r'\baround\b', 'Be specific'),
            (r'\blarge\b', 'Define what "large" means'),
            (r'\bsoon\b', 'Specify timeframe'),
        ]
        
        found = []
        for pattern, recommendation in ambiguous_terms:
            if re.search(pattern, content, re.IGNORECASE):
                found.append(f"{recommendation}: '{pattern}'")
        
        return found
    
    def generate_report(self) -> str:
        """Generate validation report."""
        report = "═" * 70 + "\n"
        report += "LEGAL DOCUMENT VALIDATION REPORT\n"
        report += "═" * 70 + "\n\n"
        
        if self.errors:
            report += f"❌ ERRORS ({len(self.errors)}):\n"
            for error in self.errors:
                report += f"  • {error}\n"
            report += "\n"
        else:
            report += "✅ No critical errors found\n\n"
        
        if self.warnings:
            report += f"⚠️  WARNINGS ({len(self.warnings)}):\n"
            for warning in self.warnings:
                report += f"  • {warning}\n"
            report += "\n"
        
        return report


def validate_legal_docs(terms_path: str, privacy_path: str) -> Tuple[bool, bool]:
    """
    Validate both Terms and Privacy Policy.
    
    Returns:
        Tuple of (terms_valid, privacy_valid)
    """
    validator = LegalDocumentValidator()
    
    # Validate Terms
    print("\n" + "="*70)
    print("VALIDATING TERMS AND CONDITIONS")
    print("="*70)
    
    terms_content = Path(terms_path).read_text()
    terms_valid = validator.validate_terms_and_conditions(terms_content)
    
    # Check links
    links = validator.check_hyperlinks(terms_content)
    logger.info(f"Terms links: {links}")
    
    # Check language
    lang_checks = validator.check_legal_language(terms_content)
    logger.info(f"Legal language: {lang_checks}")
    
    # Check ambiguity
    ambiguous = validator.check_for_ambiguity(terms_content)
    if ambiguous:
        for item in ambiguous:
            validator.warnings.append(item)
    
    print(validator.generate_report())
    
    # Validate Privacy Policy
    print("\n" + "="*70)
    print("VALIDATING PRIVACY POLICY")
    print("="*70)
    
    privacy_content = Path(privacy_path).read_text()
    privacy_valid = validator.validate_privacy_policy(privacy_content)
    
    # Check links
    links = validator.check_hyperlinks(privacy_content)
    logger.info(f"Privacy links: {links}")
    
    # Check language
    lang_checks = validator.check_legal_language(privacy_content)
    logger.info(f"Legal language: {lang_checks}")
    
    # Check ambiguity
    ambiguous = validator.check_for_ambiguity(privacy_content)
    if ambiguous:
        for item in ambiguous:
            validator.warnings.append(item)
    
    print(validator.generate_report())
    
    return terms_valid, privacy_valid


if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    terms_path = "/workspaces/DCMX/docs/TERMS_AND_CONDITIONS.md"
    privacy_path = "/workspaces/DCMX/docs/PRIVACY_POLICY.md"
    
    terms_valid, privacy_valid = validate_legal_docs(terms_path, privacy_path)
    
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    print(f"Terms and Conditions: {'✅ VALID' if terms_valid else '❌ INVALID'}")
    print(f"Privacy Policy: {'✅ VALID' if privacy_valid else '❌ INVALID'}")
    print("="*70 + "\n")
    
    sys.exit(0 if (terms_valid and privacy_valid) else 1)
