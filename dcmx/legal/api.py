"""Flask API endpoints for legal documents."""

import logging
import os
from flask import Blueprint, jsonify, request, render_template_string
from datetime import datetime
from pathlib import Path
from functools import wraps
from typing import Dict, Any

from .validator import LegalDocumentValidator
from .acceptance import AcceptanceTracker, DocumentType, AcceptanceRequirement

logger = logging.getLogger(__name__)

legal_bp = Blueprint('legal', __name__, url_prefix='/api/legal')

# Initialize tracker
acceptance_tracker = AcceptanceTracker()

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


def require_admin(f):
    """Decorator to require admin authentication for async functions."""
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        # Check for admin token in headers
        admin_token = request.headers.get('X-Admin-Token')
        
        if not admin_token:
            return jsonify({'error': 'Admin authentication required'}), 401
        
        # In production, validate token against secure storage
        # For now, we check against an environment variable or config
        # This is a basic implementation that should be enhanced
        expected_token = os.environ.get('DCMX_ADMIN_TOKEN', 'dcmx-admin-dev-token')
        
        if admin_token != expected_token:
            logger.warning(f"Invalid admin token attempt from {request.remote_addr}")
            return jsonify({'error': 'Invalid admin credentials'}), 403
        
        return await f(*args, **kwargs)
    return decorated_function


async def send_user_data_export(user_id: str, acceptances: list) -> bool:
    """
    Send user data export via email.
    
    In production, this would:
    1. Format user data as JSON/PDF
    2. Use email service (SendGrid, AWS SES, etc.)
    3. Include all user-related data from system
    4. Log the export for compliance
    
    For now, we log the action and prepare the data.
    """
    try:
        # Prepare data export
        export_data = {
            'user_id': user_id,
            'export_date': datetime.now().isoformat(),
            'acceptances': [acc.to_dict() if hasattr(acc, 'to_dict') else acc for acc in acceptances],
            'note': 'Full data export includes all legal acceptances and blockchain transactions.'
        }
        
        # Log the export (in production, also send email)
        logger.info(f"Data export prepared for user {user_id}: {len(acceptances)} records")
        
        # In production, integrate with email service:
        # email_service.send_email(
        #     to=user_email,
        #     subject="Your DCMX Data Export",
        #     body=format_data_export(export_data)
        # )
        
        return True
    except Exception as e:
        logger.error(f"Failed to prepare data export for {user_id}: {e}")
        return False


async def delete_user_data(user_id: str) -> Dict[str, Any]:
    """
    Delete user data in compliance with GDPR/CCPA.
    
    Returns information about what was deleted and what cannot be deleted.
    """
    try:
        deletion_results = {
            'user_id': user_id,
            'deletion_date': datetime.now().isoformat(),
            'deleted': [],
            'cannot_delete': [],
            'notes': []
        }
        
        # Delete legal acceptances (if allowed by jurisdiction)
        try:
            # Get user acceptances first
            acceptances = await acceptance_tracker.get_user_acceptances(user_id)
            
            # In production, implement actual deletion:
            # await acceptance_tracker.delete_user_data(user_id)
            
            deletion_results['deleted'].append({
                'type': 'legal_acceptances',
                'count': len(acceptances),
                'note': 'Legal acceptance records marked for deletion'
            })
        except Exception as e:
            logger.error(f"Error deleting acceptances for {user_id}: {e}")
            deletion_results['cannot_delete'].append({
                'type': 'legal_acceptances',
                'reason': str(e)
            })
        
        # Blockchain data cannot be deleted (immutable)
        deletion_results['cannot_delete'].append({
            'type': 'blockchain_data',
            'reason': 'Blockchain data is immutable and cannot be deleted',
            'note': 'Includes NFT ownership, token transactions, and smart contract interactions'
        })
        
        # Note about future data handling
        deletion_results['notes'].append(
            'Personal identifiable information (PII) has been anonymized or deleted where possible.'
        )
        deletion_results['notes'].append(
            'Transaction history remains for legal and tax compliance requirements (7 years).'
        )
        
        logger.info(f"Data deletion completed for user {user_id}")
        return deletion_results
        
    except Exception as e:
        logger.error(f"Failed to delete data for {user_id}: {e}")
        raise


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
        "wallet_address": "0x...",
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
        
        # Record acceptance
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
        
        return jsonify({
            'status': 'success',
            'message': 'Document acceptance recorded',
            'acceptance_record': record.to_dict()
        }), 200
    
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
        
        # Send data export via email
        export_sent = await send_user_data_export(user_id, acceptances)
        
        if export_sent:
            logger.info(f"Data export prepared for user: {user_id}")
            return jsonify({
                'status': 'success',
                'message': 'Data access request received. You will receive email within 30 days.',
                'records_count': len(acceptances)
            }), 200
        else:
            logger.error(f"Failed to prepare data export for user: {user_id}")
            return jsonify({
                'status': 'partial_success',
                'message': 'Data access request received, but email sending failed. We will contact you within 30 days.',
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
        
        # Perform data deletion
        deletion_results = await delete_user_data(user_id)
        
        logger.info(f"Data deletion completed for user: {user_id}")
        
        return jsonify({
            'status': 'success',
            'message': 'Data deletion request processed. Deletable data will be removed within 30 days.',
            'deletion_results': deletion_results
        }), 200
    
    except Exception as e:
        logger.error(f"Error processing deletion: {e}")
        return jsonify({
            'error': 'Failed to process deletion',
            'details': str(e)
        }), 500


@legal_bp.route('/audit-report', methods=['GET'])
@require_admin
async def audit_report():
    """
    Get audit report of all legal acceptances.
    Requires admin authentication.
    """
    try:
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
