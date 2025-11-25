# Agentic AI Plan: Validation Agent for Contract Refund Eligibility System

## Overview

Add an autonomous **Validation Agent** that actively verifies extracted contract data using multi-step reasoning and tool use. The agent doesn't just flag low confidence - it researches, validates, and provides intelligent suggestions.

## Why This is "Agentic AI"

Unlike simple extraction, the agent:
- **Plans**: Decides what checks to run based on contract type and extracted data
- **Uses Tools**: Queries historical data, searches similar contracts, applies business rules
- **Reasons**: Explains why something might be wrong and suggests corrections
- **Acts Autonomously**: Runs automatically after extraction without human intervention
- **Makes Decisions**: Determines if data passes validation or needs human review

## Core Agentic Features

### 1. Autonomous Data Validation Agent

**Triggers automatically after extraction**

**Agent's Tools:**
1. **Historical Comparator** - Compare against database of approved contracts
2. **Rule Engine** - Apply business logic (e.g., "cancellation fee can't exceed premium")
3. **Semantic Searcher** - Find similar language in other contracts
4. **Consistency Checker** - Cross-validate extracted fields against each other
5. **Contract Text Analyzer** - Re-read source to verify extraction accuracy

**Agent's Workflow:**
```
1. Receive extraction results (3 fields + confidence scores)
2. PLAN validation strategy based on contract type
3. EXECUTE validations using tools:
   - Check if premium in normal range for this contract type
   - Verify refund method matches contract type (GAP = pro-rata typical)
   - Validate cancellation fee is reasonable (< 20% of premium typical)
   - Search for contradictions in contract text
   - Compare against similar previously approved contracts
4. REASON about findings
5. OUTPUT validation report with:
   - Pass/Warn/Fail status per field
   - Confidence adjustment if needed
   - Explanation of concerns
   - Suggested corrections if applicable
```

**Example Output:**
```
Premium: $2,450 ✅ PASS
  → Within expected range for GAP contracts ($1,500-$3,500)
  → Matches similar contracts from same provider

Refund Method: "Pro-Rata" ✅ PASS
  → Standard for GAP insurance contracts
  → Consistent with 47 similar contracts in database

Cancellation Fee: $850 ⚠️ WARNING
  → Higher than typical (34% of premium vs 10-15% typical)
  → Agent found similar clause in Contract #GAP-2023-0456
  → Suggestion: Verify this isn't a "graduated fee schedule"
  → Human review recommended
```

### 2. Ambiguity Resolution Agent

**Triggers when confidence < 80%**

**Agent's Tools:**
1. **Similar Clause Finder** - Vector search for similar contract language
2. **Term Glossary** - Industry definitions database
3. **Pattern Matcher** - Recognize common phrasing variations
4. **Context Analyzer** - Consider surrounding text

**Agent's Workflow:**
```
1. Detect low confidence extraction (e.g., refund method = 65% confidence)
2. RESEARCH:
   - Find 5 most similar clauses from historical contracts
   - Check if any match a known pattern
   - Analyze context around the ambiguous text
3. REASON:
   - "70% of similar clauses used 'Short-Rate' method"
   - "Contract type (GAP) typically uses Pro-Rata (85% of cases)"
   - "Surrounding text mentions 'unearned premium' (Pro-Rata indicator)"
4. PROPOSE interpretation with confidence level
5. EXPLAIN reasoning to human reviewer
```

**Example Output:**
```
Refund Method: [AMBIGUOUS - 65% confidence]

Agent Analysis:
  Original extraction: "proportional basis"

  🔍 Similar clauses found (3/5 were "Pro-Rata"):
    - "proportionate refund" → Pro-Rata (Contract #GAP-2023-0123)
    - "proportional premium return" → Pro-Rata (Contract #GAP-2022-0789)

  📊 Contract type pattern:
    - GAP contracts use Pro-Rata in 87% of cases

  📝 Context analysis:
    - Surrounding text mentions "unearned premium"
    - No mention of penalty or short-rate discount

  💡 Agent's Interpretation: "Pro-Rata" (82% confidence)

  Reasoning: "Proportional basis" is synonymous with Pro-Rata refund
  method, especially in GAP insurance context with unearned premium language.

  ✋ Flagged for human verification due to original ambiguity
```

