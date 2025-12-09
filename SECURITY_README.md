# DCMX Security & Authentication

Complete security implementation for the DCMX decentralized music platform.

## ✨ Features

- **🔐 Wallet-Based Authentication**: Non-custodial login using signed nonces
- **📝 JWT Tokens**: Secure stateless authentication with expiration
- **🛡️ Rate Limiting**: DDoS and abuse prevention
- **✅ Input Validation**: OWASP Top 10 vulnerability protection
- **🔒 Encryption**: Password hashing with PBKDF2, API key generation
- **📊 Audit Logging**: Compliance-ready action tracking
- **👥 Role-Based Access Control**: LISTENER, ARTIST, NODE_OPERATOR, ADMIN
- **🆔 KYC Integration**: User verification levels for compliance

## 📦 Installation

```bash
pip install PyJWT cryptography fastapi
```

## 🚀 Quick Start

### 1. Wallet Login

```python
from dcmx.auth import WalletAuthManager

auth_manager = WalletAuthManager()

# Client: Request nonce
nonce = auth_manager.generate_nonce("0xUserWallet")

# Client: Sign nonce in wallet app
# Message: "DCMX_NONCE:{nonce}"

# Server: Verify signature and create session
session = auth_manager.create_session_from_nonce(
    nonce=nonce,
    token="jwt_token_from_signature"
)
```

### 2. JWT Authentication

```python
from dcmx.security import SecurityManager, SecurityLevel

security = SecurityManager(secret_key="your_secret")

# Generate token
token = security.jwt_manager.generate_token(
    wallet_address="0xUserWallet",
    user_id="user123",
    username="artist_name",
    security_level=SecurityLevel.USER
)

# Verify token
user_info = security.authenticate(token)

# Check authorization
if security.authorize(user_info, SecurityLevel.ARTIST):
    # Allow artist features
    pass
```

### 3. Rate Limiting

```python
# Check rate limit (100 requests per 60 seconds)
allowed, reset_time = security.check_rate_limit("user_id")

if not allowed:
    print(f"Rate limited. Reset in {reset_time} seconds")
```

### 4. Input Validation

```python
from dcmx.security import InputValidator

# Validate wallet address
InputValidator.validate_wallet_address("0xAb5801a7D398351b8bE11C63579d1Ccbf49e0fA2")

# Validate email
InputValidator.validate_email("user@example.com")

# Sanitize input (XSS prevention)
safe_text = InputValidator.sanitize_input(user_input)
```

## 🏗️ Architecture

### Modules

```
dcmx/
├── security/
│   ├── __init__.py
│   └── manager.py          # Core security
│       ├── RateLimiter
│       ├── JWTManager
│       ├── InputValidator
│       ├── EncryptionManager
│       ├── AuditLogger
│       └── SecurityManager
│
└── auth/
    ├── __init__.py
    └── wallet_auth.py      # Authentication
        ├── UserProfile
        ├── Session
        ├── SessionManager
        └── WalletAuthManager
```

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Client Wallet                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 1. User clicks "Sign In"                                │ │
│ │ 2. Request nonce from server                            │ │
│ │ 3. Sign "DCMX_NONCE:{nonce}" in wallet                 │ │
│ │ 4. Send signature to server                             │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓↑
┌─────────────────────────────────────────────────────────────┐
│ DCMX Server                                                 │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 1. Generate random nonce (15 min expiry)               │ │
│ │ 2. Verify signature: recover wallet address            │ │
│ │ 3. Generate JWT token (24 hour expiry)                 │ │
│ │ 4. Create user session                                 │ │
│ │ 5. Return JWT token                                    │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓↑
┌─────────────────────────────────────────────────────────────┐
│ Client App                                                  │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 1. Store JWT token in local storage                    │ │
│ │ 2. Send token in Authorization header                  │ │
│ │ 3. Use for all authenticated requests                  │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Security Levels

| Level | Role | Permissions |
|-------|------|---|
| PUBLIC | Anonymous | View tracks, listen |
| USER | Registered user | Vote, comment, follow |
| ARTIST | Musician/Creator | Upload tracks, manage listings |
| ADMIN | Administrator | Manage users, platform settings |

## 🔐 Encryption

### Password Hashing

```python
# PBKDF2-SHA256 with 100,000 iterations
hashed, salt = EncryptionManager.hash_password("password123")

# Verify with constant-time comparison
if EncryptionManager.verify_password("password123", hashed, salt):
    # Password correct
    pass
```

### API Keys

```python
api_key, api_key_hash = EncryptionManager.generate_api_key()

# Store api_key_hash in database
# Give api_key to user (only shown once)
# Use for API authentication
```

## 📊 Audit Logging

