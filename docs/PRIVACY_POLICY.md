# DCMX Privacy Policy

**Last Updated**: December 9, 2025  
**Effective Date**: December 9, 2025  
**Jurisdiction**: Delaware (USA) with GDPR/CCPA compliance

---

## 1. PRIVACY POLICY SUMMARY

DCMX is committed to protecting your privacy. This policy explains:
- What information we collect
- How we use that information
- Who we share it with
- Your privacy rights
- How long we keep data

**TL;DR**:
- ✓ We collect minimal data (wallet address, optional profile info)
- ✓ We do NOT sell your data to advertisers or marketers
- ✓ We encrypt sensitive data at rest
- ✓ You have rights to access, correct, and delete your data
- ✓ We comply with GDPR and CCPA privacy laws

---

## 2. INFORMATION WE COLLECT

### 2.1 Information You Provide Directly

#### A. Wallet Information
- **What**: Your Ethereum wallet address
- **Why**: Required to participate in DCMX (NFT ownership, token transfers, voting)
- **How Long**: Retained for 7 years for compliance, then deleted

#### B. KYC/Identity Information (Optional, Required for High-Value Transactions)
If you transact above $10,000 USD (cumulative lifetime transactions):
- Full legal name
- Date of birth
- Social Security Number (hashed)
- Physical address
- Proof of identity (selfie + ID photo)
- Country of residence

**Data Protection**:
- Encrypted at rest (AES-256)
- Stored in separate, access-controlled database
- NOT linked to transaction data
- Deleted within 30 days of request (GDPR/CCPA)

#### C. Profile Information (Optional)
- Display name or artist pseudonym
- Email address (for notifications)
- Website or social media links
- Profile picture
- Bio/description

**Note**: Profile information is PUBLIC by default. You control visibility.

#### D. Content You Upload
- Audio files (music)
- Metadata (title, artist, album, release date)
- Artwork (album cover)
- Lyrics or liner notes (if provided)

**Your Rights**:
- You retain all ownership of content
- You control who can access it
- You can delete it anytime (removal from network, blockchain NFT remains)

### 2.2 Information Collected Automatically

#### A. Network Data
- **IP Address**: Your internet connection (used for geolocation, DDoS prevention)
- **Device Information**: Browser, OS, device type
- **Connection Data**: How you connect to Platform (web, mobile app, API)

#### B. Usage Data
- **Actions**: What features you use (upload, mint, trade, vote)
- **Timing**: When you perform actions
- **Performance**: How long actions take, errors encountered
- **Analytics**: Aggregated user behavior patterns

#### C. Blockchain Data
- **Wallet Address**: Public on blockchain (immutable)
- **Transactions**: NFT mints, trades, token transfers (public blockchain)
- **Voting**: Your governance votes (public on-chain, optional privacy via zero-knowledge proofs)
- **Content Hashes**: SHA-256 hashes of audio (cannot be reversed to get audio)

#### D. Cookies & Tracking
- **Session Cookies**: Remember you between page visits (no tracking)
- **Analytics Cookies**: Google Analytics for aggregated usage metrics
- **Preference Cookies**: Your language, display settings

**Opt-Out**: You can disable cookies in browser settings

### 2.3 Information From Third Parties

#### A. KYC Providers
If you complete KYC verification:
- Stripe Identity, Onfido, or custom provider
- They share: Verification result (approved/denied), verification timestamp
- **NOT SHARED**: Your underlying identity data (kept by provider)

#### B. OFAC Sanctions Check
- Treasury Department Specially Designated Nationals (SDN) list
- Public data, no personal information
- We check if your wallet address appears on list
- Result stored: Yes/No, timestamp, score

#### C. Blockchain Data
- Ethereum public ledger
- All transactions are publicly viewable
- DCMX does not control blockchain data

---

## 3. HOW WE USE YOUR INFORMATION

### 3.1 Service Delivery
We use your information to:
- **Authenticate**: Verify wallet ownership
- **Content Management**: Store, organize, serve music content
- **Transactions**: Process NFT mints, trades, token transfers
- **Notifications**: Email you about activities (if opted-in)
- **Payment**: Calculate and distribute rewards