### 3. Enhanced Chat Agent (Make It More Agentic)

Upgrade existing chat from simple Q&A to **proactive analysis**

**New Capabilities:**
- **Multi-step research**: "I'll check the contract text, then compare with similar contracts, then summarize..."
- **Proactive insights**: After user views contract, agent says "I noticed 3 unusual clauses worth reviewing..."
- **Tool use**: Agent can search historical data, compare contracts, check definitions
- **Explain reasoning**: Shows thought process, not just answers

**Example Interaction:**
```
User: "Is this cancellation fee normal?"

Agent: Let me investigate that for you.

  Step 1: Analyzing extracted fee ($850 on $2,450 premium = 34.7%)
  Step 2: Checking historical data for GAP contracts...
  Step 3: Found 142 similar contracts from same provider

  Analysis:
  - Typical cancellation fee: $200-$400 (10-15% of premium)
  - Your contract: $850 (34.7% of premium) - HIGHER THAN TYPICAL
  - Provider average: $325 (13%)

  Possible explanations:
  1. Fee may be graduated (lower if cancelled in first year)
  2. Contract may include admin fees not typically counted
  3. Could be an error in the contract or extraction

  Recommendation: Review page 3, section 2.4 where fee is defined.
  Check if there's a fee schedule based on cancellation timing.
```

## Implementation Plan

### Phase 1: Core Validation Agent (Week 1)

**1.1 Create Validation Service**
- New file: `/app/services/validation_agent_service.py`
- Orchestrates validation workflow
- Calls individual validator tools

**1.2 Implement Validator Tools**
- **Historical Comparator**: Query database for similar contracts
- **Rule Engine**: Business logic checks (premium ranges, fee limits)
- **Consistency Checker**: Cross-field validation

**1.3 Integrate with Extraction Flow**
- After LLM extraction completes
- Before returning to user
- Add validation results to response

**1.4 Update UI**
- Add validation status badges (✅ Pass, ⚠️ Warning, ❌ Fail)
- Show agent's reasoning in expandable panel
- Display suggestions from agent

### Phase 2: Ambiguity Resolution (Week 2)

**2.1 Build Similar Clause Finder**
- Vector search over historical contract text
- Find top 5 most similar clauses
- Return their interpretations + confidence

**2.2 Create Pattern Library**
- Common refund method phrasings
- Cancellation fee variations
- Premium terminology

**2.3 Implement Resolution Logic**
- Triggered by low confidence (<80%)
- Multi-step research workflow
- Generate interpretation + reasoning

**2.4 Update UI**
- "Agent's Interpretation" section for ambiguous fields
- Show research process (similar clauses found, patterns matched)
- Clear indication this needs human verification

### Phase 3: Enhanced Agentic Chat (Week 3)

**3.1 Add Tool Calling to Chat**
- Give chat agent access to:
  - Historical data queries
  - Contract text search
  - Validation checks
  - Pattern matching

**3.2 Implement Multi-Step Reasoning**
- Agent plans research steps
- Shows thinking process
- Executes tools in sequence

**3.3 Proactive Insights**
- After extraction, agent analyzes for unusual patterns
- Suggests things user should review
- Explains why they matter

## Technical Architecture

### Validation Agent Flow

