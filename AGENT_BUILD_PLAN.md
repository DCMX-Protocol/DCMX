# DCMX Multi-Agent Build Plan

**Date**: December 9, 2025  
**Status**: Scaffolding Complete ✅

---

## 📋 Summary

You now have 4 specialized AI agents ready to build different components of DCMX:

1. **Blockchain Agent** - Smart contracts, NFTs, tokens
2. **Audio Agent** - Watermarking, fingerprinting, DRM
3. **Compliance Agent** - KYC/AML, OFAC, audit logging
4. **LoRa Agent** - Mesh networking, bandwidth rewards

---

## 📁 Directory Structure Created

```
dcmx/
├── agents/              # Multi-agent orchestration
│   ├── __init__.py
│   └── orchestrator.py  # MultiAgentOrchestrator class
├── blockchain/          # Web3 smart contracts
│   ├── __init__.py
│   ├── contract_manager.py
│   └── blockchain_agent.py
├── audio/              # Audio processing
│   ├── __init__.py
│   ├── audio_watermark.py
│   └── audio_fingerprint.py
├── compliance/         # Regulatory compliance
│   ├── __init__.py
│   ├── kyc_verifier.py
│   └── ofac_checker.py
└── lora/              # Mesh networking
    ├── __init__.py
    └── lora_node.py
```

---

## 🚀 How to Use This Setup

### For Each Agent

1. **Read** `.github/copilot-instructions.md` (full compliance + architecture guide)
2. **Read** `AGENTS.md` (agent-specific quick start)
3. **Review** the skeleton files in their module
4. **Implement** the TODO items marked in code

### For Coordination

1. Use `MultiAgentOrchestrator` to register agents
2. Share state through orchestrator's `get_shared_state()`/`set_shared_state()`
3. Follow integration points table in `AGENTS.md`

---

## 🎯 Key Implementation Tasks

### Blockchain Agent (`dcmx/blockchain/blockchain_agent.py`)

**Solidity Contracts to Deploy**:
- `MusicNFT.sol` (ERC-721) - Limited edition music NFTs
- `DCMXToken.sol` (ERC-20) - Utility token
- `GovernanceDAO.sol` - Voting contract
- `RewardDistributor.sol` - Token payouts

**Python Methods to Complete**:
- [ ] `BlockchainAgent.mint_nft()` - Build and sign NFT mint transaction
- [ ] `BlockchainAgent.distribute_rewards()` - Build and sign reward distribution
- [ ] `ContractManager.load_contract()` - Parse ABI and load contract instances
- [ ] Gas estimation and transaction tracking

**Dependencies**:
```bash
pip install web3 eth-brownie eth-keys
export ETHEREUM_RPC_URL="https://..."
```

---

### Audio Agent (`dcmx/audio/`)

**Implementations to Complete**:
- [ ] `AudioWatermark.embed()` - FFT-based watermarking (ISO/IEC 18040)
- [ ] `AudioWatermark.verify()` - Extract and validate watermark
- [ ] `AudioFingerprint.generate()` - MFCC perceptual hashing (like Shazam)
- [ ] `AudioFingerprint.match_similarity()` - Fuzzy matching algorithm
- [ ] Test compression robustness (MP3, AAC)

**Key Algorithm**: Constellation maps for landmark-based fingerprinting

**Dependencies**:
```bash
pip install librosa pydub soundfile essentia cryptography
```

---

### Compliance Agent (`dcmx/compliance/`)

**Implementations to Complete**:
- [ ] `KYCVerifier.verify_user()` - Integrate with KYC provider (Stripe, Onfido)
- [ ] `OFACChecker.load_sdn_list()` - Download weekly SDN list from Treasury
- [ ] `OFACChecker.check_address()` - Sanctions list lookups
- [ ] `TransactionMonitor.validate_transaction()` - AML rules engine
  - >$10K → File FinCEN SAR
  - Structuring detection
  - Velocity checks
  - Geographic blocks
- [ ] `ComplianceDatabase` - Encrypted KYC storage, separate from transaction data

**Regulatory Requirements**:
- KYC threshold: $10K lifetime spend
- OFAC update: Weekly
- SAR filing: Within 30 days
- Audit retention: 7 years

**Dependencies**:
```bash
pip install sqlalchemy cryptography twilio stripe
export DATABASE_URL="postgresql://..."
export ENCRYPTION_KEY="..."
```

---

### LoRa Agent (`dcmx/lora/lora_node.py`)

**Implementations to Complete**:
- [ ] `LoRaNode.broadcast_content()` - LoRa radio transmission
- [ ] `LoRaNode.receive_mesh_packet()` - Packet parsing and routing
- [ ] `MeshRouter.find_route()` - Geographic mesh routing (AODV-based)
- [ ] `RewardCalculator.calculate_period_reward()` - Bandwidth-based token rewards
  - Base: 10 tokens/period
  - Bandwidth: 1 token per 100MB
  - Uptime: +20% for >99%
  - Coverage: +10% for >10 unique peers
