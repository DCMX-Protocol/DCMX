"""UI components for displaying and accepting legal documents."""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum
from datetime import datetime


class DocumentType(Enum):
    """Types of legal documents."""
    TERMS_AND_CONDITIONS = "terms_and_conditions"
    PRIVACY_POLICY = "privacy_policy"
    COOKIE_POLICY = "cookie_policy"
    NFT_AGREEMENT = "nft_agreement"
    RISK_DISCLOSURE = "risk_disclosure"


@dataclass
class DocumentVersion:
    """Version of a legal document."""
    version: str
    effective_date: datetime
    updated_date: datetime
    changes: Optional[str] = None
    requires_reacceptance: bool = False


@dataclass
class UserAcceptance:
    """Record of user accepting a legal document."""
    user_id: str
    wallet_address: str
    document_type: DocumentType
    version: str
    accepted_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    signature: Optional[str] = None  # Optional blockchain signature proof


class LegalDocumentUI:
    """Web UI component for displaying legal documents."""
    
    @staticmethod
    def render_terms_and_conditions() -> str:
        """Render Terms and Conditions HTML."""
        return '''
        <div class="legal-document">
            <div class="document-header">
                <h1>Terms and Conditions</h1>
                <p class="version-info">Last Updated: December 9, 2025</p>
            </div>
            
            <div class="document-nav">
                <details>
                    <summary>Quick Navigation</summary>
                    <ul class="toc">
                        <li><a href="#acceptance">1. Acceptance of Terms</a></li>
                        <li><a href="#service">2. Service Description</a></li>
                        <li><a href="#eligibility">3. User Eligibility</a></li>
                        <li><a href="#ip">4. Intellectual Property</a></li>
                        <li><a href="#content">5. Content Policies</a></li>
                        <li><a href="#blockchain">6. Blockchain & Smart Contracts</a></li>
                        <li><a href="#compliance">7. Compliance & Regulation</a></li>
                        <li><a href="#liability">9. Limitation of Liability</a></li>
                        <li><a href="#dispute">11. Dispute Resolution</a></li>
                        <li><a href="#termination">13. Termination</a></li>
                        <li><a href="#contact">16. Contact & Support</a></li>
                    </ul>
                </details>
            </div>
            
            <div class="document-content">
                <!-- Content loaded from TERMS_AND_CONDITIONS.md -->
                <iframe src="/api/legal/terms" class="document-iframe" title="Terms and Conditions"></iframe>
            </div>
            
            <div class="document-controls">
                <div class="controls-buttons">
                    <button id="print-terms" class="btn btn-secondary">
                        <span class="icon">🖨️</span> Print
                    </button>
                    <button id="download-terms" class="btn btn-secondary">
                        <span class="icon">⬇️</span> Download PDF
                    </button>
                    <button id="agree-terms" class="btn btn-primary" data-document="terms">
                        <span class="icon">✓</span> I Agree to Terms
                    </button>
                    <button id="disagree-terms" class="btn btn-outline">
                        <span class="icon">✕</span> I Disagree
                    </button>
                </div>
            </div>
            
            <div id="acceptance-form" class="acceptance-form" style="display:none;">
                <h3>Acceptance Confirmation</h3>
                <p>By clicking "I Agree", you confirm that:</p>
                <ul>
                    <li>✓ You have read and understood these Terms</li>
                    <li>✓ You are at least 18 years of age</li>
                    <li>✓ You accept all risks of blockchain and P2P networks</li>
                    <li>✓ You are not in a sanctioned jurisdiction</li>
                    <li>✓ You own all content you upload</li>
                </ul>
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="confirm-terms" />
                        I confirm my acceptance of these Terms and Conditions
                    </label>
                </div>
                <button id="submit-acceptance" class="btn btn-primary" disabled>
                    Confirm Acceptance
                </button>
            </div>
        </div>
        '''
    
    @staticmethod
    def render_privacy_policy() -> str:
        """Render Privacy Policy HTML."""
        return '''
        <div class="legal-document">
            <div class="document-header">
                <h1>Privacy Policy</h1>
                <p class="version-info">Last Updated: December 9, 2025</p>
            </div>
            
            <div class="document-nav">
                <details>
                    <summary>Quick Navigation</summary>
                    <ul class="toc">
                        <li><a href="#summary">1. Privacy Policy Summary</a></li>
                        <li><a href="#collect">2. Information We Collect</a></li>
                        <li><a href="#use">3. How We Use Your Information</a></li>
                        <li><a href="#share">4. Who We Share Data With</a></li>
                        <li><a href="#security">5. Data Security</a></li>
                        <li><a href="#rights">6. Your Privacy Rights</a></li>
                        <li><a href="#retention">7. Data Retention</a></li>
                        <li><a href="#cookies">8. Cookies & Tracking</a></li>
                        <li><a href="#blockchain">10. Blockchain Privacy</a></li>
                        <li><a href="#contact">15. Contact & Requests</a></li>
                    </ul>
                </details>
            </div>
            
            <div class="document-content">
                <!-- Content loaded from PRIVACY_POLICY.md -->
                <iframe src="/api/legal/privacy" class="document-iframe" title="Privacy Policy"></iframe>
            </div>
            
            <div class="document-controls">
                <div class="controls-buttons">
                    <button id="print-privacy" class="btn btn-secondary">
                        <span class="icon">🖨️</span> Print
                    </button>
                    <button id="download-privacy" class="btn btn-secondary">
                        <span class="icon">⬇️</span> Download PDF
                    </button>
                    <button id="request-data" class="btn btn-secondary">
                        <span class="icon">📊</span> Request My Data
                    </button>
                    <button id="delete-data" class="btn btn-outline">
                        <span class="icon">🗑️</span> Delete My Data
                    </button>
                </div>
            </div>
            
            <div id="privacy-consent" class="privacy-consent">
                <h3>Privacy Preferences</h3>
                <div class="consent-options">
                    <div class="option">
                        <label>
                            <input type="checkbox" id="consent-analytics" checked disabled />
                            <span>Website Analytics (Required for site performance)</span>
                        </label>
                    </div>
                    <div class="option">
                        <label>
                            <input type="checkbox" id="consent-notifications" />
                            <span>Email Notifications (You can disable anytime in settings)</span>
                        </label>
                    </div>
                    <div class="option">
                        <label>
                            <input type="checkbox" id="consent-marketing" />
                            <span>Marketing Communications (Unsubscribe anytime)</span>
                        </label>
                    </div>
                </div>
                <button id="save-privacy-preferences" class="btn btn-primary">
                    Save Preferences
                </button>
            </div>
        </div>
        '''
    
    @staticmethod
    def render_cookie_banner() -> str:
        """Render GDPR/CCPA cookie consent banner."""
        return '''
        <div id="cookie-banner" class="cookie-banner">
            <div class="cookie-content">
                <h3>🍪 Cookie Consent</h3>
                <p>
                    DCMX uses cookies to enhance your experience. We do NOT use cookies 
                    for advertising or tracking across sites. 
                    <a href="/legal/privacy#cookies" target="_blank">Learn more</a>
                </p>
                <div class="cookie-options">
                    <button id="cookie-essential-only" class="btn btn-outline">
                        Essential Only
                    </button>
                    <button id="cookie-accept-all" class="btn btn-primary">
                        Accept All
                    </button>
                    <button id="cookie-settings" class="btn btn-secondary">
                        Cookie Settings
                    </button>
                </div>
            </div>
        </div>
        '''
    
    @staticmethod
    def render_risk_disclosure() -> str:
        """Render blockchain risk disclosure modal."""
        return '''
        <div id="risk-disclosure-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>⚠️  Risk Disclosure: Blockchain Assets</h2>
                    <button class="modal-close">&times;</button>
                </div>
                
                <div class="modal-body">
                    <h3>Before You Begin</h3>
                    <p>
                        DCMX is built on blockchain technology. Please understand these risks:
                    </p>
                    
                    <div class="risk-section">
                        <h4>🔓 Private Key Responsibility</h4>
                        <ul>
                            <li>You control your private key, not DCMX</li>
                            <li>If you lose it, we CANNOT recover your assets</li>
                            <li>If someone steals it, they control everything</li>
                            <li>Use hardware wallets (Ledger, Trezor) for security</li>
                        </ul>
                    </div>
                    
                    <div class="risk-section">
                        <h4>💰 No Guarantees</h4>
                        <ul>
                            <li>NFT values can go to zero</li>
                            <li>DCMX Platform may shut down</li>
                            <li>Smart contracts may have bugs despite audits</li>
                            <li>Regulations may change</li>
                        </ul>
                    </div>
                    
                    <div class="risk-section">
                        <h4>⛓️  Blockchain Immutability</h4>
                        <ul>
                            <li>All transactions are permanent</li>
                            <li>We cannot reverse transactions</li>
                            <li>Scams: No refund possible</li>
                            <li>Mistakes: You must fix manually</li>
                        </ul>
                    </div>
                    
                    <div class="risk-section">
                        <h4>🌐 Network Risks</h4>
                        <ul>
                            <li>Ethereum network can be congested → high gas fees</li>
                            <li>Transactions may fail (your ETH still spent on gas)</li>
                            <li>Front-running: Others can see your transactions</li>
                            <li>51% attacks: Extremely unlikely but theoretically possible</li>
                        </ul>
                    </div>
                </div>
                
                <div class="modal-footer">
                    <div class="risk-acknowledgment">
                        <label>
                            <input type="checkbox" id="acknowledge-risks" />
                            I understand and accept these risks
                        </label>
                    </div>
                    <button id="continue-to-app" class="btn btn-primary" disabled>
                        Continue to App
                    </button>
                </div>
            </div>
        </div>
        '''


