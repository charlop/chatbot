# Pending Decisions - Contract Refund Eligibility System

**Last Updated:** 2025-11-06
**Status:** Pre-Architecture Phase - Awaiting Critical Decisions

## Overview

This document tracks all pending decisions that must be resolved before architecture and design work can proceed. Items are prioritized by their blocking impact on system design.

---

## CRITICAL BLOCKERS 🚨

These items **MUST** be resolved before beginning architecture work. Each blocks fundamental design decisions.

### 1. Data Retention Policy

**Category:** Compliance / Storage Architecture
**Priority:** CRITICAL
**Status:** ❌ UNDEFINED

**Current Ambiguity:**
- Requirements document suggests "7 years?" but this is unconfirmed
- No specification for audit log retention
- PII handling requirements unclear
- Data deletion/purging policies undefined

**Information Needed:**
- [ ] Legal/regulatory requirements for contract document retention
  - ANSWER: 7 years in prod (although indefinitely is fine too). Much shorter in lower environments.
- [ ] Audit log retention period (separate from document retention)
  - ANSWER: user actions need to be retained for at least 7 (again, indefinitely is fine). Much shorter in lower environments
- [ ] PII/sensitive data handling requirements (encryption, masking, anonymization)
  - ANSWER: We do not store PII/sensitive data. These are template forms, not filled out documents
- [ ] Data deletion policies (right to be forgotten, contract expiration)
  - ANSWER: Right to be forgotten does not apply (not storing PII). Contract expiration also does not apply.
- [ ] Backup retention and archival strategy
  - ANSWER: Leverage AWS services as much as possible. Not sure about archival. Maybe we take that as a day 2.

**Impact if Not Resolved:**
- **BLOCKS:** Database schema design (partitioning strategy)
- **BLOCKS:** Storage architecture (hot/warm/cold data tiers)
- **BLOCKS:** Backup and disaster recovery design
- **BLOCKS:** Cost modeling and capacity planning
- **BLOCKS:** Compliance framework implementation

**Suggested Default (if decision delayed):**
- 7 years for contract documents (financial services standard)
- 10 years for audit logs (longer than data for compliance)
- S3 with lifecycle policies: Hot (1 year) → Warm (2-7 years) → Glacier (7+ years)
- ANSWER: These are reasonable

**Stakeholders:** Legal, Compliance, Finance

---

### 2. LLM Model Selection

**Category:** Technical / Integration
**Priority:** CRITICAL
**Status:** ❌ UNDEFINED

**Current Ambiguity:**
- No model vendor selected
- No cost constraints defined
- Latency requirements unclear
- Prompt management strategy undefined

**Information Needed:**
- [ ] Budget constraints for LLM API calls ($/month, $/1000 tokens)
  - ANSWER: Not relevant. We will use enterprise API endpoints. We can change endpoints as needed.
- [ ] Latency requirements (max response time for extraction)
  - ANSWER: 5-10s is totally fine, performance not a concern
- [ ] Accuracy expectations (minimum acceptable confidence)
  - ANSWER: Accuracy matters, but model selection is not important yet.
- [ ] Vendor preferences and lock-in concerns
  - ANSWER: Not relevant
- [ ] Model capabilities required (multimodal, function calling, JSON mode)
  - ANSWER: Function calling and structured output required.
- [ ] Prompt versioning and governance strategy
  - ANSWER: Will use git, do we need something more sophisticated? Governance and OPM will be reviewed quarterly
- [ ] Fallback model for cost/availability issues
  - ANSWER: N/A

**Vendor Options:**
| Vendor | Model | Cost | Latency | Notes |
|--------|-------|------|---------|-------|
| OpenAI | GPT-4 Turbo | $$$ | Fast | Mature, reliable |
| Anthropic | Claude 3.5 Sonnet | $$$ | Fast | Strong reasoning, long context |
| AWS Bedrock | Multiple | $-$$$ | Variable | AWS integration, multi-model |
| Azure OpenAI | GPT-4 | $$$ | Fast | Enterprise features |

**Impact if Not Resolved:**
- **BLOCKS:** API integration architecture
- **BLOCKS:** Cost structure and rate limiting design
- **BLOCKS:** Response time optimization strategy
- **BLOCKS:** Prompt versioning and management approach
- **BLOCKS:** Vendor contract negotiations