### 3.2 Compliance & Legal
- **KYC/AML**: Verify your identity and check sanctions lists
- **Tax Reporting**: Track transactions for 1099-K reporting
- **Audit Trails**: Maintain 7-year transaction logs for regulatory review
- **Fraud Prevention**: Detect suspicious patterns
- **Law Enforcement**: Respond to valid legal requests

### 3.3 Improving DCMX
- **Analytics**: Understand how users interact with Platform
- **Debugging**: Fix technical issues
- **Features**: Develop new features based on usage data
- **Security**: Identify and fix vulnerabilities

### 3.4 Communication
- **Critical Updates**: Security issues, service changes
- **Optional Marketing**: News about DCMX (only if you opt-in)
- **Support**: Respond to your questions/issues
- **Surveys**: Gather feedback (optional)

### 3.5 What We DON'T Do
- ✗ We do NOT sell your data to advertisers
- ✗ We do NOT share data with data brokers
- ✗ We do NOT use data for behavioral targeting
- ✗ We do NOT combine with social media data (except what you provide)
- ✗ We do NOT create detailed user profiles for marketing

---

## 4. WHO WE SHARE DATA WITH

### 4.1 Service Providers
We share data with third parties only as necessary:

| Provider | Data Shared | Purpose | Contract |
|----------|------------|---------|----------|
| **AWS/Cloud Host** | IP address, usage logs | Server hosting | Data Processing Agreement |
| **Stripe/Onfido** | Identity documents, name, DOB | KYC verification | Separate privacy policy |
| **Ethereum Blockchain** | Wallet address, transactions | NFT/token operations | Public blockchain |
| **OFAC Checker** | Wallet address | Sanctions screening | Government list (public) |
| **Email Provider** | Email address | Notifications | Data Processing Agreement |
| **Analytics (Google)** | Anonymized usage data | Site analytics | Privacy policy applies |
| **Jaeger/Prometheus** | Performance metrics | Monitoring/observability | Only non-personal data |

### 4.2 Legally Required Disclosures
We may disclose information if required by:
- **Subpoena/Court Order**: Law enforcement with warrant
- **Government Agencies**: FBI, IRS, SEC (with legal process)
- **Law Enforcement**: Criminal investigation with warrant
- **Bankruptcy**: Chapter 7 trustee in liquidation

**Note**: We will inform you of requests unless legally prohibited.

### 4.3 Business Transfers
If DCMX is acquired, merged, or dissolved:
- Your data may transfer to acquiring company
- You will be notified of any material changes to this policy
- You have right to delete data instead (GDPR/CCPA)

### 4.4 Aggregated/De-identified Data
We may share:
- Anonymized usage statistics
- Aggregated performance metrics
- De-identified research data
- Public blockchain information (already public)

**Cannot Re-identify**: De-identified data cannot be traced back to you.

---

## 5. DATA SECURITY

### 5.1 Encryption
- **At Rest**: AES-256 encryption for sensitive data (KYC, SSN)
- **In Transit**: TLS 1.3 for all network communications
- **Key Management**: Encryption keys stored separately from data

### 5.2 Access Controls
- **Principle of Least Privilege**: Employees see only data they need
- **Authentication**: Multi-factor authentication for admin access
- **Audit Logging**: All data access logged and monitored
- **Role-Based Access**: Different permissions for different roles

### 5.3 Data Segregation
- **KYC Database**: Separate from transaction/content data
- **Wallet Data**: Separate from personal data
- **Blockchain Data**: Separate from private data
- **No Linking**: Personal data not linked to wallet address in databases

### 5.4 Incident Response
If a data breach occurs:
- **Detection**: 24/7 monitoring for unauthorized access
- **Notification**: Users notified within 30 days per GDPR
- **Investigation**: Full forensic analysis
- **Remediation**: Steps taken to prevent recurrence

---

## 6. YOUR PRIVACY RIGHTS

### 6.1 GDPR Rights (EU Residents)

You have the right to:

#### A. Access
- **What**: Get copy of all personal data we hold
- **How**: Email privacy@dcmx.io with "Data Subject Access Request"
- **Timeline**: Response within 30 days
- **Format**: Machine-readable format (JSON or CSV)

