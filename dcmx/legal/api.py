"""Flask API endpoints for legal documents."""

import logging
from flask import Blueprint, jsonify, request, render_template_string
from datetime import datetime
from pathlib import Path

from .validator import LegalDocumentValidator
from .acceptance import AcceptanceTracker, DocumentType, AcceptanceRequirement

logger = logging.getLogger(__name__)

legal_bp = Blueprint('legal', __name__, url_prefix='/api/legal')

# Initialize tracker
acceptance_tracker = AcceptanceTracker()

# Blockchain integration (optional, initialized on first use)
_contract_manager = None

def get_contract_manager():
    """Get or initialize contract manager."""
    global _contract_manager
    if _contract_manager is None:
        try:
            from dcmx.tron.contracts import ContractManager
            from dcmx.tron.config import TronConfig
            config = TronConfig.from_env()
            if config.compliance_registry_address:
                _contract_manager = ContractManager(config)
                logger.info("Blockchain compliance integration enabled")
            else:
                logger.warning("Compliance registry address not configured")
        except Exception as e:
            logger.error(f"Failed to initialize blockchain integration: {e}")
    return _contract_manager

# Load document content
TERMS_PATH = Path(__file__).parent.parent.parent / "docs" / "TERMS_AND_CONDITIONS.md"
PRIVACY_PATH = Path(__file__).parent.parent.parent / "docs" / "PRIVACY_POLICY.md"

try:
    TERMS_CONTENT = TERMS_PATH.read_text()
    PRIVACY_CONTENT = PRIVACY_PATH.read_text()
except FileNotFoundError:
    logger.warning("Legal documents not found")
    TERMS_CONTENT = "Terms not found"
    PRIVACY_CONTENT = "Privacy policy not found"


@legal_bp.route('/terms', methods=['GET'])
def get_terms():
    """Get Terms and Conditions."""
    return TERMS_CONTENT, 200, {'Content-Type': 'text/plain; charset=utf-8'}


@legal_bp.route('/privacy', methods=['GET'])
def get_privacy():
    """Get Privacy Policy."""
    return PRIVACY_CONTENT, 200, {'Content-Type': 'text/plain; charset=utf-8'}