**Suggested Default (if decision delayed):**
- Start with Claude 3.5 Sonnet (strong document understanding)
- Budget: $2,000/month for 100-1,000 contracts/day
- Fallback to GPT-4 Turbo if Claude unavailable
- Implement abstraction layer for vendor switching

**Stakeholders:** Technical Lead, Finance, Procurement

---

### 3. SLA Requirements

**Category:** Business / Infrastructure
**Priority:** CRITICAL
**Status:** ❌ UNDEFINED

**Current Ambiguity:**
- "<10 sec response time realistic?" mentioned but unconfirmed
- "99.9%?" availability mentioned but unconfirmed
- Peak load expectations undefined
- Maintenance windows not specified

**Information Needed:**
- [ ] Target response time for contract processing (p50, p95, p99)
- [ ] System availability requirement (uptime percentage)
- [ ] Acceptable downtime windows for maintenance
- [ ] Peak concurrent users
- [ ] Peak contracts processed per hour/day
- [ ] Geographic distribution of users (impacts latency)
- [ ] Degraded mode acceptable? (e.g., read-only during maintenance)

**Impact if Not Resolved:**
- **BLOCKS:** Infrastructure redundancy requirements
- **BLOCKS:** Caching architecture and optimization needs
- **BLOCKS:** Multi-region deployment decisions
- **BLOCKS:** Database replication and failover design
- **BLOCKS:** Cost estimation for infrastructure

**Suggested Default (if decision delayed):**
- Response time: <10 seconds (p95) for extraction
- Availability: 99.5% (single region, allows 3.6 hours downtime/month)
- Peak load: 100 contracts/hour (burst to 200)
- Maintenance window: Saturday 2-6 AM EST
- ANSWER: These are reasonable.

**Stakeholders:** Business Operations, Technical Lead, Finance

---

### 4. Integration Points & Data Sources

**Category:** Integration / Data Architecture
**Priority:** CRITICAL
**Status:** ❌ UNDEFINED

**Current Ambiguity:**
- "Which upstream systems provide account numbers?" - unknown
- "How are contract IDs currently managed?" - unknown
- No specification of data formats or APIs

**Information Needed:**
- [ ] Complete list of upstream systems (source of account numbers)
  - ANSWER: Relational database, our code (or AI agent) will probably run a tool call
- [ ] Complete list of downstream systems (consumers of extracted data)
  - ANSWER: End-users primarily. We will also store structured data in Dynamo or Relational DB
- [ ] Contract ID generation and management system
  - ANSWER: This will come from our existing relational DB. Contract IDs are loaded in nightly batch
- [ ] Data formats for each integration (REST API, file feed, database)
  - ANSWER: PDFs are binary, most other responses will be REST API.
- [ ] Authentication mechanisms (OAuth, API keys, IAM)
  - ANSWER: User auth through external provider (e.g. Auth0). APIs will use JWT Bearer tokens
- [ ] Data synchronization requirements and frequency
  - ANSWER: Whatever is in our external database. Eventual consistency is fine, not super time-critical
- [ ] Error handling for integration failures
  - ANSWER: handle gracefully, present error message. Nothing too complicated.
- [ ] Master data management system (if exists)
  - ANSWER: What is this? Do we need it?

**Current System Integrations (to be confirmed):**
| System | Purpose | Format | Auth | Frequency |
|--------|---------|--------|------|-----------|
| CRM? | Account lookup | ? | ? | Real-time? |
| Document Repository | PDF retrieval | Known | ? | Real-time |
| Finance System? | Post extracted data | ? | ? | ? |

**Impact if Not Resolved:**
- **BLOCKS:** Database schema design (external keys)
- **BLOCKS:** API gateway and integration middleware design
- **BLOCKS:** Authentication/authorization requirements
- **BLOCKS:** Data validation and referential integrity
- **BLOCKS:** End-to-end testing strategy

**Suggested Default (if decision delayed):**
- Assume REST APIs for all integrations
- Implement API gateway with abstraction layer
- Design for eventual consistency
- Build mock services for development

**Stakeholders:** Enterprise Architecture, System Owners, Technical Lead

---

## HIGH PRIORITY BLOCKERS ⚠️