- [ ] `BandwidthStats.get_reward_score()` - Weighted metric calculation

**Hardware**: LoRa modem on `/dev/ttyUSB0` (e.g., RasPi with LoRa HAT)

**Dependencies**:
```bash
pip install pylorawan meshtastic aiohttp
# Hardware: LoRa modem device
```

---

## 🔗 Critical Integration Points

| From | To | What |
|------|-----|------|
| Audio Agent | Blockchain Agent | `watermark_hash`, `perceptual_fingerprint` |
| Blockchain Agent | Compliance Agent | Wallet address for KYC/OFAC check |
| Compliance Agent | Blockchain Agent | KYC level, OFAC clearance |
| LoRa Agent | Compliance Agent | Bandwidth stats, uptime metrics |
| Compliance Agent | LoRa Agent | Verified reward eligibility |
| LoRa Agent | Blockchain Agent | Bandwidth proofs for reward distribution |

---

## 📚 Documentation

**Read in This Order**:

1. **`.github/copilot-instructions.md`** (1240 lines)
   - Full architecture
   - Regulatory compliance requirements
   - Development patterns and conventions
   - Critical for all agents

2. **`AGENTS.md`** (This file's companion)
   - Agent-specific quick starts
   - Setup instructions
   - Code examples
   - Integration protocol

3. **Agent Source Files**
   - `dcmx/blockchain/blockchain_agent.py`
   - `dcmx/audio/audio_watermark.py`
   - `dcmx/compliance/kyc_verifier.py`
   - `dcmx/lora/lora_node.py`

---

## ✅ Pre-Implementation Checklist

Before agents start coding:

- [ ] **Legal**: Consult blockchain attorney about token classification (Howey Test)
- [ ] **Legal**: Confirm you own all music being tokenized
- [ ] **Setup**: Polygon testnet RPC endpoint (for gas cost savings)
- [ ] **Setup**: Third-party KYC provider account (Stripe Identity, Onfido)
- [ ] **Setup**: PostgreSQL for compliance data storage
- [ ] **Setup**: LoRa hardware if building mesh network
- [ ] **Crypto**: Generate encryption key for KYC database
- [ ] **Contracts**: Review Solidity patterns for ERC-721 and ERC-20

---

## 🛡️ Regulatory Summary

**Your Token is Likely NOT a Security IF**:
- ✅ Designed as utility (purchasing NFTs, network participation)
- ✅ Energy rewards tied to actual work (not investment returns)
- ✅ Voting is advisory-only (not profit-sharing)
- ✅ Fixed supply (no inflation)

**Your Token IS a Security IF**:
- ❌ Marketed as "will appreciate as platform grows"
- ❌ Voting rewards proportional to holdings
- ❌ Profit distribution to token holders
- ❌ No utility except trading

---

## 📞 Quick References

| Need | Resource |
|------|----------|
| Smart contract audit template | Search "smart contract audit checklist" |
| OFAC SDN list | https://home.treasury.gov/policy-issues/financial-sanctions/sdn-list |
| FinCEN SAR form | https://www.fincen.gov/suspicious-activity-report |
| Polygon RPC endpoints | https://polygon.technology/developers |
| Audio watermarking | ISO/IEC 18040-1:2021 |
| LoRa specification | https://lora-alliance.org/lorawan-for-developers/ |

---

## 🎓 Next Steps

### For the Blockchain Agent:
1. Set up Hardhat or Brownie development environment
2. Implement ERC-721 and ERC-20 test contracts on Sepolia testnet
3. Deploy RewardDistributor contract with time-locked distributions
4. Create governance voting system with multi-sig execution

### For the Audio Agent:
1. Integrate librosa for MFCC extraction
2. Implement FFT-based watermarking in low-frequency band
3. Test watermark survival through MP3 re-encoding at various bitrates
4. Build fingerprint similarity matching algorithm

### For the Compliance Agent:
1. Spin up PostgreSQL instance with encryption-at-rest
2. Integrate with Stripe Identity for KYC verification
3. Set up weekly OFAC SDN list download and parsing
4. Build transaction monitoring with rule engine (AML rules)

### For the LoRa Agent:
1. Design mesh routing protocol (AODV-based)
2. Implement bandwidth accounting and metrics
3. Build reward calculation with auditable proofs
4. Create geographic routing with geohashing

---

## 📊 Expected Outcomes

After agents complete their work, you will have:

- ✅ Smart contracts deployed on Polygon (mainnet or testnet)
- ✅ Audio watermarking preventing casual copying
- ✅ Full KYC/AML/OFAC compliance infrastructure
- ✅ LoRa mesh network with bandwidth incentives
- ✅ 7-year immutable audit trail
- ✅ Token distribution mechanism tied to actual work
- ✅ All regulatory checklists passed

---

**Good luck! This is an ambitious but achievable build. 🚀**