@legal_bp.route('/accept', methods=['POST'])
async def accept_document():
    """
    Record user acceptance of a legal document.
    
    Request JSON:
    {
        "user_id": "user123",
        "wallet_address": "T...",
        "document_type": "terms_and_conditions",
        "version": "1.0",
        "ip_address": "1.2.3.4",
        "user_agent": "Mozilla/5.0...",
        "read_time_seconds": 300
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['user_id', 'wallet_address', 'document_type', 'version']
        if not all(field in data for field in required):
            return jsonify({
                'error': 'Missing required fields',
                'required': required
            }), 400
        
        # Record acceptance in file storage
        record = await acceptance_tracker.record_acceptance(
            user_id=data['user_id'],
            wallet_address=data['wallet_address'],
            document_type=DocumentType[data['document_type'].upper()],
            version=data['version'],
            ip_address=data.get('ip_address'),
            user_agent=data.get('user_agent'),
            signature=data.get('signature'),
            read_time_seconds=data.get('read_time_seconds', 0),
            document_content=get_document_content(data['document_type'])
        )
        
        response_data = {
            'status': 'success',
            'message': 'Document acceptance recorded',
            'acceptance_record': record.to_dict()
        }
        
        # Also record on blockchain if available
        contract_manager = get_contract_manager()
        if contract_manager and contract_manager.compliance:
            try:
                from dcmx.tron import utils
                
                # Get document type enum
                doc_type_map = {
                    'terms_and_conditions': 0,
                    'privacy_policy': 1,
                    'cookie_policy': 2,
                    'nft_agreement': 3,
                    'risk_disclosure': 4,
                }
                doc_type = doc_type_map.get(data['document_type'].lower(), 0)
                
                # Compute document hash
                doc_content = get_document_content(data['document_type'])
                doc_hash = utils.compute_document_hash(doc_content)
                
                # Record on blockchain
                result = contract_manager.compliance.record_acceptance(
                    user_address=data['wallet_address'],
                    document_hash=doc_hash,
                    document_type=doc_type,
                    version=data['version'],
                    ip_address=utils.compute_document_hash(data.get('ip_address', 'unknown'))
                )
                
                if result.success:
                    response_data['blockchain_tx'] = result.transaction_hash
                    logger.info(f"Acceptance recorded on blockchain: {result.transaction_hash}")
                else:
                    logger.warning(f"Blockchain recording failed: {result.error}")
                    
            except Exception as e:
                logger.error(f"Blockchain integration error: {e}")
                # Don't fail the request if blockchain fails
        
        return jsonify(response_data), 200
    
    except Exception as e:
        logger.error(f"Error recording acceptance: {e}")
        return jsonify({
            'error': 'Failed to record acceptance',
            'details': str(e)
        }), 500


@legal_bp.route('/acceptance-status/<user_id>/<document_type>', methods=['GET'])
async def get_acceptance_status(user_id: str, document_type: str):
    """
    Check if user has accepted a document.
    
    Query params:
    - version: Specific version to check
    - within_days: Must be within this many days
    """
    try:
        version = request.args.get('version')
        within_days = request.args.get('within_days', type=int)
        
        record = await acceptance_tracker.get_acceptance(
            user_id=user_id,
            document_type=DocumentType[document_type.upper()],
            version=version
        )
        
        if not record:
            return jsonify({
                'user_id': user_id,
                'document_type': document_type,
                'accepted': False,
                'reason': 'No acceptance record found'
            }), 200
        
        # Check if within required days
        if within_days:
            from datetime import datetime, timedelta
            accepted_time = datetime.fromisoformat(record.accepted_at)
            now = datetime.utcnow()
            if (now - accepted_time).days > within_days:
                return jsonify({
                    'user_id': user_id,
                    'document_type': document_type,
                    'accepted': False,
                    'reason': f'Acceptance is {(now - accepted_time).days} days old (max: {within_days})'
                }), 200
        
        return jsonify({
            'user_id': user_id,
            'document_type': document_type,
            'accepted': True,
            'acceptance_record': record.to_dict()
        }), 200
    
    except KeyError:
        return jsonify({
            'error': 'Invalid document type',
            'valid_types': [dt.value for dt in DocumentType]
        }), 400
    except Exception as e:
        logger.error(f"Error checking acceptance: {e}")
        return jsonify({
            'error': 'Failed to check acceptance status',
            'details': str(e)
        }), 500


@legal_bp.route('/request-data', methods=['POST'])
async def request_data():
    """
    Handle GDPR/CCPA right to access request.
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        # Get all acceptances for user
        acceptances = await acceptance_tracker.get_user_acceptances(user_id)
        
        # TODO: Implement email sending with user data export
        logger.info(f"Data access request from user: {user_id}")
        
        return jsonify({
            'status': 'success',
            'message': 'Data access request received. You will receive email within 30 days.',
            'records_count': len(acceptances)
        }), 200
    
    except Exception as e:
        logger.error(f"Error processing data request: {e}")
        return jsonify({
            'error': 'Failed to process request',
            'details': str(e)
        }), 500