These items should be resolved early in architecture phase. They impact significant design decisions but workarounds exist.

### 5. User Roles & Permissions

**Category:** Security / UX
**Priority:** HIGH
**Status:** ❌ UNDEFINED

**Current Ambiguity:**
- "Beyond admin, what permission levels needed (viewer, validator, approver)?"
- No permission matrix defined
- Multi-tenancy requirements unclear

**Information Needed:**
- [ ] Complete role hierarchy (all roles)
  - ANSWER: Day 2 priority. Probably Operations, Admin, and Read-Only
- [ ] Permission matrix for each role
  - ANSWER: Day 2 priority
- [ ] Multi-tenant requirements (separate customers/organizations?)
  - ANSWER: no multi-tenant
- [ ] Delegation capabilities
  - ANSWER: What does this mean? I don't think we need it
- [ ] Approval workflows and authorities
  - ANSWER: Keep it simple. Just an authorized user clicking Approve
- [ ] Session timeout requirements
  - ANSWER: we can configure this later
- [ ] MFA requirements per role
  - ANSWER: We are not implementing auth. Just integrating with a provider.

**Suggested Role Structure:**
| Role | View | Search | Validate | Edit | Approve | Admin |
|------|------|--------|----------|------|---------|-------|
| Viewer | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| Validator | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| Approver | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| Admin | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Auditor | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ (read-only audit logs) |

**Impact if Not Resolved:**
- Authentication and authorization architecture
- RBAC implementation complexity
- Audit trail requirements per role
- UI/UX design for different user types

**Suggested Default (if decision delayed):**
- Implement flexible RBAC with Auth0/Okta
- Start with basic roles: Admin, User
- Add granular permissions in Phase 2

**Stakeholders:** Security, Business Operations, Compliance

---

### 6. State-Specific Rules Management

**Category:** Technical / Business Logic
**Priority:** HIGH
**Status:** ❌ UNDEFINED

**Current Ambiguity:**
- "Rule engine design (database-driven vs. code-based)"
- "Who maintains state-specific logic—ops team or developers?"
- Number of states to support unclear

**Information Needed:**
- [ ] Number of states to support initially (Phase 1)
  - ANSWER: Probably not a workflow even. User searches by Account Number. If it hasn't been reviewed, we pull up the data (if it exists in our system) and they review/approve it. Done.
- [ ] Number of states in roadmap (future phases)
  - ANSWER: N/A
- [ ] Frequency of rule changes (weekly? monthly? quarterly?)
  - ANSWER: N/A
- [ ] Technical capability of rule maintainers
  - ANSWER: N/A
- [ ] Approval workflow required before rule activation?
  - ANSWER: N/A
- [ ] Rule versioning requirements
  - ANSWER: N/A
- [ ] Effective date requirements (when do rules take effect?)
  - ANSWER: N/A
- [ ] Backward compatibility needs (old contracts with old rules?)
  - ANSWER: N/A

**Architecture Options:**
| Option | Pros | Cons | Best For |
|--------|------|------|----------|
| **Code-based** | Fast, type-safe, version controlled | Requires deployments, developer changes | Few states, rare changes |
| **Database rules** | Non-technical updates, no deployments | Complex testing, harder debugging | Many states, frequent changes |
| **Rules engine** (Drools, etc.) | Powerful, flexible, auditable | Added complexity, learning curve | Complex rules, compliance needs |

**Impact if Not Resolved:**
- Business logic architecture
- Testing strategy for state variations
- Deployment and versioning approach
- Non-technical user capabilities

**Suggested Default (if decision delayed):**
- Start with database-driven rules (JSON config per state)
- Implement simple rule version control
- Build admin UI for rule management
- Plan migration to rules engine if complexity grows

**Stakeholders:** Business Operations, Technical Lead, Product

---

### 7. Escalation & Approval Hierarchy

**Category:** Business Process / Workflow
**Priority:** HIGH
**Status:** ❌ UNDEFINED

**Current Ambiguity:**
- "Who reviews flagged low-confidence extractions?"
- "What's the approval hierarchy?"
- Confidence thresholds not defined

**Information Needed:**
- [ ] Confidence threshold for automatic approval
  - ANSWER: Configurable, depends on UAT. Start with 80%