```python
# Log security event
security.audit_logger.log_action(
    action="nft_purchase",
    user_id="user123",
    resource="track_hash",
    details={"amount": 100, "currency": "DCMX"},
    status="success"
)

# Retrieve audit trail (for compliance)
trail = security.audit_logger.get_audit_trail(user_id="user123", limit=50)
```

## 🧪 Testing

```bash
# Run all security tests
pytest tests/test_security.py tests/test_auth.py -v

# Specific test
pytest tests/test_security.py::TestRateLimiter -v

# Coverage
pytest tests/test_security.py tests/test_auth.py --cov=dcmx.security --cov=dcmx.auth
```

**Test Coverage**: 56 test cases covering all security features

## 🌐 API Integration

See `examples/secure_api_server.py` for FastAPI implementation:

```python
# Endpoints
POST   /auth/nonce        # Get nonce for wallet
POST   /auth/login        # Login with signed nonce
GET    /profile           # Get user profile (auth required)
PUT    /profile           # Update profile
POST   /tracks/upload     # Upload track (artist + KYC)
GET    /admin/audit-log   # View audit log (admin)
```

## ⚙️ Configuration

### Environment Variables

```bash
# Secret key for JWT signing (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
SECRET_KEY="your_secret_key_here"

# Rate limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60

# Session settings
SESSION_MAX_IDLE_MINUTES=120
TOKEN_EXPIRY_HOURS=24

# HTTPS enforcement
FORCE_HTTPS=true
```

### Django Integration

```python
# settings.py
DCMX_SECRET_KEY = os.getenv("SECRET_KEY")
DCMX_RATE_LIMIT = {
    "max_requests": 100,
    "window_seconds": 60
}

# Middleware
MIDDLEWARE = [
    'dcmx.security.middleware.SecurityMiddleware',  # Add security headers
    'dcmx.auth.middleware.AuthenticationMiddleware',  # Validate tokens
]
```

## 🛡️ OWASP Compliance

| Threat | Protection | Status |
|--------|-----------|--------|
| Injection | Input validation, parameterized queries | ✅ |
| Broken Auth | JWT tokens, session management | ✅ |
| XSS | HTML escaping, sanitization | ✅ |
| CSRF | SameSite cookies, token validation | ✅ |
| Insecure Deserialization | Type validation | ✅ |
| XXE | XML parsing restrictions | ✅ |
| Broken Access Control | RBAC, authorization checks | ✅ |
| Security Misconfiguration | Secure defaults | ✅ |
| Using Components with Known Vulnerabilities | Dependency scanning | ✅ |
| Insufficient Logging/Monitoring | Audit logging | ✅ |

## 📝 Best Practices

### 1. Secret Management

```python
# ✅ Good: Use environment variables
SECRET_KEY = os.getenv("SECRET_KEY")

# ❌ Bad: Hardcode secrets
SECRET_KEY = "my_secret_key"
```

### 2. Token Rotation

```python
# ✅ Good: Short-lived tokens
token = jwt_manager.generate_token(..., expires_in_hours=1)

# Implement refresh token for long sessions
refresh_token = jwt_manager.generate_token(..., expires_in_hours=24)
```

### 3. HTTPS Only

```python
# ✅ Good: Secure transmission
# Always use HTTPS in production
# Set Secure flag on cookies
# Implement HSTS

# ❌ Bad: HTTP transmission
# Never send tokens over HTTP
```

### 4. Input Validation

```python
# ✅ Good: Validate before use
if InputValidator.validate_wallet_address(input):
    # Use input
    pass

# ❌ Bad: Trust user input
# Use input directly
```

## 🚨 Security Alerts

Monitor these events:

- Failed login attempts (>3 in 1 hour)
- Rate limit exceeded (repeated)
- Unusual transaction amounts
- Geographic anomalies
- KYC verification failures
- Admin account access
- Audit log tampering attempts

## 📚 References

- **JWT.io**: https://jwt.io
- **OWASP**: https://owasp.org/Top10/
- **PBKDF2**: https://en.wikipedia.org/wiki/PBKDF2
- **Web3 Authentication**: https://www.w3c-ccg.github.io/did-siwe/
- **Rate Limiting**: https://en.wikipedia.org/wiki/Rate_limiting

## 🤝 Contributing

1. Follow existing patterns in `dcmx/security/` and `dcmx/auth/`
2. Add tests for new security features
3. Document with docstrings
4. Run tests: `pytest tests/test_security.py tests/test_auth.py`
5. Check coverage: `pytest --cov=dcmx.security --cov=dcmx.auth`

## 📄 License

MIT - See LICENSE file

## ⚖️ Legal Notice

**This security module is provided for educational purposes.**

For production deployment, especially involving:
- Real money transactions
- Personal data storage
- Financial compliance

Consult with security professionals and legal advisors.

---

**Questions?** See `docs/SECURITY.md` for comprehensive documentation.