@legal_bp.route('/delete-data', methods=['POST'])
async def delete_data():
    """
    Handle GDPR/CCPA right to deletion request.
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        # TODO: Implement actual data deletion
        # Note: Blockchain data cannot be deleted (immutable)
        logger.info(f"Data deletion request from user: {user_id}")
        
        return jsonify({
            'status': 'success',
            'message': 'Data deletion request received. Data will be deleted within 30 days.',
            'note': 'Blockchain data (NFTs, tokens) cannot be deleted as it is immutable.'
        }), 200
    
    except Exception as e:
        logger.error(f"Error processing deletion: {e}")
        return jsonify({
            'error': 'Failed to process deletion',
            'details': str(e)
        }), 500


@legal_bp.route('/audit-report', methods=['GET'])
async def audit_report():
    """
    Get audit report of all legal acceptances.
    Requires admin authentication.
    """
    try:
        # TODO: Add admin authentication check
        
        stats = await acceptance_tracker.audit_report()
        
        return jsonify({
            'status': 'success',
            'report': stats
        }), 200
    
    except Exception as e:
        logger.error(f"Error generating audit report: {e}")
        return jsonify({
            'error': 'Failed to generate report',
            'details': str(e)
        }), 500


@legal_bp.route('/validate', methods=['POST'])
def validate():
    """
    Validate legal documents for compliance.
    """
    try:
        validator = LegalDocumentValidator()
        
        # Validate both documents
        terms_valid = validator.validate_terms_and_conditions(TERMS_CONTENT)
        terms_report = validator.generate_report()
        
        privacy_valid = validator.validate_privacy_policy(PRIVACY_CONTENT)
        privacy_report = validator.generate_report()
        
        return jsonify({
            'terms_and_conditions': {
                'valid': terms_valid,
                'report': terms_report
            },
            'privacy_policy': {
                'valid': privacy_valid,
                'report': privacy_report
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error validating documents: {e}")
        return jsonify({
            'error': 'Validation failed',
            'details': str(e)
        }), 500


@legal_bp.route('/blockchain/verify/<wallet_address>', methods=['GET'])
def verify_blockchain_compliance(wallet_address: str):
    """
    Verify user's compliance acceptance on blockchain.
    
    Query params:
    - document_type: Type of document (0-4)
    - document_hash: Hash of document to verify
    """
    try:
        contract_manager = get_contract_manager()
        if not contract_manager or not contract_manager.compliance:
            return jsonify({
                'error': 'Blockchain integration not available'
            }), 503
        
        document_type = request.args.get('document_type', type=int, default=0)
        document_hash = request.args.get('document_hash')
        
        if not document_hash:
            return jsonify({
                'error': 'document_hash required'
            }), 400
        
        # Verify on blockchain
        verified = contract_manager.compliance.verify_acceptance(
            user_address=wallet_address,
            document_type=document_type,
            document_hash=document_hash
        )
        
        return jsonify({
            'wallet_address': wallet_address,
            'document_type': document_type,
            'document_hash': document_hash,
            'verified': verified,
            'source': 'blockchain'
        }), 200
        
    except Exception as e:
        logger.error(f"Blockchain verification error: {e}")
        return jsonify({
            'error': 'Verification failed',
            'details': str(e)
        }), 500


@legal_bp.route('/blockchain/request-deletion', methods=['POST'])
def request_blockchain_deletion():
    """
    Request data deletion on blockchain (GDPR/CCPA).
    
    Request JSON:
    {
        "wallet_address": "T...",
        "reason": "GDPR right to deletion"
    }
    """
    try:
        data = request.get_json()
        wallet_address = data.get('wallet_address')
        reason = data.get('reason', 'User requested deletion')
        
        if not wallet_address:
            return jsonify({'error': 'wallet_address required'}), 400
        
        contract_manager = get_contract_manager()
        if not contract_manager or not contract_manager.compliance:
            return jsonify({
                'error': 'Blockchain integration not available'
            }), 503
        
        # Request deletion on blockchain
        result = contract_manager.compliance.request_data_deletion(reason)
        
        if result.success:
            return jsonify({
                'status': 'success',
                'message': 'Deletion request recorded on blockchain',
                'transaction_hash': result.transaction_hash,
                'note': 'Blockchain data is immutable. Request has been recorded for compliance purposes.'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to record deletion request',
                'error': result.error
            }), 500
            
    except Exception as e:
        logger.error(f"Blockchain deletion request error: {e}")
        return jsonify({
            'error': 'Request failed',
            'details': str(e)
        }), 500


def get_document_content(document_type: str) -> str:
    """Get full document content by type."""
    if document_type == 'terms_and_conditions':
        return TERMS_CONTENT
    elif document_type == 'privacy_policy':
        return PRIVACY_CONTENT
    return ""


def register_legal_routes(app):
    """Register legal document routes with Flask app."""
    app.register_blueprint(legal_bp)
    logger.info("Legal document routes registered")
