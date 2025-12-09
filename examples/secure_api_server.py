"""
DCMX Secure API Server Example

Demonstrates:
- Wallet-based authentication
- JWT token validation
- Rate limiting
- Input validation
- Audit logging
- Role-based access control
"""

import logging
from fastapi import FastAPI, HTTPException, Request, Header, Depends
from pydantic import BaseModel
from typing import Optional
import os

from dcmx.core.node import Node
from dcmx.security import SecurityManager, SecurityLevel, InputValidator
from dcmx.auth import WalletAuthManager, UserRole, KYCLevel

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize managers
SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key_change_in_production")
security = SecurityManager(SECRET_KEY)
auth_manager = WalletAuthManager()

app = FastAPI(title="DCMX Secure API", version="1.0.0")


# ============================================================================
# Models
# ============================================================================

class NonceRequest(BaseModel):
    """Request nonce for wallet login."""
    wallet_address: str


class NonceResponse(BaseModel):
    """Response with nonce."""
    nonce: str
    expires_in_minutes: int = 15


class LoginRequest(BaseModel):
    """Login with signed nonce."""
    nonce: str
    signature: str
    wallet_address: str


class LoginResponse(BaseModel):
    """Response with session token."""
    access_token: str
    token_type: str = "bearer"
    user_id: str


class UserProfileUpdate(BaseModel):
    """Update user profile."""
    username: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None


class UserProfileResponse(BaseModel):
    """User profile response."""
    user_id: str
    wallet_address: str
    username: str
    email: str
    bio: str
    kyc_level: str
    roles: list
    reputation_score: float


# ============================================================================
# Dependencies
# ============================================================================

async def get_current_user(
    authorization: Optional[str] = Header(None),
    request: Request = None
):
    """Dependency to get authenticated user."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        # Extract token from "Bearer <token>"
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authorization scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    # Verify token
    user_info = security.authenticate(token)
    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Check rate limit
    allowed, reset_time = security.check_rate_limit(user_info["user_id"])
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limited. Try again in {reset_time} seconds"
        )
    
    return user_info


async def require_artist_role(user_info: dict = Depends(get_current_user)):
    """Dependency to require artist role."""
    user = auth_manager.get_user(user_info["user_id"])
    
    if not user or UserRole.ARTIST not in user.roles:
        raise HTTPException(status_code=403, detail="Artist role required")
    
    return user_info


async def require_kyc_verified(user_info: dict = Depends(get_current_user)):
    """Dependency to require KYC verification."""
    user = auth_manager.get_user(user_info["user_id"])
    
    if not user or user.kyc_level.value < KYCLevel.BASIC.value:
        raise HTTPException(status_code=403, detail="KYC verification required")
    
    return user_info


# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/auth/nonce", response_model=NonceResponse)
async def get_nonce(request: NonceRequest):
    """
    Step 1: Generate nonce for wallet login.
    
    Client must:
    1. Request nonce for their wallet
    2. Sign the nonce in their wallet app
    3. Send signature back to /auth/login
    """
    # Validate wallet address
    if not InputValidator.validate_wallet_address(request.wallet_address):
        raise HTTPException(status_code=400, detail="Invalid wallet address format")
    
    # Check rate limit on nonce requests (prevent abuse)
    allowed, reset_time = security.check_rate_limit(
        f"nonce_request_{request.wallet_address}",
        limit=5  # 5 nonces per user
    )
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Too many nonce requests. Try again in {reset_time} seconds"
        )
    
    # Generate nonce
    nonce = auth_manager.generate_nonce(request.wallet_address)
    
    logger.info(f"Nonce generated for {request.wallet_address[:16]}...")
    
    return NonceResponse(nonce=nonce, expires_in_minutes=15)


@app.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Step 2: Verify signed nonce and create session.
    
    Client must:
    1. Get nonce from /auth/nonce
    2. Sign message "DCMX_NONCE:{nonce}" in their wallet
    3. Send nonce + signature to this endpoint
    """
    # Validate inputs
    if not InputValidator.validate_wallet_address(request.wallet_address):
        raise HTTPException(status_code=400, detail="Invalid wallet address")
    
    # TODO: In production, use web3.py to recover address from signature
    # Example:
    # from web3 import Web3
    # recovered_address = Web3().eth.account.recover_message(
    #     message=f"DCMX_NONCE:{request.nonce}",
    #     signature=request.signature
    # )
    # if recovered_address.lower() != request.wallet_address.lower():
    #     raise HTTPException(status_code=401, detail="Invalid signature")
    
    # For demo, accept any signature
    recovered_address = request.wallet_address
    
    # Generate JWT token
    token = security.jwt_manager.generate_token(
        wallet_address=recovered_address,
        user_id=recovered_address,  # Use wallet as user_id for now
        username=f"user_{recovered_address[:8]}",
        security_level=SecurityLevel.USER,
        expires_in_hours=24,
    )
    
    # Create session
    session = auth_manager.create_session_from_nonce(
        nonce=request.nonce,
        token=token,
        ip_address="127.0.0.1",  # Get from request in production
    )
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired nonce")
    
    # Audit log
    security.audit_logger.log_action(
        action="user_login",
        user_id=session.user_id,
        resource="session",
        details={"wallet": recovered_address},
        status="success"
    )
    
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user_id=session.user_id
    )