class LegalDocumentStyles:
    """CSS styles for legal documents."""
    
    @staticmethod
    def get_styles() -> str:
        """Return CSS for legal documents."""
        return '''
        <style>
        .legal-document {
            max-width: 900px;
            margin: 40px auto;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            color: #333;
            line-height: 1.6;
        }
        
        .document-header {
            border-bottom: 3px solid #2563eb;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        
        .document-header h1 {
            margin: 0 0 10px 0;
            font-size: 2.5em;
            color: #1e40af;
        }
        
        .version-info {
            color: #666;
            margin: 5px 0 0 0;
            font-size: 0.9em;
        }
        
        .document-nav {
            background: #f3f4f6;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .document-nav summary {
            cursor: pointer;
            font-weight: 600;
            color: #2563eb;
            user-select: none;
        }
        
        .document-nav .toc {
            list-style: none;
            padding-left: 20px;
            margin-top: 10px;
        }
        
        .document-nav .toc li {
            margin: 8px 0;
        }
        
        .document-nav .toc a {
            color: #2563eb;
            text-decoration: none;
            transition: color 0.2s;
        }
        
        .document-nav .toc a:hover {
            color: #1e40af;
            text-decoration: underline;
        }
        
        .document-iframe {
            width: 100%;
            height: 800px;
            border: 1px solid #ddd;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        .document-content {
            background: white;
            padding: 30px;
            border: 1px solid #ddd;
            border-radius: 8px;
            margin-bottom: 20px;
            line-height: 1.8;
        }
        
        .document-content h2 {
            margin-top: 30px;
            margin-bottom: 15px;
            color: #1e40af;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 10px;
        }
        
        .document-content h3 {
            margin-top: 20px;
            color: #2563eb;
        }
        
        .document-content ul, .document-content ol {
            margin: 15px 0;
            padding-left: 30px;
        }
        
        .document-content li {
            margin: 8px 0;
        }
        
        .document-content code {
            background: #f3f4f6;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
        }
        
        .document-content table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        
        .document-content table th {
            background: #f3f4f6;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border: 1px solid #ddd;
        }
        
        .document-content table td {
            padding: 12px;
            border: 1px solid #ddd;
        }
        
        .document-controls {
            background: #f9fafb;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        .controls-buttons {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1em;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.3s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        .btn-primary {
            background: #2563eb;
            color: white;
        }
        
        .btn-primary:hover {
            background: #1e40af;
        }
        
        .btn-secondary {
            background: #6b7280;
            color: white;
        }
        
        .btn-secondary:hover {
            background: #4b5563;
        }
        
        .btn-outline {
            background: white;
            color: #2563eb;
            border: 2px solid #2563eb;
        }
        
        .btn-outline:hover {
            background: #eff6ff;
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .acceptance-form {
            background: #eff6ff;
            border: 2px solid #2563eb;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        
        .acceptance-form h3 {
            color: #1e40af;
            margin-top: 0;
        }
        
        .acceptance-form ul {
            list-style: none;
            padding: 0;
            margin: 15px 0;
        }
        
        .acceptance-form li {
            padding: 8px 0;
            color: #1f2937;
        }
        
        .form-group {
            margin: 20px 0;
        }
        
        .form-group label {
            display: flex;
            align-items: center;
            gap: 10px;
            cursor: pointer;
            font-weight: 500;
        }
        
        .form-group input[type="checkbox"] {
            width: 18px;
            height: 18px;
            cursor: pointer;
        }
        
        .privacy-consent, .cookie-banner {
            background: #f3f4f6;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        .consent-options {
            margin: 20px 0;
        }
        
        .option {
            padding: 12px;
            background: white;
            border-radius: 6px;
            margin-bottom: 10px;
        }
        
        .option label {
            display: flex;
            align-items: center;
            gap: 10px;
            cursor: pointer;
        }
        
        .option input[type="checkbox"] {
            width: 18px;
            height: 18px;
            cursor: pointer;
        }
        
        .cookie-banner {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: white;
            border-top: 2px solid #2563eb;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
            z-index: 9999;
        }
        
        .cookie-content {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 20px;
        }
        
        .cookie-options {
            display: flex;
            gap: 10px;
        }
        
        .modal {
            display: flex;
            position: fixed;
            z-index: 10000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            align-items: center;
            justify-content: center;
        }
        
        .modal-content {
            background: white;
            border-radius: 8px;
            max-width: 600px;
            max-height: 90vh;
            overflow-y: auto;
            box-shadow: 0 20px 25px rgba(0,0,0,0.2);
        }
        
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px;
            border-bottom: 1px solid #ddd;
        }
        
        .modal-header h2 {
            margin: 0;
        }
        
        .modal-close {
            background: none;
            border: none;
            font-size: 1.5em;
            cursor: pointer;
            color: #999;
        }
        
        .modal-body {
            padding: 20px;
        }
        
        .risk-section {
            margin: 20px 0;
            padding: 15px;
            background: #fff5f5;
            border-left: 4px solid #dc2626;
            border-radius: 4px;
        }
        
        .risk-section h4 {
            margin-top: 0;
            color: #991b1b;
        }
        
        .risk-section ul {
            margin: 10px 0;
            padding-left: 20px;
        }
        
        .modal-footer {
            padding: 20px;
            border-top: 1px solid #ddd;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 10px;
        }
        
        .risk-acknowledgment label {
            display: flex;
            align-items: center;
            gap: 10px;
            cursor: pointer;
        }
        
        @media (max-width: 768px) {
            .document-header h1 {
                font-size: 1.8em;
            }
            
            .controls-buttons {
                flex-direction: column;
            }
            
            .btn {
                width: 100%;
                justify-content: center;
            }
            
            .cookie-content {
                flex-direction: column;
                align-items: flex-start;
            }
            
            .cookie-options {
                width: 100%;
                flex-direction: column;
            }
            
            .btn {
                width: 100%;
            }
            
            .modal-footer {
                flex-direction: column;
                align-items: stretch;
            }
        }
        </style>
        '''


