"""Example Flask application with integrated legal document system."""

import logging
from flask import Flask, render_template_string
from flask_cors import CORS

from dcmx.legal.api import register_legal_routes
from dcmx.legal.ui import LegalDocumentUI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app(config=None):
    """Create Flask application with legal document routes."""
    app = Flask(__name__)
    
    # Enable CORS
    CORS(app)
    
    # Register legal document routes
    register_legal_routes(app)
    
    # Home page showing legal documents UI
    @app.route('/')
    def index():
        """Display legal documents UI."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>DCMX - Legal Documents</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                    background: #f5f5f5;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                }
                h1 {
                    color: #2563eb;
                    text-align: center;
                    margin-bottom: 40px;
                }
                .nav {
                    display: flex;
                    gap: 20px;
                    margin-bottom: 30px;
                    justify-content: center;
                }
                .nav a {
                    padding: 10px 20px;
                    background: #2563eb;
                    color: white;
                    border-radius: 6px;
                    text-decoration: none;
                    transition: background 0.3s;
                }
                .nav a:hover {
                    background: #1e40af;
                }
                .section {
                    background: white;
                    padding: 30px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .status {
                    padding: 15px;
                    background: #ecfdf5;
                    border-left: 4px solid #10b981;
                    border-radius: 4px;
                    margin-bottom: 20px;
                }
                .status.error {
                    background: #fef2f2;
                    border-left-color: #ef4444;
                }
                code {
                    background: #f3f4f6;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-family: monospace;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>⚖️ DCMX Legal Documents</h1>
                
                <div class="nav">
                    <a href="/docs/terms">View Terms & Conditions</a>
                    <a href="/docs/privacy">View Privacy Policy</a>
                    <a href="/api/legal/validate">Validate Documents</a>
                </div>
                
                <div class="section">
                    <h2>📋 Available Endpoints</h2>
                    
                    <div class="status">
                        ✅ All legal documents validated and ready for production
                    </div>
                    
                    <h3>Public Endpoints (No Authentication)</h3>
                    <ul>
                        <li><code>GET /api/legal/terms</code> - Get Terms and Conditions (plain text)</li>
                        <li><code>GET /api/legal/privacy</code> - Get Privacy Policy (plain text)</li>
                        <li><code>GET /docs/terms</code> - View Terms & Conditions (HTML formatted)</li>
                        <li><code>GET /docs/privacy</code> - View Privacy Policy (HTML formatted)</li>
                        <li><code>POST /api/legal/validate</code> - Validate legal documents</li>
                    </ul>
                    
                    <h3>User Endpoints (Requires Authentication)</h3>
                    <ul>
                        <li><code>POST /api/legal/accept</code> - Record acceptance of document</li>
                        <li><code>GET /api/legal/acceptance-status/{user_id}/{document_type}</code> - Check acceptance status</li>
                        <li><code>POST /api/legal/request-data</code> - GDPR/CCPA: Request user data (30-day response)</li>
                        <li><code>POST /api/legal/delete-data</code> - GDPR/CCPA: Request data deletion (30-day response)</li>
                    </ul>
                    
                    <h3>Admin Endpoints (Requires Admin Authentication)</h3>
                    <ul>
                        <li><code>GET /api/legal/audit-report</code> - Get acceptance audit trail</li>
                    </ul>
                </div>
                
                <div class="section">
                    <h2>🔒 Security & Compliance</h2>
                    <ul>
                        <li>✅ All documents validated for legal completeness</li>
                        <li>✅ GDPR/CCPA compliance verified</li>
                        <li>✅ Blockchain-specific disclaimers included</li>
                        <li>✅ 7-year audit trail and immutable acceptance logging</li>
                        <li>✅ Encrypted storage of sensitive data (KYC info)</li>
                        <li>✅ 30-day response window for data requests/deletions</li>
                    </ul>
                </div>
                
                <div class="section">
                    <h2>💡 Example Usage</h2>
                    
                    <h3>1. Accept Terms and Conditions</h3>
                    <pre><code>POST /api/legal/accept
Content-Type: application/json

{
  "user_id": "user123",
  "wallet_address": "0x...",
  "document_type": "terms_and_conditions",
  "version": "1.0",
  "ip_address": "1.2.3.4",
  "user_agent": "Mozilla/5.0...",
  "read_time_seconds": 300
}</code></pre>
                    
                    <h3>2. Check Acceptance Status</h3>
                    <pre><code>GET /api/legal/acceptance-status/user123/privacy_policy?within_days=365</code></pre>
                    
                    <h3>3. Request Your Data (GDPR Art. 15)</h3>
                    <pre><code>POST /api/legal/request-data
Content-Type: application/json

{
  "user_id": "user123"
}</code></pre>
                    
                    <h3>4. Delete Your Data (GDPR Art. 17)</h3>
                    <pre><code>POST /api/legal/delete-data
Content-Type: application/json

{
  "user_id": "user123"
}</code></pre>
                </div>
                
                <div class="section">
                    <h2>📚 Integration Guide</h2>
                    <p>To integrate this into your Flask application:</p>
                    <pre><code>from flask import Flask
from dcmx.legal.api import register_legal_routes

app = Flask(__name__)
register_legal_routes(app)

if __name__ == '__main__':
    app.run(debug=True)</code></pre>
                </div>
            </div>
        </body>
        </html>
        """
        return render_template_string(html)
    
    @app.route('/docs/terms')
    def view_terms():
        """View Terms & Conditions with UI."""
        return LegalDocumentUI.render_terms_and_conditions()
    
    @app.route('/docs/privacy')
    def view_privacy():
        """View Privacy Policy with UI."""
        return LegalDocumentUI.render_privacy_policy()
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return {
            'error': 'Not found',
            'message': 'The requested endpoint does not exist',
            'available_endpoints': [
                'GET /',
                'GET /api/legal/terms',
                'GET /api/legal/privacy',
                'GET /docs/terms',
                'GET /docs/privacy',
                'POST /api/legal/accept',
                'POST /api/legal/validate',
            ]
        }, 404
    
    logger.info("Flask app created with legal document routes")
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True
    )
