# Stakeholder Questions - Contract Refund Eligibility System

**Purpose:** This document contains specific questions for stakeholders to resolve critical blockers and high-priority decisions before architecture work begins.

**Instructions:** Send the relevant section to each stakeholder group. Track responses in the Decision Log section of `pending-decisions.md`.

---

## For Legal & Compliance Team

**Priority:** CRITICAL
**Estimated Time:** 30 minutes
**Contact:** [Legal Team Lead Name/Email]

### Data Retention & Privacy

1. **Contract Document Retention**
   - What is the regulatory requirement for retaining contract documents in our industry?
   - Are there state-specific variations in retention requirements?
   - Suggested answer if unsure: 7 years (standard for financial services)

2. **Audit Log Retention**
   - How long must we retain audit logs of user actions and system events?
   - Is this different from document retention requirements?
   - Suggested answer: 10 years (longer than data for compliance)

3. **PII Handling**
   - What PII exists in these contracts (names, addresses, SSN, account numbers)?
   - Do we need to encrypt PII at rest? In transit?
   - Do we need to mask/anonymize PII in audit logs?
   - Are there right-to-be-forgotten requirements?

4. **Data Deletion/Purging**
   - What triggers data deletion (contract expiration, customer request, time-based)?
   - What is the process for purging expired data?
   - Can we soft-delete or must it be hard-deleted?

5. **Training Data Usage**
   - Can we use corrected contract extractions to improve our AI model?
   - Do we need explicit customer consent for this?
   - Must data be anonymized before use in training?
   - Are there restrictions in our vendor contracts (OpenAI, Anthropic, etc.)?

---

## For Enterprise Architecture / System Integration Team

**Priority:** CRITICAL
**Estimated Time:** 45 minutes
**Contact:** [Enterprise Architect Name/Email]

### System Integration Points

1. **Account Number Source**
   - Which system is the authoritative source for account numbers?
   - What API or interface does it expose?
   - Authentication method (OAuth, API keys, IAM)?
   - Is it real-time or batch?

2. **Contract ID Management**
   - How are contract IDs currently generated and managed?
   - Which system owns the contract ID lifecycle?
   - Format/structure of contract IDs?
   - Are they unique across all states/regions?

3. **Upstream Systems (Data Sources)**
   - Please list all systems that this application will integrate with as a consumer:

   | System Name | Purpose | API Type | Auth Method | Frequency | Owner |
   |-------------|---------|----------|-------------|-----------|-------|
   | Example: CRM | Account lookup | REST | OAuth | Real-time | Sales |
   | | | | | | |

4. **Downstream Systems (Data Consumers)**
   - Which systems will consume the extracted refund data?
   - What format do they expect (REST API, file feed, database)?
   - Real-time or batch?

5. **Document Repository Integration**
   - Confirm: We already have OCR'd documents with embeddings?
   - API to retrieve document text by contract ID?
   - PDF download API?
   - Authentication requirements?

6. **Master Data Management**
   - Is there an MDM system for customer/contract master data?
   - How do we handle data consistency across systems?

---

## For Business Operations / Process Owners

**Priority:** CRITICAL & HIGH
**Estimated Time:** 45 minutes
**Contact:** [Operations Manager Name/Email]

### SLA & Performance Requirements

1. **Response Time Expectations**
   - When a user searches for a contract, how quickly do they need results?
   - Suggested targets: <5 sec (search), <10 sec (AI extraction)
   - What percentile matters most? (p50, p95, p99)

2. **Availability Requirements**
   - What system uptime is required? (99%, 99.5%, 99.9%?)
   - 99.5% = 3.6 hours downtime/month
   - 99.9% = 43 minutes downtime/month
   - Can we have scheduled maintenance windows? When?

3. **Volume Expectations**
   - Current: How many contracts are cancelled per month?
   - Peak: What's the highest volume day/week?
   - Concurrent users: How many people will use this simultaneously?
   - Growth: Expected volume increase over next 2 years?

### User Roles & Permissions

4. **User Roles**
   - Please review this proposed role structure. Any changes needed?

   | Role | View | Search | Validate | Edit | Approve | Admin |
   |------|------|--------|----------|------|---------|-------|
   | Viewer | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
   | Operations Staff | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
   | Finance Specialist | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
   | Admin | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
   | Auditor | ✓ (read-only) | ✓ | ✗ | ✗ | ✗ | ✗ |