#### B. Correction
- **What**: Fix inaccurate or incomplete data
- **How**: Update profile settings or request via email
- **Timeline**: Changes take effect within 7 days

#### C. Deletion ("Right to be Forgotten")
- **What**: Delete your personal data (with exceptions)
- **How**: Email privacy@dcmx.io with "Deletion Request"
- **Timeline**: Deletion within 30 days
- **Exceptions**: 
  - Tax/compliance data (retained 7 years)
  - Blockchain data (cannot be deleted, immutable)
  - Legal hold due to investigation

#### D. Portability
- **What**: Get your data in portable format to move to another service
- **How**: Email privacy@dcmx.io with "Portability Request"
- **Timeline**: Within 30 days in machine-readable format

#### E. Restrict Processing
- **What**: Stop using your data while investigating issues
- **How**: Email privacy@dcmx.io with "Restriction Request"
- **Timeline**: Restriction applied within 7 days

#### F. Object
- **What**: Opt-out of certain data uses
- **How**: Use settings menu or email privacy@dcmx.io
- **Marketing**: Unsubscribe from all non-critical emails
- **Cookies**: Disable tracking cookies in browser

### 6.2 CCPA Rights (California Residents)

You have the right to:

#### A. Know What Data Is Collected
- Right to request categories and specific data

#### B. Delete
- Delete data collected (with exceptions)
- Same exceptions as GDPR (tax data, blockchain data)

#### C. Opt-Out of Sale
- Right to opt-out of "sale" of personal information
- **Note**: We don't sell data, but we have "Do Not Sell My Personal Information" link

#### D. Non-Discrimination
- DCMX cannot discriminate against you for exercising privacy rights
- Same service, same price, regardless of privacy choices

### 6.3 Other Jurisdiction Rights

**Canada (PIPEDA)**:
- Access and correction rights (similar to GDPR)
- Complaint to Privacy Commissioner

**UK (UK-GDPR)**:
- Same rights as EU GDPR (post-Brexit)

**Australia (Privacy Act)**:
- Notifiable Data Breaches Scheme
- Australian Information Commissioner (OAIC)

### 6.4 How to Exercise Rights

**Email**: privacy@dcmx.io  
**Subject Line**: Specify request type:
- "Data Subject Access Request" (GDPR Article 15)
- "Deletion Request" (GDPR Article 17)
- "Data Portability Request" (GDPR Article 20)
- "CCPA Right to Know" (CCPA §1798.100)
- "CCPA Right to Delete" (CCPA §1798.105)

**Include**:
- Your name
- Email address
- Wallet address (if applicable)
- Specific data request

**Verification**: We will verify your identity before processing request.

---

## 7. DATA RETENTION

### 7.1 Retention Schedule

| Data Type | Retention Period | Reason | Deletion |
|-----------|------------------|--------|----------|
| **KYC/Identity** | 7 years + 90 days | SEC requirements, tax reporting | Auto-delete after 90-day grace |
| **Transaction Logs** | 7 years | IRS/SEC compliance, audit trail | Auto-delete after expiration |
| **IP Logs** | 90 days | Security, abuse prevention | Auto-delete |
| **Cookies** | Session or 1 year | User preference, security | Browser clear, or 1 year auto-delete |
| **Email Address** | Until deleted by user | Notifications, support | On-demand deletion |
| **Profile Data** | Until deleted by user | Account management | On-demand deletion |
| **Content Metadata** | 7 years | Blockchain immutability | Cannot delete (on-chain) |
| **Blockchain Data** | Permanent | Blockchain immutability | Cannot delete (not under our control) |
| **Analytics (anonymized)** | 13 months | Google Analytics default | Google auto-deletes |
| **Support Tickets** | 1 year | Dispute resolution | Auto-delete after 1 year |

### 7.2 Deletion Process
When data is deleted:
1. **Immediate**: Removed from primary database
2. **Within 30 days**: Removed from backups
3. **Verification**: Deletion verified by audit log
4. **Certification**: You receive deletion certificate

---

## 8. COOKIES & TRACKING

### 8.1 Cookie Types

#### Essential Cookies
- **Name**: session_id, auth_token
- **Purpose**: Keep you logged in
- **Duration**: Session (until logout)
- **Disable**: Not recommended (breaks functionality)

