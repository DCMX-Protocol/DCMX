-- DCMX Compliance Database Schema

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- KYC Verification Table
CREATE TABLE IF NOT EXISTS kyc_verifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) UNIQUE NOT NULL,
    wallet_address VARCHAR(42) UNIQUE NOT NULL,
    
    -- Personal Information (Encrypted)
    encrypted_name BYTEA NOT NULL,
    encrypted_dob BYTEA NOT NULL,
    encrypted_ssn BYTEA NOT NULL,
    encrypted_address BYTEA NOT NULL,
    country VARCHAR(2) NOT NULL DEFAULT 'US',
    
    -- Verification Status
    verification_level INT DEFAULT 0,  -- 0=none, 1=basic, 2=enhanced
    verified_at TIMESTAMP,
    verification_provider VARCHAR(50),  -- stripe, onfido, custom
    
    -- Audit Trail
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,  -- Soft delete for GDPR
    
    INDEX idx_user_id (user_id),
    INDEX idx_wallet (wallet_address),
    INDEX idx_verification_level (verification_level),
    INDEX idx_created_at (created_at)
);

-- OFAC Sanctions Check Table
CREATE TABLE IF NOT EXISTS ofac_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    wallet_address VARCHAR(42) NOT NULL,
    entity_name VARCHAR(255),
    
    -- Check Result
    is_blocked BOOLEAN DEFAULT FALSE,
    match_score FLOAT DEFAULT 0.0,
    matched_entity VARCHAR(255),
    
    -- Audit Trail
    checked_at TIMESTAMP DEFAULT NOW(),
    sdn_list_version VARCHAR(20),
    
    INDEX idx_wallet (wallet_address),
    INDEX idx_is_blocked (is_blocked),
    INDEX idx_checked_at (checked_at)
);

-- Transaction Monitoring Table
CREATE TABLE IF NOT EXISTS transaction_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    transaction_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255),
    wallet_from VARCHAR(42),
    wallet_to VARCHAR(42),
    
    -- Transaction Details
    amount_wei NUMERIC(78, 0),  -- Arbitrary precision for big numbers
    amount_usd NUMERIC(18, 2),
    transaction_type VARCHAR(50),  -- mint, transfer, stake, vote, etc
    
    -- Compliance Checks
    kyc_verified BOOLEAN,
    kyc_level INT,
    ofac_blocked BOOLEAN,
    ofac_score FLOAT,
    aml_flagged BOOLEAN,
    sar_filed BOOLEAN,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending',  -- pending, approved, rejected, flagged
    rejection_reason TEXT,
    
    -- Audit Trail
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP,
    blockchain_hash VARCHAR(66),  -- Ethereum tx hash
    
    INDEX idx_user_id (user_id),
    INDEX idx_wallet_from (wallet_from),
    INDEX idx_wallet_to (wallet_to),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_aml_flagged (aml_flagged),
    INDEX idx_sar_filed (sar_filed)
);

-- Suspicious Activity Reports (SARs) for FinCEN
CREATE TABLE IF NOT EXISTS suspicious_activity_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sar_id VARCHAR(50) UNIQUE NOT NULL,
    transaction_id UUID REFERENCES transaction_logs(id),
    
    -- Filing Information
    filing_date TIMESTAMP DEFAULT NOW(),
    filing_deadline TIMESTAMP,  -- 30 days from suspicious activity
    filed BOOLEAN DEFAULT FALSE,
    filed_at TIMESTAMP,
    
    -- Suspicious Details
    suspicious_activity_type VARCHAR(100),
    description TEXT NOT NULL,
    amount_involved NUMERIC(18, 2),
    involved_wallets TEXT[],  -- Array of wallet addresses
    
    -- FinCEN Metadata
    fincen_reference_number VARCHAR(50),
    report_status VARCHAR(20),  -- draft, submitted, confirmed
    
    INDEX idx_transaction_id (transaction_id),
    INDEX idx_filing_date (filing_date),
    INDEX idx_filed (filed),
    INDEX idx_sar_id (sar_id)
);