```
┌─────────────────┐
│  LLM Extraction │
│   (existing)    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   Validation Agent Orchestrator     │
│  (NEW: validation_agent_service.py) │
└──┬──────────────────────────────┬───┘
   │                              │
   ▼                              ▼
┌──────────────┐           ┌──────────────┐
│ Tool: Compare│           │ Tool: Check  │
│  Historical  │           │    Rules     │
│    Data      │           │              │
└──────────────┘           └──────────────┘
   │                              │
   └────────────┬─────────────────┘
                ▼
   ┌─────────────────────────┐
   │   Validation Report     │
   │  • Field status         │
   │  • Confidence adj.      │
   │  • Reasoning            │
   │  • Suggestions          │
   └───────────┬─────────────┘
               │
               ▼
   ┌─────────────────────────┐
   │  Return to User with    │
   │  Enhanced Extraction    │
   └─────────────────────────┘
```

## Critical Files to Create/Modify

### New Files (Backend)
- `/app/services/validation_agent_service.py` - Main validation orchestrator
- `/app/services/ambiguity_resolver_service.py` - Handles low-confidence cases
- `/app/validators/` - Individual validator tools
  - `historical_validator.py` - Compare against database
  - `rule_validator.py` - Business logic checks
  - `consistency_validator.py` - Cross-field validation
  - `semantic_validator.py` - Similar clause search
- `/app/models/validation.py` - Validation result models

### Modified Files (Backend)
- `/app/services/extraction_service.py` - Add validation step after extraction
- `/app/services/chat_service.py` - Enhance with tool calling
- `/app/schemas/responses.py` - Add validation results to extraction response

### New/Modified Files (Frontend)
- `/components/extraction/ValidationPanel.tsx` - NEW: Display validation results
- `/components/extraction/AgentInsights.tsx` - NEW: Show agent's reasoning
- `/components/extraction/DataCard.tsx` - MODIFY: Add validation status badges
- `/components/chat/ChatInterface.tsx` - MODIFY: Show agent's tool use/thinking

## Database Schema Changes

### New Table: validation_results

```sql
CREATE TABLE validation_results (
    validation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    extraction_id UUID NOT NULL REFERENCES extractions(extraction_id),

    -- Validation metadata
    validated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    agent_version VARCHAR(50),

    -- Overall status
    overall_status VARCHAR(20) CHECK (overall_status IN ('pass', 'warning', 'fail')),

    -- Field-level validations (JSONB for flexibility)
    field_validations JSONB,

    -- Agent insights
    insights JSONB,
    suggestions JSONB,

    -- Performance tracking
    validation_duration_ms INTEGER,
    tools_used JSONB
);

CREATE INDEX idx_validation_extraction ON validation_results(extraction_id);
CREATE INDEX idx_validation_status ON validation_results(overall_status);
```

## Success Criteria

**Functional:**
- [ ] Validation agent runs automatically after every extraction
- [ ] Agent provides pass/warning/fail status for each field
- [ ] Agent explains reasoning for all warnings/failures
- [ ] Ambiguity resolver triggers for confidence < 80%
- [ ] Agent suggests interpretations with supporting evidence

**Quality:**
- [ ] Validation catches >80% of known data quality issues
- [ ] Ambiguity resolution improves confidence from <80% to >85% in 70% of cases
- [ ] False positive rate < 15%

**Performance:**
- [ ] Validation adds < 3 seconds to extraction time
- [ ] Ambiguity resolution completes in < 5 seconds

## Why This is Better Than Boss's Idea

**Boss's Idea**: Agent looks up contract ID from account number
- ❌ This is just a database query - not agentic at all
- ❌ Adds complexity with no value

**Our Validation Agent Approach:**
- ✅ Actually autonomous (plans, uses tools, reasons)
- ✅ Adds real value (catches errors, resolves ambiguity)
- ✅ Improves data quality
- ✅ Demonstrably "AI" (not just glorified search)
- ✅ Within existing scope (no regulatory risk)

## Implementation Timeline

- **Week 1**: Core validation agent + historical comparison
- **Week 2**: Ambiguity resolution + similar clause finder
- **Week 3**: Enhanced agentic chat + UI integration
- **Week 4**: Testing, refinement, monitoring

**Total**: ~3-4 weeks for full agentic AI capabilities

---

**Document Version**: 1.0
**Last Updated**: 2025-11-24
**Status**: Ready for Review