#### Analytics Cookies
- **Name**: _ga, _gid (Google Analytics)
- **Purpose**: Understand user behavior (aggregated)
- **Duration**: 2 years
- **Disable**: Browser settings or opt-out link in footer

#### Preference Cookies
- **Name**: language, theme, notifications
- **Purpose**: Remember your preferences
- **Duration**: 1 year
- **Disable**: Browser settings

#### No Advertising Cookies
- We do NOT use cookies for behavioral advertising
- We do NOT track you across sites
- We do NOT build detailed user profiles

### 8.2 How to Control Cookies

**Browser Settings**:
- Open Privacy/Settings
- Find "Cookies and site data"
- Delete or block cookies

**Opt-Out of Analytics**:
- Click "Do Not Track Me" link in footer
- Google Analytics Opt-Out Extension
- Browser "Do Not Track" setting

**Third-Party Cookies**:
- We do NOT allow third-party ad networks
- We do NOT use Facebook Pixel, Google Ads, etc.
- We only use Google Analytics (anonymized)

---

## 9. CHILDREN'S PRIVACY

DCMX is NOT intended for children under 13:
- We do NOT knowingly collect data from users <13
- If we discover child user, we delete their data
- Parents can request deletion anytime

**Parental Rights**:
- Request deletion of child's data
- Request we not collect from child
- Email: privacy@dcmx.io

---

## 10. INTERNATIONAL DATA TRANSFERS

### 10.1 Data Location
- **Primary**: United States (AWS servers)
- **Backup**: Geographic redundancy (EU option available)

### 10.2 EU/UK Data Transfers
For GDPR-protected data transferred to USA:
- **Safeguards**: Standard Contractual Clauses (SCCs)
- **Legitimacy**: SCCs approved by EU Commission
- **Adequacy**: Supplementary safeguards for Schrems II compliance

**Your Rights**:
- You can request EU-only hosting
- Available for additional fee
- Email: privacy@dcmx.io

---

## 11. THIRD-PARTY LINKS & INTEGRATIONS

### 11.1 External Links
DCMX may link to:
- Music streaming services (Spotify, Apple Music)
- Blockchain explorers (Etherscan)
- Social media (Twitter, Discord)

**Disclaimer**: We're not responsible for their privacy practices.

### 11.2 Wallet Providers
If you use MetaMask, WalletConnect, or other providers:
- Their privacy policies apply
- DCMX doesn't control their data collection
- Review their privacy policies separately

---

## 12. BLOCKCHAIN PRIVACY CONSIDERATIONS

### 12.1 Public Data
Everything on Ethereum blockchain is permanent and public:
- **Wallet Address**: Your transactions forever visible
- **NFT Transfers**: Who owned what NFT, when
- **Token Transfers**: Your token movements visible
- **Voting**: Optional: your votes can be public or private (via zero-knowledge proofs)

### 12.2 Pseudonymity (Not Anonymity)
- Blockchain gives you **pseudonymity** (anonymous wallet address)
- NOT true anonymity (wallet can be linked to identity via exchange transactions)
- **IP Address**: Your internet provider may see you're a crypto user

### 12.3 Privacy-Preserving Features
DCMX implements:
- **Zero-Knowledge Proofs**: Prove voting without revealing vote
- **Wallet Mixing**: Optional coin mixing for privacy
- **Multiple Wallets**: Use different wallets for different purposes

---

## 13. ANALYTICS & PERFORMANCE

### 13.1 Google Analytics
- **Data Collected**: Pages visited, actions performed, referral source
- **Retention**: 14 months (aggregated)
- **NOT Collected**: Personal identifiable information
- **Opt-Out**: Link in footer, or Google Analytics opt-out

### 13.2 Jaeger/Prometheus
- **Data Collected**: Performance metrics, error rates, response times
- **Retention**: 30 days
- **NOT Personal**: No user identifiers or personal data
- **Aggregated**: Only statistics, not individual events

---

## 14. NOTIFICATION OF CHANGES

### 14.1 Policy Updates
- We may update this policy anytime
- **Critical Changes**: Notify via email if you're a user
- **Timeline**: 30 days notice before changes take effect
- **Acceptance**: Continued use = acceptance of new policy