- [ ] Confidence threshold for flagging "needs review"
  - ANSWER: Everything needs review. Human must review and approve.
- [ ] Escalation tiers and routing logic
  - ANSWER: N/A. This process is done during contract termination. It is not a time-sensitive thing. If it's not done today, it can wait until tomorrow.
- [ ] Notification mechanisms (email, in-app, SMS)
  - ANSWER: N/A
- [ ] SLAs per escalation level
  - ANSWER: N/A
- [ ] Override capabilities and approval authority
  - ANSWER: N/A
- [ ] After-hours handling (on-call? queue until morning?)
  - ANSWER: N/A

**Suggested Escalation Flow:**
```
Confidence >= 95% → Auto-approve
Confidence 85-94% → Operations staff review
Confidence 70-84% → Finance specialist review
Confidence < 70% → Senior finance + manual extraction

Override authority:
- Operations: Can approve 85-94%
- Finance: Can approve 70-94%
- Senior Finance: Can approve any
- Admin: Can approve any
```

**Impact if Not Resolved:**
- Workflow engine design
- Notification and queue management
- Business logic for routing decisions
- SLA tracking per level

**Suggested Default (if decision delayed):**
- Simple two-tier: Auto (>90%) or Manual review (<90%)
- Email notifications for flagged items
- No complex routing in Phase 1

**Stakeholders:** Business Operations, Finance, Management

---

### 8. Deployment Model & Disaster Recovery

**Category:** Infrastructure / Compliance
**Priority:** HIGH
**Status:** ❌ UNDEFINED

**Current Ambiguity:**
- "Multi-region? Disaster recovery requirements?"
- RTO/RPO not specified
- Data residency requirements unclear

**Information Needed:**
- [ ] Single region vs. multi-region deployment
  - ANSWER: Single region
- [ ] Recovery Time Objective (RTO) - max downtime
  - ANSWER: Not important. Standard availability. Not business critical.
- [ ] Recovery Point Objective (RPO) - max data loss
  - ANSWER: N/A
- [ ] Geographic redundancy requirements
  - ANSWER: N/A
- [ ] Data residency/sovereignty requirements
  - ANSWER: N/A
- [ ] Compliance requirements for data location
  - ANSWER: N/A
- [ ] Backup frequency and retention
  - ANSWER: What even needs to be backed up manually, that isn't handled by AWS?

**Deployment Options:**
| Option | Cost | Complexity | RTO | RPO | Best For |
|--------|------|------------|-----|-----|----------|
| **Single region, single AZ** | $ | Low | Hours | 1 hour | Development only |
| **Single region, multi-AZ** | $$ | Medium | Minutes | 5 min | Standard production |
| **Multi-region active-passive** | $$$ | High | 15 min | 5 min | High availability |
| **Multi-region active-active** | $$$$ | Very High | Seconds | Near-zero | Mission-critical |

**Impact if Not Resolved:**
- Infrastructure complexity and cost
- Data replication strategy
- Failover automation requirements
- Compliance risk

**Suggested Default (if decision delayed):**
- Single region (US-East-1), multi-AZ for Phase 1
- RTO: 4 hours, RPO: 1 hour
- Daily backups retained 30 days
- Plan multi-region for Phase 2

**Stakeholders:** Technical Lead, Compliance, Finance

---

## MEDIUM PRIORITY 🔸

These items should be clarified during architecture phase but have reasonable defaults.

### 9. Performance Caching Strategy

**Category:** Technical / Performance
**Priority:** MEDIUM
**Status:** ❌ UNDEFINED

**Current Ambiguity:**
- "Need caching strategy for frequently accessed contracts?"
- Access patterns not analyzed

**Information Needed:**
- [ ] Access patterns (read-heavy vs. write-heavy)
- [ ] Cache hit ratio expectations
- [ ] Acceptable data staleness
- [ ] Cache warming strategies
- [ ] Frequently accessed data types

**Suggested Default:**
- Redis for session and recently processed contracts
- CloudFront CDN for PDF serving
- Application-level caching for extracted data (1 hour TTL)
- No cache warming in Phase 1
- ANSWER: This is reasonable.

**Stakeholders:** Technical Lead

---

### 10. Training Data Usage & Model Improvement