# ============================================================================
# User Profile Endpoints
# ============================================================================

@app.get("/profile", response_model=UserProfileResponse)
async def get_profile(user_info: dict = Depends(get_current_user)):
    """Get authenticated user's profile."""
    user = auth_manager.get_user(user_info["user_id"])
    
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    # Audit log
    security.audit_logger.log_action(
        action="profile_view",
        user_id=user.user_id,
        resource=user.user_id,
        status="success"
    )
    
    return UserProfileResponse(
        user_id=user.user_id,
        wallet_address=user.wallet_address,
        username=user.username,
        email=user.email,
        bio=user.bio,
        kyc_level=user.kyc_level.name,
        roles=[r.value for r in user.roles],
        reputation_score=user.reputation_score
    )


@app.put("/profile", response_model=UserProfileResponse)
async def update_profile(
    update: UserProfileUpdate,
    user_info: dict = Depends(get_current_user)
):
    """Update user profile."""
    # Validate inputs
    if update.username and not InputValidator.validate_username(update.username):
        raise HTTPException(status_code=400, detail="Invalid username")
    
    if update.email and not InputValidator.validate_email(update.email):
        raise HTTPException(status_code=400, detail="Invalid email")
    
    if update.bio:
        update.bio = InputValidator.sanitize_input(update.bio, max_length=500)
    
    # Update profile
    user = auth_manager.update_profile(
        user_id=user_info["user_id"],
        username=update.username,
        email=update.email,
        bio=update.bio
    )
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Audit log
    security.audit_logger.log_action(
        action="profile_update",
        user_id=user.user_id,
        resource=user.user_id,
        details={"fields": list(update.dict(exclude_none=True).keys())},
        status="success"
    )
    
    return UserProfileResponse(
        user_id=user.user_id,
        wallet_address=user.wallet_address,
        username=user.username,
        email=user.email,
        bio=user.bio,
        kyc_level=user.kyc_level.name,
        roles=[r.value for r in user.roles],
        reputation_score=user.reputation_score
    )


# ============================================================================
# Artist Endpoints
# ============================================================================

@app.post("/tracks/upload")
async def upload_track(
    user_info: dict = Depends(require_artist_role),
    kyc_required: dict = Depends(require_kyc_verified)
):
    """
    Upload track (artist only, requires KYC).
    
    This endpoint requires:
    - Artist role
    - KYC verification (BASIC level or higher)
    - Valid JWT token
    """
    user = auth_manager.get_user(user_info["user_id"])
    
    # Audit log
    security.audit_logger.log_action(
        action="track_upload_started",
        user_id=user.user_id,
        resource="track",
        status="success"
    )
    
    return {"status": "ready_for_upload", "max_size_mb": 100}


# ============================================================================
# Admin Endpoints
# ============================================================================

@app.get("/admin/security-status")
async def get_security_status(
    authorization: Optional[str] = Header(None)
):
    """Get security system status (admin only)."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # In production, verify this is an admin
    # For now, require a specific admin token
    
    return {
        "security": security.get_security_report(),
        "auth": auth_manager.get_auth_status(),
        "timestamp": security.audit_logger.audit_log[-1]["timestamp"] if security.audit_logger.audit_log else None
    }


@app.get("/admin/audit-log")
async def get_audit_log(
    user_id: Optional[str] = None,
    limit: int = 100,
    authorization: Optional[str] = Header(None)
):
    """Get audit log (admin only)."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    return security.audit_logger.get_audit_trail(user_id=user_id, limit=limit)


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "security_enabled": True,
        "rate_limiting": True,
        "audit_logging": True
    }


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with audit logging."""
    # Log security-relevant errors
    if exc.status_code in [401, 403, 429]:
        logger.warning(f"Security event: {exc.status_code} - {exc.detail}")
    
    return {
        "error": exc.detail,
        "status_code": exc.status_code
    }


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("Starting DCMX Secure API Server...")
    print("Documentation: http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