### 14.2 Your Opt-Out Right
If you disagree with policy changes:
- **Right to Delete**: Request all data deleted
- **No Penalty**: No discrimination for declining new policy
- **Continued Access**: Old terms still apply for past data

---

## 15. CONTACT & REQUESTS

### 15.1 Privacy Inquiries

**Email**: privacy@dcmx.io  
**Response Time**: 30 days (GDPR/CCPA required)  
**Include**: Your name, email, wallet address, specific request

### 15.2 Data Subject Access Request (GDPR)

**Email**: privacy@dcmx.io  
**Subject**: "Data Subject Access Request"  
**Include**: Identification + specific data requested  
**Timeline**: 30 days

### 15.3 Deletion Request (GDPR/CCPA)

**Email**: privacy@dcmx.io  
**Subject**: "Deletion Request"  
**Timeline**: 30 days  
**What We Delete**: Personal data (not blockchain data)

### 15.4 Complaints

**GDPR Complaint** (EU/UK):
- Your national Data Protection Authority
- Example (UK): Information Commissioner's Office (ICO)
- Example (EU): Check your country's DPA list

**CCPA Complaint** (California):
- California Attorney General
- California Privacy Protection Agency (CPPA)
- Or file complaint through CCPA website

---

## 16. SECURITY STATEMENT

### 16.1 Encryption
- ✅ AES-256 for sensitive data
- ✅ TLS 1.3 for network traffic
- ✅ Key rotation every 90 days

### 16.2 Access Controls
- ✅ Multi-factor authentication
- ✅ Role-based access control (RBAC)
- ✅ Principle of least privilege
- ✅ Access logging and monitoring

### 16.3 Compliance
- ✅ ISO 27001 (or pending)
- ✅ SOC 2 Type II (or pending)
- ✅ GDPR-compliant
- ✅ CCPA-compliant

### 16.4 What We Can't Guarantee
- ⚠️ 100% security (no system is perfect)
- ⚠️ Protection from state-level attacks
- ⚠️ Protection from your own password compromise
- ⚠️ Private key recovery (blockchain immutability)

---

## 17. FAQ

### Q: Does DCMX sell my data?
**A**: No. We do not sell personal data to advertisers or data brokers. We only share data with service providers under contracts, and only when necessary.

### Q: Can I opt-out of email notifications?
**A**: Yes. Go to Settings > Notifications and uncheck non-critical emails. Critical alerts (security, compliance) cannot be disabled.

### Q: How long do you keep transaction history?
**A**: 7 years for compliance, then deleted. You can export your history anytime.

### Q: Is my voting private?
**A**: Not by default. Votes are public on-chain. But you can use zero-knowledge proofs to vote privately while still proving you voted.

### Q: What if I lose my private key?
**A**: DCMX cannot recover it. The blockchain is immutable. That's why we recommend hardware wallets and secure backups.

### Q: Can I delete my NFTs?
**A**: No. NFTs live on the blockchain forever, controlled by your wallet private key. You can destroy the private key, but the NFT persists.

### Q: How do I delete my account?
**A**: Email privacy@dcmx.io with "Account Deletion Request". We'll delete personal data (not blockchain data) within 30 days.

### Q: Is DCMX covered by GDPR?
**A**: Yes, if you're an EU resident or your data is processed in EU. Same rights apply.

### Q: Is DCMX covered by CCPA?
**A**: Yes, if you're a California resident. Same rights apply.

### Q: Who can I contact with privacy questions?
**A**: Email privacy@dcmx.io. We respond within 30 days.

---

## 18. ACKNOWLEDGMENT

**BY USING DCMX, YOU ACKNOWLEDGE THAT:**
- ✓ You have read and understood this Privacy Policy
- ✓ You understand the privacy risks of blockchain technology
- ✓ You understand your personal data rights
- ✓ You consent to the data practices described here
- ✓ You understand blockchain data is permanent and public

---

## 19. EFFECTIVE DATE & UPDATES

**Current Version**: 1.0  
**Effective Date**: December 9, 2025  
**Last Updated**: December 9, 2025  
**Next Review**: June 9, 2026

---

**Questions about privacy?** Contact: privacy@dcmx.io

DCMX Protocol - December 2025
