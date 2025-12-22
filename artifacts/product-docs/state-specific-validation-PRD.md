# Product Requirements Document (PRD)
## State-Specific Contract Term Validation

**Version:** 1.0
**Date:** 2025-12-19
**Status:** APPROVED - Ready for Implementation
**Project Type:** Enhancement to Existing System

---

## Executive Summary

### Problem Statement

Contract terms for GAP Insurance, Vehicle Service Contracts, and F&I products vary significantly by state jurisdiction due to differing insurance regulations. Currently, our system:
- Extracts contract terms without considering state-specific rules
- Applies generic validation rules regardless of jurisdiction
- Cannot warn users when extracted values violate state-specific requirements
- Lacks visibility into which state's rules apply to each contract

This creates compliance risks and requires manual verification of state-specific requirements by finance operations staff.

### Proposed Solution

Enhance the AI-powered extraction system to:
1. Track which state jurisdiction(s) apply to each contract template
2. Store state-specific validation rules in a flexible database structure
3. Apply appropriate state rules during validation
4. Display state information and validation context to users
5. Handle multi-state contracts with primary jurisdiction and conflict detection

### Key Benefits

- **Compliance:** Automatically validate against state-specific regulatory requirements
- **Risk Reduction:** Flag violations of state-specific rules before approval
- **Efficiency:** Eliminate manual state rule verification
- **Transparency:** Show users which state rules were applied
- **Flexibility:** Non-technical staff can update state rules via admin interface
- **Scalability:** Support all 50 US states with extensibility for future jurisdictions

### Success Criteria

- State-specific rules applied to all 3 extracted fields (GAP Premium, Refund Method, Cancellation Fee)
- Multi-state contracts handled correctly with primary jurisdiction validation
- State information displayed clearly in UI
- Admin interface for managing state rules (no code deployments needed)
- Validation messages include state-specific context
- Complete audit trail of which state rules were applied

---

## Product Overview

### Product Vision

Create an intelligent contract analysis system that automatically applies the correct state-specific regulatory rules, reducing compliance risk while maintaining the speed and efficiency of AI-assisted extraction.

### Product Goals

1. **Jurisdiction Awareness:** Automatically identify and track applicable state jurisdictions for contracts
2. **Rule Management:** Provide flexible, database-driven state-specific validation rules
3. **Multi-State Support:** Handle contracts that apply to multiple states with conflict detection
4. **User Transparency:** Show users which state rules are applied and why validation passed/failed
5. **Admin Control:** Enable non-technical staff to manage state rules without code changes
6. **Audit Compliance:** Maintain complete history of state rules applied to each extraction

### In Scope

- State/jurisdiction tracking for contract templates
- Database-driven state validation rules (JSONB configuration)
- State-specific validation for all 3 extracted fields
- Multi-state contract support with primary jurisdiction
- UI display of state information and validation context
- Admin API endpoints for managing state rules
- Audit trail of state rules applied

### Out of Scope (Future Phases)

- Automatic detection of state from contract PDF content
- State-specific extraction prompts (Phase 3)
- Complex multi-state workflow routing
- State-specific disclosure requirements tracking
- Integration with state regulatory databases
- Mobile/tablet UI for state management

---

## User Personas

### Primary User: Finance Operations Staff

**Profile:**
- **Role:** Finance operations team member processing refund requests
- **Goal:** Quickly verify contract terms comply with state regulations
- **Technical Proficiency:** Moderate (comfortable with web applications)
- **Volume:** Reviews 10-50 contracts per day across multiple states
- **Context:** Desktop environment, needs confidence in state compliance

**Pain Points:**
- Manual verification of state-specific requirements is time-consuming
- Easy to overlook state-specific restrictions (e.g., NY prohibits Rule of 78s)
- No visibility into which state's rules apply to a given contract
- Must reference external state regulation documents

**Needs:**
- Automatic validation against correct state rules
- Clear indication of which state's rules are applied
- Warning when extracted values violate state requirements
- Confidence that state-specific compliance is checked

### Secondary User: Compliance Administrator

**Profile:**
- **Role:** Compliance team member responsible for regulatory adherence
- **Goal:** Ensure all contract processing follows current state regulations
- **Technical Proficiency:** Moderate (not a developer)
- **Volume:** Updates state rules quarterly or when regulations change
- **Context:** Needs to update rules without IT involvement

**Pain Points:**
- State regulations change, but updating validation rules requires developer intervention
- No central place to view all state-specific rules
- Cannot easily compare rules across states
- Difficult to track when rule changes take effect

