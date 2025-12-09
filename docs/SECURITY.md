# DCMX Security & Authentication Module

## Overview

The DCMX Security and Authentication modules provide comprehensive security features for the decentralized music platform:

- **Authentication**: Wallet-based authentication using signed nonces
- **Session Management**: Secure user session handling with expiration
- **Authorization**: Role-based access control (RBAC)
- **Rate Limiting**: DDoS protection with configurable limits
- **Input Validation**: OWASP top-10 vulnerability prevention
- **Encryption**: Password hashing, API key generation, sensitive data encryption
- **Audit Logging**: Compliance-ready audit trails
- **KYC/AML Ready**: User profile management with KYC verification levels

## Quick Start

### Installation

```bash
pip install PyJWT cryptography
```

### Basic Usage

#### Wallet Authentication

```python
from dcmx.auth import WalletAuthManager

# Initialize manager
auth_manager = WalletAuthManager()

# Step 1: Generate nonce for user wallet
nonce = auth_manager.generate_nonce("0xYourWalletAddress")
print(f"Sign this nonce in your wallet: {nonce}")

# Step 2: After user signs nonce in wallet, create session
session = auth_manager.create_session_from_nonce(
    nonce=nonce,
    token="jwt_token_from_signature",
    ip_address="192.168.1.100",
    user_agent="Mozilla/5.0..."
)

if session:
    print(f"Session created: {session.session_id}")
    print(f"User ID: {session.user_id}")
```

#### Security Manager

```python
from dcmx.security import SecurityManager, SecurityLevel

# Initialize
security_manager = SecurityManager(secret_key="your_secret_key_here")

# Generate JWT token
token = security_manager.jwt_manager.generate_token(
    wallet_address="0xYourWallet",
    user_id="user123",
    username="artist_name",
    security_level=SecurityLevel.USER,
    expires_in_hours=24
)

# Verify token
user_info = security_manager.authenticate(token)

# Check authorization
if security_manager.authorize(user_info, SecurityLevel.USER):
    print("User authorized!")

# Check rate limit
allowed, reset_time = security_manager.check_rate_limit("user123")
if not allowed:
    print(f"Rate limited. Reset in {reset_time} seconds")
```

#### Input Validation

```python
from dcmx.security import InputValidator

# Validate wallet address
if InputValidator.validate_wallet_address("0xAb5801a7D398351b8bE11C63579d1Ccbf49e0fA2"):
    print("Valid wallet!")

# Validate email
if InputValidator.validate_email("user@example.com"):
    print("Valid email!")

# Sanitize user input
safe_input = InputValidator.sanitize_input(user_provided_text)

# Validate transaction amount
if InputValidator.validate_amount(100, min_val=1, max_val=1000000):
    print("Valid amount!")
```

#### Encryption

```python
from dcmx.security import EncryptionManager

# Hash password
hashed, salt = EncryptionManager.hash_password("user_password_123")

# Verify password
if EncryptionManager.verify_password("user_password_123", hashed, salt):
    print("Password correct!")

# Generate API key
api_key, api_key_hash = EncryptionManager.generate_api_key()
# Store api_key_hash in database, give api_key to user once
```

## Module Architecture

### `dcmx/security/manager.py`

Core security module with:

- **RateLimiter**: Per-user request rate limiting
- **JWTManager**: JWT token generation and verification
- **InputValidator**: OWASP-compliant input validation
- **EncryptionManager**: Password hashing and encryption
- **AuditLogger**: Compliance-ready audit trail
- **SecurityManager**: Central orchestrator

### `dcmx/auth/wallet_auth.py`

Authentication module with:

- **UserProfile**: User account with roles and KYC levels
- **Session**: User session with expiration and invalidation
- **SessionManager**: Session lifecycle management
- **WalletAuthManager**: Wallet-based authentication flow

## Features

### 1. Wallet-Based Authentication

**Flow**:
1. User requests nonce from node
2. User signs nonce in their wallet app
3. User sends signature to node
4. Node verifies signature and creates session
5. Session token used for subsequent requests

**Benefits**:
- No passwords to store
- User controls private keys
- Non-custodial
- Compatible with hardware wallets

```python
# Step 1: Generate nonce
nonce = auth_manager.generate_nonce("0xUserWallet")

# Step 2: User signs nonce (happens in wallet app)
# User's wallet signs: "DCMX_NONCE:{nonce}"

# Step 3: Server verifies signature
# (In production, use web3.py to recover address from signature)

# Step 4: Create session
session = auth_manager.create_session_from_nonce(nonce, token)
```

### 2. Role-Based Access Control (RBAC)

**User Roles**:
- `LISTENER`: Can listen and vote
- `ARTIST`: Can upload tracks and receive rewards
- `NODE_OPERATOR`: Can run LoRa node
- `ADMIN`: Platform administrator