class LegalDocumentScript:
    """JavaScript for legal document interactions."""
    
    @staticmethod
    def get_script() -> str:
        """Return JavaScript for legal documents."""
        return '''
        <script>
        // Terms and Conditions Handling
        document.getElementById('agree-terms')?.addEventListener('click', function() {
            document.getElementById('acceptance-form').style.display = 'block';
            document.getElementById('agree-terms').style.display = 'none';
        });
        
        document.getElementById('confirm-terms')?.addEventListener('change', function() {
            const submitBtn = document.getElementById('submit-acceptance');
            submitBtn.disabled = !this.checked;
        });
        
        document.getElementById('submit-acceptance')?.addEventListener('click', async function() {
            const response = await fetch('/api/legal/accept', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    document_type: 'terms_and_conditions',
                    accepted_at: new Date().toISOString(),
                    ip_address: await getClientIp()
                })
            });
            
            if (response.ok) {
                alert('✅ Terms accepted! You can now use DCMX.');
                window.location.href = '/app';
            }
        });
        
        document.getElementById('disagree-terms')?.addEventListener('click', function() {
            if (confirm('You cannot use DCMX without accepting the Terms. Proceed to exit?')) {
                window.location.href = '/';
            }
        });
        
        // Privacy Policy Data Requests
        document.getElementById('request-data')?.addEventListener('click', async function() {
            if (confirm('Request your personal data (GDPR right to access)? \\nYou will receive an email with your data.')) {
                const response = await fetch('/api/legal/request-data', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                
                if (response.ok) {
                    alert('✅ Request submitted. Check your email within 30 days.');
                }
            }
        });
        
        document.getElementById('delete-data')?.addEventListener('click', async function() {
            if (confirm('WARNING: This will delete your personal data (GDPR right to be forgotten). \\nBlockchain data cannot be deleted. \\nProceed?')) {
                const response = await fetch('/api/legal/delete-data', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                
                if (response.ok) {
                    alert('✅ Deletion request submitted. Your data will be deleted within 30 days.');
                }
            }
        });
        
        // Cookie Banner
        document.getElementById('cookie-accept-all')?.addEventListener('click', function() {
            localStorage.setItem('cookie_consent', 'all');
            document.getElementById('cookie-banner').style.display = 'none';
        });
        
        document.getElementById('cookie-essential-only')?.addEventListener('click', function() {
            localStorage.setItem('cookie_consent', 'essential');
            document.getElementById('cookie-banner').style.display = 'none';
        });
        
        // Risk Disclosure
        document.getElementById('acknowledge-risks')?.addEventListener('change', function() {
            document.getElementById('continue-to-app').disabled = !this.checked;
        });
        
        document.getElementById('continue-to-app')?.addEventListener('click', function() {
            localStorage.setItem('risk_acknowledged', 'true');
            document.getElementById('risk-disclosure-modal').style.display = 'none';
        });
        
        // Utility functions
        async function getClientIp() {
            try {
                const response = await fetch('https://api.ipify.org?format=json');
                const data = await response.json();
                return data.ip;
            } catch (e) {
                return null;
            }
        }
        
        // Privacy preferences
        document.getElementById('save-privacy-preferences')?.addEventListener('click', function() {
            const prefs = {
                analytics: document.getElementById('consent-analytics').checked,
                notifications: document.getElementById('consent-notifications').checked,
                marketing: document.getElementById('consent-marketing').checked
            };
            
            localStorage.setItem('privacy_preferences', JSON.stringify(prefs));
            alert('✅ Privacy preferences saved');
        });
        
        // Print functionality
        document.getElementById('print-terms')?.addEventListener('click', function() {
            window.print();
        });
        
        document.getElementById('print-privacy')?.addEventListener('click', function() {
            window.print();
        });
        
        // Download PDF (requires server-side PDF generation)
        document.getElementById('download-terms')?.addEventListener('click', async function() {
            const response = await fetch('/api/legal/download?doc=terms&format=pdf');
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'DCMX-Terms-and-Conditions.pdf';
            a.click();
        });
        
        document.getElementById('download-privacy')?.addEventListener('click', async function() {
            const response = await fetch('/api/legal/download?doc=privacy&format=pdf');
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'DCMX-Privacy-Policy.pdf';
            a.click();
        });
        </script>
        '''