**Needs:**
- Self-service interface for managing state rules
- Ability to update rules without code deployments
- Rule versioning with effective dates
- Ability to preview impact of rule changes

---

## Functional Requirements

### FR1: Jurisdiction Data Model

**Requirement:** System must support multiple jurisdictions with flexible many-to-many relationship to contracts.

**Acceptance Criteria:**
- ✅ `jurisdictions` table stores all US states (50) plus federal default
- ✅ Each jurisdiction has: ID (e.g., "US-CA"), name, country code, state code
- ✅ `contract_jurisdictions` table enables many-to-many mapping
- ✅ Multi-state contracts supported with `is_primary` flag
- ✅ Jurisdiction effective/expiration dates supported for historical tracking

**User Story:**
> As a finance operations staff member, I need to know which state(s) apply to a contract template so I can understand which regulations govern its terms.

### FR2: State-Specific Validation Rules

**Requirement:** System must store and apply state-specific validation rules for each extracted field.

**Acceptance Criteria:**
- ✅ `state_validation_rules` table stores rules with JSONB configuration
- ✅ Rules support numeric ranges (min/max) for GAP Premium and Cancellation Fee
- ✅ Rules support allowed/prohibited values for Refund Calculation Method
- ✅ Rules include effective dates and versioning
- ✅ Rule configuration examples:
  - California: GAP $200-$1500, Fee $0-$75
  - New York: Refund methods = Pro-rata only (no Rule of 78s)
  - Texas: Fee $0-$75

**User Story:**
> As a compliance administrator, I need to define state-specific validation rules for contract terms so the system automatically checks compliance with state regulations.

### FR3: State-Aware Validation Logic

**Requirement:** ValidationAgent must apply correct state-specific rules during extraction validation.

**Acceptance Criteria:**
- ✅ `StateAwareRuleValidator` replaces hardcoded `RuleValidator`
- ✅ Validator queries database for applicable state rules
- ✅ Validation uses PRIMARY jurisdiction for multi-state contracts
- ✅ Secondary jurisdictions checked for conflicts
- ✅ Validation results include state context
- ✅ Extraction records track which jurisdiction rules were applied

**User Story:**
> As a finance operations staff member, when I view extracted contract data, I need the system to automatically validate it against the correct state's rules so I know if there are compliance issues.

### FR4: Multi-State Contract Handling

**Requirement:** System must handle contracts that apply to multiple states with primary jurisdiction logic.

**Acceptance Criteria:**
- ✅ Contracts can map to multiple jurisdictions
- ✅ One jurisdiction marked as `is_primary=true`
- ✅ Validation uses primary jurisdiction rules
- ✅ Conflicts with secondary jurisdictions logged in `state_validation_results`
- ✅ UI displays: "CA (also applies to: NY, TX)"

**User Story:**
> As a finance operations staff member, when reviewing a multi-state contract, I need to see which state's rules are being applied for validation and whether other states have conflicting requirements.

### FR5: State Information Display (UI)

**Requirement:** UI must clearly display which state(s) apply to a contract and validation context.