**Security Levels**:
- `PUBLIC`: No authentication required
- `USER`: Basic user login required
- `ARTIST`: Artist-specific permissions
- `ADMIN`: Administrator only

```python
# Check user role
if user_profile.has_role(UserRole.ARTIST):
    # Allow artist features
    pass

# Check authorization level
if security_manager.authorize(user_info, SecurityLevel.ARTIST):
    # Allow artist endpoint
    pass
```

### 3. Rate Limiting

**Protection against**:
- DDoS attacks
- Brute force login attempts
- API abuse

**Configuration**:
```python
# 100 requests per 60 seconds per user
limiter = RateLimiter(max_requests=100, window_seconds=60)

# Check if request allowed
if limiter.is_allowed("user_id"):
    # Process request
    pass
else:
    # Rate limited
    reset_time = limiter.get_reset_time("user_id")
    print(f"Try again in {reset_time} seconds")
```

### 4. Input Validation

**OWASP Protections**:
- SQL Injection: Parameterized queries
- XSS: HTML/JS character escaping
- Command Injection: Input character restriction
- Path Traversal: Whitelist validation

```python
# Validate wallet addresses (Ethereum format)
if InputValidator.validate_wallet_address(user_input):
    pass

# Validate email format
if InputValidator.validate_email(user_input):
    pass

# Sanitize user input
safe_text = InputValidator.sanitize_input(user_input, max_length=1000)

# Validate amounts
if InputValidator.validate_amount(amount, min_val=0, max_val=1000000):
    pass
```

### 5. Encryption & Hashing

**Password Security**:
- PBKDF2-SHA256 with 100,000 iterations
- Unique salt per password
- Constant-time comparison

**API Key Generation**:
- Cryptographically secure tokens
- Never store plaintext keys
- Store hash only

```python
# Hash password with salt
hashed_password, salt = EncryptionManager.hash_password("password123")

# Verify password (constant time)
if EncryptionManager.verify_password("password123", hashed_password, salt):
    # Passwords match
    pass

# Generate API key
api_key, api_key_hash = EncryptionManager.generate_api_key()
# Save api_key_hash to database
# Give api_key to user once
```

### 6. Audit Logging

**Compliance Features**:
- Immutable action logging
- Timestamped entries
- User tracking
- Resource tracking
- Status recording

```python
# Log security event
audit_logger.log_action(
    action="nft_purchase",
    user_id="user123",
    resource="track_hash_abc",
    details={"amount": 100, "currency": "DCMX"},
    status="success"
)

# Retrieve audit trail
trail = audit_logger.get_audit_trail(user_id="user123")
# For compliance/regulatory review
```

### 7. KYC Verification

**Verification Levels**:
- `NONE` (0): No verification
- `BASIC` (1): Email verified
- `ENHANCED` (2): ID verified
- `FULL` (3): ID + Address verified

```python
# Update user KYC level
user_profile.verify_kyc(KYCLevel.ENHANCED)

# Check KYC level before operation
if user_profile.kyc_level.value >= KYCLevel.BASIC.value:
    # Allow transaction
    pass
```

## Integration with Node

### Adding Security to Node

```python
from dcmx.core.node import Node
from dcmx.security import SecurityManager
from dcmx.auth import WalletAuthManager

class SecureNode(Node):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.security = SecurityManager("your_secret_key")
        self.auth = WalletAuthManager()
    
    async def authenticate_request(self, request):
        """Middleware to verify JWT token."""
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        user_info = self.security.authenticate(token)
        
        if not user_info:
            return {"error": "Unauthorized"}, 401
        
        return user_info
    
    async def check_rate_limit(self, user_id):
        """Check rate limit before processing."""
        allowed, reset_time = self.security.check_rate_limit(user_id)
        
        if not allowed:
            return {"error": f"Rate limited. Reset in {reset_time}s"}, 429
        
        return None
```

### REST API Integration

```python
@app.post("/auth/nonce")
async def get_nonce(wallet_address: str):
    """Generate nonce for wallet login."""
    # Validate wallet format
    if not InputValidator.validate_wallet_address(wallet_address):
        return {"error": "Invalid wallet address"}, 400
    
    # Generate nonce
    nonce = auth_manager.generate_nonce(wallet_address)
    
    return {"nonce": nonce}


@app.post("/auth/login")
async def login(nonce: str, signature: str):
    """Create session from signed nonce."""
    # Verify signature (implement web3 signature verification)
    # recovered_address = verify_signature(nonce, signature)
    
    # Create session
    session = auth_manager.create_session_from_nonce(
        nonce=nonce,
        token=generate_jwt_token(recovered_address),
        ip_address=request.client.host,
        user_agent=request.headers.get("User-Agent", "")
    )
    
    if not session:
        return {"error": "Invalid nonce"}, 400
    
    return {"session_id": session.session_id, "token": session.token}


@app.get("/profile")
async def get_profile(request):
    """Get user profile (requires authentication)."""
    # Authenticate
    user_info = await authenticate_request(request)
    if isinstance(user_info, dict) and "error" in user_info:
        return user_info
    
    # Check rate limit
    rate_limit_response = await check_rate_limit(user_info["user_id"])
    if rate_limit_response:
        return rate_limit_response
    
    # Get user profile
    profile = auth_manager.get_user(user_info["user_id"])
    
    return {"profile": profile.to_dict() if profile else None}
```