5. **Approval Workflow**
   - Who can approve high-confidence extractions automatically?
   - Who reviews medium-confidence extractions?
   - Who handles low-confidence or error cases?
   - Are there financial thresholds that require senior approval (e.g., >$10K)?

6. **Escalation Process**
   - When AI confidence is low (<70%), what happens?
   - Who gets notified? How? (email, in-app, SMS)
   - What's the SLA for reviewing flagged items?
   - After-hours handling: on-call person or wait until morning?

### State-Specific Rules

7. **State Complexity**
   - How many states do we need to support in Phase 1?
   - Are state rules simple (2-3 differences) or complex (many variations)?
   - How often do state rules change? (weekly, monthly, quarterly)
   - Who is responsible for maintaining state-specific rules?
   - Do rule changes require approval before activation?

8. **Rule Management Preference**
   - Would you prefer:
     - **Option A:** Developers update rules in code (requires deployment)
     - **Option B:** Business users update rules in admin UI (no deployment)
     - **Option C:** Hybrid (common rules in code, overrides in UI)

### Bulk Operations

9. **Batch Processing**
   - Do users need to process multiple contracts at once?
   - Maximum batch size needed?
   - Can users bulk-approve, or must each be reviewed individually?
   - Priority handling needed (rush jobs, important customers)?

---

## For Finance Team

**Priority:** HIGH
**Estimated Time:** 30 minutes
**Contact:** [Finance Manager Name/Email]

### Cost & Budget

1. **LLM Budget**
   - What's the monthly budget for AI API calls?
   - Rough estimate: $2,000/month for 1,000 contracts (depends on model)
   - Is there a hard cap or can we flex if volume spikes?

2. **Infrastructure Budget**
   - AWS infrastructure estimated at $3,000-5,000/month (depends on SLA)
   - Higher availability (99.9%) costs more than 99.5%
   - Multi-region adds 50-100% cost
   - What's acceptable?

3. **ROI Expectations**
   - What's the manual cost per contract review currently?
   - How many FTE hours saved with automation?
   - Payback period expectations?

### Financial Data Elements

4. **Extracted Fields**
   - Confirm these are the 3 data points to extract:
     1. GAP Insurance Premium (dollar amount)
     2. Refund Calculation Method (pro-rata, rule of 78s, etc.)
     3. Cancellation Fee (dollar amount)
   - Are there additional fields for Phase 1?
   - Are there fields for future phases?

5. **Validation Rules**
   - What validations should we apply to extracted data?
   - Min/max values for premiums and fees?
   - Allowable refund calculation methods?
   - Cross-field validation rules?

6. **Confidence Thresholds**
   - What confidence level is acceptable for auto-approval?
   - Suggested: 95% for auto-approve, 85-95% for review, <85% for manual
   - What's the cost of an error (false approval vs. false rejection)?

---

## For Security Team

**Priority:** HIGH
**Estimated Time:** 20 minutes
**Contact:** [Security Lead Name/Email]

### Security & Access Control

1. **Authentication Provider**
   - Confirm: We're using Auth0 or Okta for SSO?
   - MFA required for all users or only admins?
   - Session timeout requirements?

2. **Authorization Model**
   - Confirm RBAC (role-based access control) is acceptable?
   - Do we need ABAC (attribute-based) for more granular control?
   - Need to support groups/teams (e.g., Florida team vs. Texas team)?

3. **Data Encryption**
   - Encryption at rest required? (RDS encryption, S3 encryption)
   - Encryption in transit required? (TLS 1.2+)
   - Key management: AWS KMS acceptable?

4. **Audit Logging**
   - What events must be logged?
     - User login/logout
     - Data access (view contract)
     - Data modification (edit extraction)
     - Approval/rejection actions
     - Admin actions
     - API calls
   - Log retention: 1 year? 7 years?
   - SIEM integration required?

5. **Vulnerability Scanning**
   - Frequency of security scans (weekly, monthly)?
   - Penetration testing requirements?
   - Compliance frameworks (SOC 2, PCI-DSS, HIPAA)?

---

## For Technical Leadership

**Priority:** CRITICAL
**Estimated Time:** 45 minutes
**Contact:** [CTO / Technical Lead Name/Email]

### LLM Selection