**Acceptance Criteria:**
- ✅ Contract metadata section shows primary state
- ✅ State displayed with visual indicator (teal badge)
- ✅ Multi-state contracts show "Also applies to: [states]"
- ✅ Validation messages include state-specific context
- ✅ State indicator uses teal color (#00857f) to differentiate from confidence badges
- ✅ Tooltip shows full state name on hover

**User Story:**
> As a finance operations staff member, I need to clearly see which state's rules apply to the contract I'm reviewing so I understand the regulatory context.

### FR6: State Rules Admin API

**Requirement:** Admin interface (API) must allow authorized users to manage state validation rules.

**Acceptance Criteria:**
- ✅ `GET /state-rules/jurisdictions` - List all jurisdictions
- ✅ `GET /state-rules/jurisdictions/{id}/rules` - Get rules for a state
- ✅ `POST /state-rules/rules` - Create new rule
- ✅ `PUT /state-rules/rules/{id}` - Update rule (creates new version with effective date)
- ✅ Rules authenticated and authorized (admin role required)
- ✅ Rule changes tracked in audit log

**User Story:**
> As a compliance administrator, I need to update state-specific validation rules when regulations change, without requiring a developer or code deployment.

### FR7: Audit Trail of State Rules

**Requirement:** System must maintain complete audit trail of which state rules were applied to each extraction.

**Acceptance Criteria:**
- ✅ `extractions.applied_jurisdiction_id` stores which jurisdiction was used
- ✅ `extractions.jurisdiction_applied_at` timestamp recorded
- ✅ `extractions.state_validation_results` JSONB stores detailed state validation context
- ✅ Audit events include state rule application events
- ✅ Historical queries can determine which rules were in effect at extraction time

**User Story:**
> As a compliance officer, I need to audit historical extractions to verify the correct state rules were applied at the time of processing.

---

## Non-Functional Requirements

### NFR1: Performance

- **Requirement:** State validation must not significantly increase extraction time
- **Target:** < 500ms additional latency for state rule queries and validation
- **Approach:** Database indexing on jurisdiction_id, rule_category, effective_date

### NFR2: Scalability

- **Requirement:** Support all 50 US states with potential for international expansion
- **Target:** System handles 1,000+ extractions per day across all states
- **Approach:** Efficient database queries, optional caching layer for jurisdiction lookups

### NFR3: Maintainability

- **Requirement:** State rules must be updateable without code changes
- **Target:** Non-technical staff can update rules via admin interface
- **Approach:** JSONB configuration, versioned rules, effective date management

### NFR4: Data Integrity

- **Requirement:** Rule changes must not affect historical extractions
- **Target:** Audit trail shows which rules were in effect at extraction time
- **Approach:** Immutable audit log, rule versioning with effective/expiration dates

### NFR5: Usability

- **Requirement:** State information must be clear and unobtrusive in UI
- **Target:** Users immediately understand which state rules apply
- **Approach:** Teal visual design system, prominent metadata section, clear labeling

---

## Technical Architecture

### Database Schema Changes

**New Tables:**
1. `jurisdictions` - Master list of states/jurisdictions
2. `contract_jurisdictions` - Many-to-many mapping (multi-state support)
3. `state_validation_rules` - State-specific rules with JSONB config

**Updated Tables:**
1. `extractions` - Add `applied_jurisdiction_id`, `jurisdiction_applied_at`, `state_validation_results`
2. `audit_events` - Add state-specific event types

### Backend Components

**New:**
- `StateRuleRepository` - Data access for jurisdiction and rule queries
- `StateAwareRuleValidator` - Replaces `RuleValidator` with database-driven rules
- State Rules Admin API (`/state-rules/*`)

**Updated:**
- `ValidationAgent` - Use `StateAwareRuleValidator`
- `ExtractionService` - Track applied jurisdiction
- Contract Search API - Include state information from external database

### Frontend Components

**New:**
- `StateIndicator.tsx` - Teal badge for displaying state(s)
- `ContractMetadata.tsx` - Grid display of contract metadata including state
- `StateValidationNote.tsx` - State-specific validation context display

**Updated:**
- `DataPanel.tsx` - Add contract metadata section
- TypeScript types - Add state fields to Contract and Extraction interfaces

---

## Data Model

### Jurisdiction

```typescript
interface Jurisdiction {
  jurisdiction_id: string;      // "US-CA", "US-TX", "US-NY"
  jurisdiction_name: string;    // "California", "Texas"
  country_code: string;         // "US"
  state_code: string;           // "CA", "TX"
  is_active: boolean;
}
```

### Contract Jurisdiction Mapping

```typescript
interface ContractJurisdiction {
  contract_jurisdiction_id: string;
  contract_id: string;
  jurisdiction_id: string;
  is_primary: boolean;          // Primary jurisdiction for validation
  effective_date: Date;
  expiration_date: Date | null;
}
```

### State Validation Rule

```typescript
interface StateValidationRule {
  rule_id: string;
  jurisdiction_id: string;
  rule_category: 'gap_premium' | 'cancellation_fee' | 'refund_method';
  rule_config: {
    // Numeric validation
    min?: number;
    max?: number;
    strict?: boolean;
    warning_threshold?: number;

    // Value validation
    allowed_values?: string[];
    prohibited_values?: string[];

    // Metadata
    reason?: string;
    disclosure_required?: boolean;
  };
  effective_date: Date;
  expiration_date: Date | null;
  is_active: boolean;
  rule_description: string;
}
```

---

## User Workflows

### Workflow 1: Finance Staff Reviews Contract with State Validation

1. User searches for contract by account number
2. **System queries external database for contract ID AND state information**
3. System creates/updates `contract_jurisdictions` record(s)
4. System triggers AI extraction
5. **ValidationAgent queries state rules for applicable jurisdiction**
6. **Validator applies state-specific rules to each extracted field**
7. System displays extracted data with state indicator
8. **User sees: "State: CA" with teal badge**
9. **Validation badges show state-specific pass/warning/fail**
10. User reviews, corrects if needed, and approves

### Workflow 2: Compliance Admin Updates State Rule

1. Admin logs into system
2. Admin navigates to state rules management (API or future UI)
3. Admin selects jurisdiction (e.g., "California")
4. Admin views current rules for GAP Premium, Refund Method, Cancellation Fee
5. Admin updates rule (e.g., changes CA cancellation fee max from $75 to $50)
6. **System creates new rule version with effective_date = today**
7. **System expires old rule (expiration_date = yesterday)**
8. Future extractions automatically use new rule
9. Historical extractions remain unchanged (show old rule was applied)

### Workflow 3: Multi-State Contract Handling

1. User searches for contract applicable in multiple states
2. **System identifies contract applies to CA (primary), NY, TX**
3. System extracts data and validates against CA rules (primary)
4. **System checks NY and TX rules for conflicts**
5. **Conflict detected: "NY prohibits Rule of 78s refund method"**
6. System logs conflict in `state_validation_results`
7. UI displays: "State: CA (also applies to: NY, TX)"
8. **Validation warning: "Valid in CA, but conflicts with NY regulations"**
9. User reviews and makes informed decision

---

## Example State Rules

### California

**GAP Insurance Premium:**
```json
{
  "min": 200,
  "max": 1500,
  "strict": true,
  "disclosure_required": true,
  "reason": "California Insurance Code §1758.7"
}
```

**Cancellation Fee:**
```json
{
  "min": 0,
  "max": 75,
  "strict": false,
  "warning_threshold": 50,
  "reason": "California regulatory guidance"
}
```

### New York

**Refund Calculation Method:**
```json
{
  "allowed_values": ["pro-rata", "prorata", "pro rata"],
  "prohibited_values": ["rule of 78s", "rule of 78's"],
  "strict": true,
  "reason": "NY Insurance Law §3426 - Rule of 78s prohibited"
}
```

### Texas

**Cancellation Fee:**
```json
{
  "min": 0,
  "max": 75,
  "strict": false,
  "warning_threshold": 50
}
```

### Federal (Default)

**All Fields:**
```json
{
  "gap_premium": {"min": 100, "max": 2000, "strict": false},
  "cancellation_fee": {"min": 0, "max": 100, "strict": false},
  "refund_method": {
    "allowed_values": ["pro-rata", "rule of 78s", "actuarial", "flat", "none"]
  }
}
```

---

## UI Design Specifications

### Contract Metadata Section

```
┌─────────────────────────────────────────────┐
│ Contract Details                            │
│                                             │
│ Account Number       Contract ID            │
│ 123456789012         GAP-2024-001           │
│                                             │
│ State                Contract Type          │
│ 🗺️ California         GAP Insurance          │
│                                             │
│ Also applies to: NY, TX                     │
└─────────────────────────────────────────────┘
```

### State Indicator Badge

- Background: Light teal (#e3fffa)
- Text: Dark teal (#00857f)
- Shape: Rounded pill
- Size: Small, inline with text
- Tooltip: Shows full state name on hover

### State-Specific Validation Display

```
┌─────────────────────────────────────────────┐
│ Cancellation Fee                            │
│                           ✓ pass  🗺️ CA     │
│ $75.00                                      │
│                                             │
│ ℹ️ Meets California requirements ($0-$75)  │
│                                             │
│ Source: Page 3, Section 2.1                 │
└─────────────────────────────────────────────┘
```

---

## Security & Compliance

### Access Control

- **State Rules Management:** Admin role required
- **State Rule Viewing:** All authenticated users
- **Rule History:** Audit log captures all rule changes

### Data Privacy

- No PII involved in state rules
- Audit trail includes user ID of rule creator/updater
- Historical rule queries support compliance audits

### Regulatory Compliance

- Complete audit trail of which state rules were applied
- Rule versioning prevents retroactive changes
- Historical queries support regulatory investigations

---

## Success Metrics & KPIs

### Operational Metrics

- **Validation Accuracy:** % of extractions that correctly apply state rules
- **User Confidence:** User survey on confidence in state compliance
- **Processing Time:** Time to review contract with state validation (target: < 2 minutes)

### Compliance Metrics

- **State Rule Coverage:** % of extractions with applicable state rules defined
- **Rule Update Frequency:** Number of state rule updates per quarter
- **Conflict Detection:** Number of multi-state conflicts identified

### Technical Metrics

- **Performance:** State validation latency (target: < 500ms)
- **Uptime:** State rules API availability (target: 99.9%)
- **Audit Trail:** 100% of state rule applications logged

---

## Implementation Phases

### Phase 1: Database & Backend (Priority) - 2 weeks

- Database schema changes (jurisdictions, rules, mappings)
- SQLAlchemy models
- StateRuleRepository
- StateAwareRuleValidator
- Update ValidationAgent & ExtractionService
- Seed initial state rules (all 50 states + federal default)

### Phase 2: API & Integration - 1 week

- State Rules Admin API endpoints
- Update contract search to include state
- Response schema updates
- Testing (unit + integration)

### Phase 3: Frontend Display - 1 week

- TypeScript type updates
- StateIndicator, ContractMetadata components
- Update DataPanel with metadata section
- Tailwind config updates
- Frontend testing

### Phase 4: Testing & Documentation - 1 week

- End-to-end testing
- Performance testing
- Security review
- User documentation
- Admin guide for state rules management

**Total Estimated Timeline:** 5 weeks

---

## Risks & Mitigation

### Risk 1: External database doesn't provide state information

**Likelihood:** Medium
**Impact:** High
**Mitigation:** Verify data availability before starting; implement manual entry fallback; coordinate with external database team

### Risk 2: Multi-state complexity harder than expected

**Likelihood:** Medium
**Impact:** Medium
**Mitigation:** Start with primary jurisdiction only in Phase 1; add conflict detection incrementally in Phase 2

### Risk 3: State regulations change frequently

**Likelihood:** Low
**Impact:** Medium
**Mitigation:** Rule versioning with effective dates; Admin API enables quick updates; Document process for regulatory monitoring

### Risk 4: Performance impact of additional queries

**Likelihood:** Low
**Impact:** Medium
**Mitigation:** Database indexing; consider caching layer; monitor query performance; optimize if needed

---

## Dependencies

### External Dependencies

- **External Database:** Must provide state information in contract lookup query
- **Auth System:** Must support admin role for state rules management

### Internal Dependencies

- **Existing System:** Must be operational (contract search, AI extraction, validation)
- **Database:** PostgreSQL 15.x with JSONB support
- **Python:** SQLAlchemy ORM for new models
- **Frontend:** Next.js/React with TypeScript

---

## Open Questions

1. **Q:** How often do state regulations change?
   **A:** Quarterly on average; some states more frequent than others

2. **Q:** Who monitors state regulation changes?
   **A:** Compliance team; they will update rules via admin API

3. **Q:** Do all contracts have state information available?
   **A:** Yes, confirmed with external database team

4. **Q:** What happens if a contract applies to ALL 50 states?
   **A:** Use federal default; or primary state with note "Applies nationally"

5. **Q:** Can state rules differ by contract type (GAP vs VSC)?
   **A:** Future enhancement; Phase 1 rules apply uniformly

---

## Approval & Sign-Off

**Product Owner:** _______________ Date: ___________

**Technical Lead:** _______________ Date: ___________

**Compliance Lead:** _______________ Date: ___________

---

## Appendix A: State Abbreviation Reference

All 50 US states will be seeded in the `jurisdictions` table with format:
- `jurisdiction_id`: "US-XX" (e.g., "US-CA", "US-NY")
- `state_code`: Two-letter state code (e.g., "CA", "NY")
- `jurisdiction_name`: Full state name (e.g., "California", "New York")

Federal default: `jurisdiction_id = "US-FEDERAL"`, `state_code = NULL`

---

## Appendix B: Rule Configuration Schema

**Numeric Range Validation:**
```json
{
  "min": <number>,
  "max": <number>,
  "strict": <boolean>,  // If true, violations are FAIL; if false, WARNING
  "warning_threshold": <number>,  // Optional threshold for warnings
  "disclosure_required": <boolean>,  // Optional metadata
  "reason": <string>  // Optional explanation of rule
}
```

**Value List Validation:**
```json
{
  "allowed_values": [<string>, ...],  // List of acceptable values
  "prohibited_values": [<string>, ...],  // List of prohibited values
  "strict": <boolean>,  // If true, violations are FAIL; if false, WARNING
  "reason": <string>  // Optional explanation of rule
}
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-19 | System | Initial PRD for state-specific validation feature |

---

**End of PRD**