## Security Best Practices

### 1. Secret Key Management

```python
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable not set")

security = SecurityManager(SECRET_KEY)
```

### 2. HTTPS Only

```python
# In production, always use HTTPS
# Never transmit tokens over HTTP
# Set Secure cookie flag
```

### 3. Token Rotation

```python
# Generate short-lived tokens (24 hours)
token = jwt_manager.generate_token(
    wallet_address=wallet,
    user_id=user_id,
    username=username,
    expires_in_hours=24
)

# Implement refresh token mechanism for long-lived sessions
```

### 4. Password Policy

```python
# Enforce strong passwords
def validate_password(password: str) -> bool:
    # At least 12 characters
    if len(password) < 12:
        return False
    
    # Must contain uppercase, lowercase, numbers, special chars
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*]", password):
        return False
    
    return True
```

### 5. Session Security

```python
# Max session idle time (2 hours)
session = session_manager.create_session(
    user_id=user_id,
    wallet_address=wallet,
    token=token,
    ip_address=request.client.host,
)

# Validate session before each request
if not session.is_valid(max_idle_minutes=120):
    # Session expired
    pass
```

### 6. Logging & Monitoring

```python
# Log all authentication events
audit_logger.log_action(
    action="login",
    user_id=user_id,
    resource="session",
    details={"wallet": wallet_address, "ip": ip_address},
    status="success"
)

# Alert on suspicious patterns
if failed_login_attempts > 3:
    # Lock account or require verification
    pass
```

## Testing

Run security tests:

```bash
# All security tests
pytest tests/test_security.py -v

# All auth tests
pytest tests/test_auth.py -v

# Combined
pytest tests/test_security.py tests/test_auth.py -v

# Coverage report
pytest tests/test_security.py tests/test_auth.py --cov=dcmx.security --cov=dcmx.auth
```

## Compliance

### GDPR Compliance

```python
# Right to deletion
def delete_user_data(user_id: str):
    """Delete user personal data (30-day window)."""
    profile = auth_manager.get_user(user_id)
    if profile:
        del auth_manager.user_profiles[user_id]
        del auth_manager.wallet_users[profile.wallet_address]
        
        # Keep audit log for 7 years (tax requirement)
```

### OWASP Top 10

- ✅ A1: Broken Access Control (RBAC)
- ✅ A2: Cryptographic Failures (AES-256, PBKDF2)
- ✅ A3: Injection (Input validation, parametrized)
- ✅ A4: Insecure Design (OAuth/wallet-based)
- ✅ A5: Security Misconfiguration (Secure defaults)
- ✅ A6: Vulnerable Components (Up-to-date deps)
- ✅ A7: Identification Failures (JWT + rate limiting)
- ✅ A8: Data Integrity Failures (Audit logging)
- ✅ A9: Logging & Monitoring (Comprehensive audit trail)
- ✅ A10: SSRF (Input validation prevents)

## Troubleshooting

### Token Verification Fails

```python
# Check token expiration
try:
    payload = jwt_manager.verify_token(token)
except jwt.ExpiredSignatureError:
    print("Token has expired")
except jwt.InvalidTokenError as e:
    print(f"Invalid token: {e}")
```

### Rate Limit Triggered

```python
# Check reset time
reset_time = rate_limiter.get_reset_time("user_id")
print(f"Please try again in {reset_time} seconds")

# For development, increase limit
limiter = RateLimiter(max_requests=1000, window_seconds=60)
```

### Session Expired

```python
# Check session validity
if not session.is_valid():
    # Create new session with refreshed token
    new_session = session_manager.create_session(...)
```

## Performance

- **Rate Limiter**: O(1) lookups, O(n) cleanup
- **JWT**: Fast verification with HMAC-SHA256
- **Input Validation**: O(n) where n = input length
- **Password Hashing**: Intentionally slow (100k iterations)
- **Audit Logging**: Append-only, O(1) writes

## Future Enhancements

- [ ] Multi-signature wallet support
- [ ] Social recovery mechanisms
- [ ] Hardware wallet integration
- [ ] Biometric authentication
- [ ] Risk-based authentication (adaptive)
- [ ] Passwordless authentication
- [ ] OAuth2/OpenID Connect integration
- [ ] RBAC with resource-level permissions
- [ ] Blockchain-based reputation scores
- [ ] DeFi integration (collateral-based access)