**Category:** Technical / Legal
**Priority:** MEDIUM
**Status:** ❌ UNDEFINED

**Current Ambiguity:**
- "Can we use corrected extractions to fine-tune/improve the model over time?"

**Information Needed:**
- [ ] Legal clearance for using contract data in training
  - ANSWER: N/A
- [ ] Customer consent requirements
  - ANSWER: N/A
- [ ] Data anonymization requirements
  - ANSWER: N/A
- [ ] Model retraining frequency and process
  - ANSWER: Day 2
- [ ] Vendor terms regarding fine-tuning
  - ANSWER: N/A

**Suggested Default:**
- Store corrections in separate analytics database
- Do NOT send to LLM vendor for training in Phase 1
- Evaluate fine-tuning in Phase 2 after legal review

**Stakeholders:** Legal, Technical Lead, Data Science

---

### 11. Bulk Operations & Queue Management

**Category:** UX / Technical
**Priority:** MEDIUM
**Status:** ❌ UNDEFINED

**Current Ambiguity:**
- "Process multiple contracts in queue with priority handling"
- Batch size and priority rules not defined

**Information Needed:**
- [ ] Maximum batch size for bulk operations
- [ ] Priority rules (FIFO, by customer, by contract value, by deadline)
- [ ] Bulk approval vs. individual review requirements
- [ ] Partial batch failure handling
- [ ] Progress reporting requirements

**Suggested Default:**
- Simple FIFO queue in Phase 1
- Batch size: 50 contracts
- Individual review required (no bulk approve in Phase 1)
- AWS SQS for job queue
- ANSWERS: Day 2 priority. Maybe not even in scope.

**Stakeholders:** Business Operations, Technical Lead

---

## LOW PRIORITY 🔹

These items can be deferred to later phases without blocking architecture.

### 12. Keyboard Shortcuts

**Category:** UX Enhancement
**Priority:** LOW
**Status:** ❌ UNDEFINED

**Suggested Default:**
- Defer to Phase 2
- Basic shortcuts: Tab, Enter, Esc only in Phase 1
- ANSWER: Fine for now.

**Stakeholders:** UX, Product

---

## GAPS IN REQUIREMENTS 🕳️

These items were not explicitly mentioned but should be addressed.

### 13. Confidence Scoring Thresholds

**Category:** Technical / Business
**Priority:** HIGH
**Status:** ❌ UNDEFINED

**What's Missing:**
- No defined thresholds for confidence levels
- No specification of how confidence is calculated
- No guidance on visual indicators

**Recommended Resolution:**
- Define in stakeholder workshop with historical data
- Suggested thresholds: High (>90%), Medium (70-90%), Low (<70%)
- ANSWER: This is reasonable

---

### 14. Error Recovery & Fallback Procedures

**Category:** Technical / Business
**Priority:** HIGH
**Status:** ❌ UNDEFINED

**What's Missing:**
- No specification of retry logic
- No timeout values
- No circuit breaker thresholds
- No manual fallback workflow

**Recommended Resolution:**
- Define as part of technical architecture
- Suggested: 3 retries, 30s timeout, circuit opens after 5 failures
- ANSWER: Sounds reasonable

---

### 15. User Persona Specifics

**Category:** UX / Business
**Priority:** MEDIUM
**Status:** ❌ PARTIALLY DEFINED

**What's Missing:**
- Specific tasks per persona not detailed
- Technical proficiency levels unknown
- Training availability unclear

**Recommended Resolution:**
- Conduct user interviews with 3-5 operations staff
- Conduct user interviews with 3-5 finance specialists
- Document workflows, pain points, technical capabilities
- ANSWER: Single persona, this is an enterprise app. Not an important factor.

---

## Decision Log

Track all decisions as they are made.

| ID | Decision | Date | Decided By | Rationale | Impact |
|----|----------|------|------------|-----------|--------|
| - | - | - | - | - | - |

---

## Architecture Readiness Score

**Current Status: 0/15 Critical & High Priority Items Resolved (0%)**

**Can Begin Architecture When:**
- ✅ All 4 Critical items resolved (0/4)
- ✅ At least 3/4 High Priority items resolved (0/4)
- ✅ Stakeholder sign-off obtained

**Go/No-Go Decision:** ❌ NOT READY - Resolve critical blockers first