-- Audit Log for All Compliance Operations
CREATE TABLE IF NOT EXISTS compliance_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action_type VARCHAR(100) NOT NULL,  -- verify_kyc, check_ofac, file_sar, etc
    actor_id VARCHAR(255),
    target_user_id VARCHAR(255),
    target_wallet VARCHAR(42),
    
    -- Details
    action_description TEXT,
    result VARCHAR(20),  -- success, failure
    error_message TEXT,
    
    -- Metadata
    ip_address INET,
    user_agent TEXT,
    correlation_id VARCHAR(255),
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_action_type (action_type),
    INDEX idx_actor_id (actor_id),
    INDEX idx_target_user_id (target_user_id),
    INDEX idx_created_at (created_at)
);

-- Data Deletion Requests (GDPR/CCPA)
CREATE TABLE IF NOT EXISTS deletion_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    request_type VARCHAR(20),  -- gdpr, ccpa
    
    -- Timeline
    requested_at TIMESTAMP DEFAULT NOW(),
    deadline TIMESTAMP,  -- 30 days from request
    completed_at TIMESTAMP,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending',  -- pending, processing, completed, cancelled
    completion_summary TEXT,
    
    -- Audit
    requested_by VARCHAR(255),  -- email or admin id
    notes TEXT,
    
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_requested_at (requested_at),
    INDEX idx_deadline (deadline)
);

-- Blockchain Transaction Cache
-- For mapping blockchain events back to compliance logs
CREATE TABLE IF NOT EXISTS blockchain_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100),  -- Transfer, Mint, Approval, etc
    transaction_hash VARCHAR(66) UNIQUE,
    block_number BIGINT,
    
    -- Contract Info
    contract_address VARCHAR(42),
    from_address VARCHAR(42),
    to_address VARCHAR(42),
    
    -- Value
    value_wei NUMERIC(78, 0),
    value_usd NUMERIC(18, 2),
    
    -- Status
    is_confirmed BOOLEAN DEFAULT FALSE,
    confirmations INT DEFAULT 0,
    
    -- Compliance Link
    transaction_log_id UUID REFERENCES transaction_logs(id),
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_transaction_hash (transaction_hash),
    INDEX idx_block_number (block_number),
    INDEX idx_from_address (from_address),
    INDEX idx_to_address (to_address),
    INDEX idx_is_confirmed (is_confirmed)
);

-- OFAC SDN List Cache
CREATE TABLE IF NOT EXISTS ofac_sdn_cache (
    id BIGINT PRIMARY KEY,
    name VARCHAR(500),
    entity_type VARCHAR(50),
    programs TEXT[],
    addresses TEXT[],
    crypto_addresses TEXT[],
    
    -- Metadata
    last_updated TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    INDEX idx_name (name),
    INDEX idx_entity_type (entity_type),
    INDEX idx_is_active (is_active)
);

-- Create indexes for common queries
CREATE INDEX idx_kyc_verification_status ON kyc_verifications(verification_level, verified_at DESC);
CREATE INDEX idx_transaction_date_range ON transaction_logs(created_at DESC, status);
CREATE INDEX idx_ofac_check_status ON ofac_checks(is_blocked, checked_at DESC);
CREATE INDEX idx_sar_filing_status ON suspicious_activity_reports(filing_date DESC, filed);

-- Create view for compliance dashboard
CREATE VIEW compliance_dashboard AS
SELECT 
    (SELECT COUNT(*) FROM kyc_verifications WHERE verified_at IS NOT NULL) as kyc_verified_count,
    (SELECT COUNT(*) FROM transaction_logs WHERE created_at > NOW() - INTERVAL '24 hours') as transactions_24h,
    (SELECT COUNT(*) FROM transaction_logs WHERE aml_flagged = TRUE AND status != 'processed') as pending_aml_flags,
    (SELECT COUNT(*) FROM suspicious_activity_reports WHERE filed = FALSE AND filing_deadline < NOW()) as overdue_sars,
    (SELECT COUNT(*) FROM ofac_checks WHERE is_blocked = TRUE AND checked_at > NOW() - INTERVAL '7 days') as recent_blocks;

-- Set permissions
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
GRANT ALL ON ALL TABLES IN SCHEMA public TO dcmx_app;