1. **Vendor Preference**
   - Any preference between OpenAI, Anthropic, AWS Bedrock, Azure OpenAI?
   - Factors to consider:
     - Cost
     - Latency
     - Accuracy
     - Vendor lock-in
     - Enterprise support
     - Data privacy/residency

2. **Model Requirements**
   - What minimum capabilities needed?
     - Multimodal (text + images)?
     - Function calling (structured output)?
     - JSON mode?
     - Long context window (100K+ tokens)?

3. **Fallback Strategy**
   - Should we support multiple models for redundancy?
   - Cost-based routing (cheap model first, expensive if low confidence)?
   - Performance-based routing (fast model first, accurate model if uncertain)?

### Infrastructure & DevOps

4. **Deployment Model**
   - Single region acceptable for Phase 1?
   - Suggested: US-East-1 (AWS) or East US (Azure)
   - Multi-region needed immediately or can defer?

5. **Disaster Recovery**
   - Recovery Time Objective (RTO): How long can the system be down?
     - 15 minutes? 1 hour? 4 hours?
   - Recovery Point Objective (RPO): How much data loss is acceptable?
     - 0 (no loss)? 5 minutes? 1 hour?

6. **Environment Strategy**
   - How many environments? (Dev, Staging, Prod minimum?)
   - Separate AWS accounts per environment?
   - Infrastructure as Code preferred (Terraform, CDK)?

### Monitoring & Observability

7. **Monitoring Requirements**
   - Preferred tools: CloudWatch, DataDog, New Relic, Grafana?
   - Metrics to track:
     - API response times
     - LLM accuracy over time
     - Error rates
     - User activity
     - Cost per contract
   - Alerting thresholds and channels (PagerDuty, Slack)?

8. **Logging Strategy**
   - Centralized logging: CloudWatch, ELK stack, Splunk?
   - Log retention: 30 days? 90 days? 1 year?
   - Structured logging (JSON) preferred?

---

## For Product / UX Team

**Priority:** MEDIUM
**Estimated Time:** 30 minutes
**Contact:** [Product Manager Name/Email]

### User Experience

1. **User Personas**
   - Confirm two primary personas:
     - Operations Staff (high volume, speed-focused)
     - Finance Specialists (detailed review, accuracy-focused)
   - Any other personas to consider?

2. **Workflow Priorities**
   - For Operations Staff:
     - What's most important: speed, simplicity, or volume?
     - Acceptable to auto-approve high-confidence results?
   - For Finance Specialists:
     - What's most important: detail, traceability, or flexibility?
     - Need to see full audit trail every time?

3. **Feature Priorities**
   - Phase 1 must-haves (confirm):
     - Search by account number
     - AI extraction display
     - PDF viewer with highlights
     - Approve/reject/edit actions
     - Audit trail
     - Chat interface for additional queries
   - Phase 1 nice-to-haves:
     - Bulk processing
     - Advanced search/filters
     - Export to Excel
     - Dashboard with metrics

4. **Error Handling UX**
   - When AI extraction fails completely, what should user see?
   - When confidence is low (<70%), how should we guide the user?
   - Should we allow manual extraction in the UI or send to separate workflow?

5. **Mobile Requirements**
   - Confirm: Desktop only for Phase 1?
   - Tablet support needed eventually?
   - Mobile phone support needed eventually?

---

## Response Instructions

**Please respond to your section via:**
- Email to: [Project Manager Email]
- Subject: "Contract Refund System - [Your Area] Responses"
- Format: Copy questions and add answers inline

**Deadline:** [Date - ideally within 1 week]

**Questions?** Contact [Project Manager Name] at [Email/Phone]

---

## Response Tracking

| Stakeholder Group | Sent Date | Response Date | Status | Follow-up Needed |
|-------------------|-----------|---------------|--------|------------------|
| Legal & Compliance | | | ⏳ Pending | |
| Enterprise Architecture | | | ⏳ Pending | |
| Business Operations | | | ⏳ Pending | |
| Finance | | | ⏳ Pending | |
| Security | | | ⏳ Pending | |
| Technical Leadership | | | ⏳ Pending | |
| Product / UX | | | ⏳ Pending | |

**Status Legend:**
- ⏳ Pending
- 🔄 In Review
- ✅ Complete
- ⚠️ Needs Follow-up

---

## Next Steps

Once all responses are received:
1. Update `pending-decisions.md` with decisions made
2. Schedule architecture kickoff meeting
3. Create technical architecture document
4. Begin detailed design work
