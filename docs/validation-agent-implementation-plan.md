# Sprint 2: Validation Agent - Implementation Plan

**Created**: 2025-11-30
**Status**: Ready for Implementation

---

## Overview

Implement a Validation Agent that automatically validates extracted contract data after LLM extraction. The agent uses a Tool architecture that supports future phases (Ambiguity Resolution, Enhanced Chat).

### Success Criteria (from backlog)
- [ ] Validation agent runs after every extraction
- [ ] Pass/warning/fail status displayed per field
- [ ] Agent reasoning visible in UI
- [ ] Validation adds <3 seconds to extraction time

---

## Architecture

```
┌─────────────────┐
│  LLM Extraction │
│   (existing)    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│      ValidationAgent                │
│  (orchestrates tool execution)      │
└──┬──────────────────────────────┬───┘
   │                              │
   ▼                              ▼
┌──────────────┐           ┌──────────────┐
│ Tool: Rule   │           │ Tool: History│
│  Validators  │           │  Validator   │
└──────────────┘           └──────────────┘
   │                              │
   └────────────┬─────────────────┘
                ▼
   ┌─────────────────────────┐
   │   Validation Results    │
   │  stored on extraction   │
   └─────────────────────────┘
```

---

## Implementation Steps

### Step 1: Database Schema (backend)

**Modify**: `project/backend/database/schema.sql`

Add columns to `extractions` table:
```sql
-- Validation results
validation_status VARCHAR(20) CHECK (validation_status IN ('pass', 'warning', 'fail')),
validation_results JSONB,
validated_at TIMESTAMP WITH TIME ZONE
```

**Modify**: `project/backend/app/models/database/extraction.py`

Add to Extraction model:
```python
validation_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
validation_results: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
validated_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
```

---

### Step 2: Core Agent Infrastructure (backend)

**Create**: `project/backend/app/agents/__init__.py`

**Create**: `project/backend/app/agents/base.py`
- `ToolContext` - input context for tools (field_name, value, confidence, source, document_text)
- `ToolResult` - output from tools (status: pass/warning/fail, reason, details)
- `Tool` - abstract base class with `name`, `description`, `execute(context) -> ToolResult`
- `AgentContext` - input for agents (extraction_data, contract_id, document_text)
- `AgentResult` - output from agents (overall_status, field_results list)
- `Agent` - abstract base class with `execute(context) -> AgentResult`

**Create**: `project/backend/app/agents/tools/__init__.py`

**Create**: `project/backend/app/agents/tools/base.py`
- `ValidationTool(Tool)` - base class for validators with skip logic for N/A fields

---

### Step 3: Validation Tools (backend)

**Create**: `project/backend/app/agents/tools/validators/__init__.py`

**Create**: `project/backend/app/agents/tools/validators/rule_validator.py`
- `RuleValidator` - business logic checks:
  - GAP premium in range ($100-$2000)
  - Cancellation fee in range ($0-$100)
  - Refund method is known value (Pro-Rata, Rule of 78s, Flat, None)
  - Cancellation fee < premium (cross-field)

**Create**: `project/backend/app/agents/tools/validators/historical_validator.py`
- `HistoricalValidator` - compare against approved extractions:
  - Query avg/stddev from approved extractions
  - Flag values >2 stddev from mean
  - Requires db session injection

**Create**: `project/backend/app/agents/tools/validators/consistency_validator.py`
- `ConsistencyValidator` - cross-field validation:
  - Fee cannot exceed premium
  - Confidence scores are reasonable (not all 100% or all low)

---

### Step 4: Validation Agent (backend)

**Create**: `project/backend/app/agents/validation_agent.py`

```python
class ValidationAgent(Agent):
    """Orchestrates validation tools on extracted data."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.tools = [
            RuleValidator(),
            HistoricalValidator(db),
            ConsistencyValidator(),
        ]

    async def execute(self, context: AgentContext) -> AgentResult:
        field_results = []
        fields = ["gap_insurance_premium", "refund_calculation_method", "cancellation_fee"]

        for field in fields:
            field_data = context.extraction_data.get(field, {})
            tool_context = ToolContext(
                field_name=field,
                field_value=field_data.get("value"),
                field_confidence=field_data.get("confidence"),
                field_source=field_data.get("source"),
                all_fields=context.extraction_data,
            )

            for tool in self.tools:
                result = await tool.execute(tool_context)
                if result.status != "skipped":
                    field_results.append(result.to_dict())

        # Aggregate: fail > warning > pass
        overall = self._compute_overall_status(field_results)

        return AgentResult(
            overall_status=overall,
            field_results=field_results,
        )
```

---

### Step 5: Integration with ExtractionService (backend)

**Modify**: `project/backend/app/services/extraction_service.py`

In `create_extraction()`, after LLM extraction completes (~line 198):

```python
from app.agents.validation_agent import ValidationAgent

# After: extraction_result = await self.llm_service.extract_contract_data(...)

# Run validation
validation_agent = ValidationAgent(self.db)
agent_context = AgentContext(
    contract_id=contract_id,
    extraction_id=str(extraction.extraction_id),
    extraction_data={
        "gap_insurance_premium": {"value": extraction_result.gap_insurance_premium.value, ...},
        "refund_calculation_method": {...},
        "cancellation_fee": {...},
    },
)
validation_result = await validation_agent.execute(agent_context)

# Store on extraction
extraction.validation_status = validation_result.overall_status
extraction.validation_results = {"field_results": validation_result.field_results}
extraction.validated_at = datetime.utcnow()
```

---

### Step 6: Update API Response (backend)

**Modify**: `project/backend/app/schemas/responses.py`

Add to file:
```python
class FieldValidationResponse(BaseModel):
    field: str
    status: Literal["pass", "warning", "fail"]
    reason: str
    tool_name: str | None = None
```

Add to `ExtractionResponse`:
```python
validation_status: str | None = None
validation_results: list[FieldValidationResponse] | None = None
validated_at: datetime | None = None
```

Update `from_orm_model()` to include validation fields.

---

### Step 7: Frontend Types (frontend)

**Modify**: `project/frontend/lib/api/extractions.ts`

Add types:
```typescript
export interface FieldValidation {
  field: string;
  status: 'pass' | 'warning' | 'fail';
  reason: string;
  tool_name?: string;
}

// Add to Extraction interface:
validation_status?: 'pass' | 'warning' | 'fail';
validation_results?: FieldValidation[];
validated_at?: string;
```

---

### Step 8: ValidationBadge Component (frontend)

**Create**: `project/frontend/components/extraction/ValidationBadge.tsx`

```tsx
interface ValidationBadgeProps {
  status?: 'pass' | 'warning' | 'fail';
  reason?: string;
}

export const ValidationBadge: React.FC<ValidationBadgeProps> = ({ status, reason }) => {
  if (!status) return null;

  const styles = {
    pass: 'bg-success-light text-success-dark',
    warning: 'bg-warning-light text-warning-dark',
    fail: 'bg-danger-light text-danger-dark',
  };

  const icons = { pass: '✓', warning: '⚠', fail: '✗' };

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium ${styles[status]}`} title={reason}>
      {icons[status]} {status}
    </span>
  );
};
```

**Create**: `project/frontend/__tests__/components/extraction/ValidationBadge.test.tsx`

---

### Step 9: Update DataCard (frontend)

**Modify**: `project/frontend/components/extraction/DataCard.tsx`

Add props:
```tsx
validationStatus?: 'pass' | 'warning' | 'fail';
validationReason?: string;
```

In render, next to ConfidenceBadge:
```tsx
<div className="flex items-center gap-2">
  <ConfidenceBadge confidence={confidence} />
  <ValidationBadge status={validationStatus} reason={validationReason} />
</div>
```

---

### Step 10: Update DataPanel (frontend)

**Modify**: `project/frontend/components/extraction/DataPanel.tsx`

Add helper to map validation results to fields:
```tsx
const getFieldValidation = (fieldName: string) => {
  const result = extraction.validation_results?.find(r => r.field === fieldName);
  return { validationStatus: result?.status, validationReason: result?.reason };
};
```

Pass to each DataCard:
```tsx
<DataCard
  label="GAP Insurance Premium"
  {...getFieldValidation('gap_insurance_premium')}
  // ... other props
/>
```

---

### Step 11: Tests (TDD)

**Create**: `project/backend/tests/unit/test_agents/`

**Create**: `project/backend/tests/unit/test_agents/test_validation_agent.py`
- Test ValidationAgent orchestration
- Test overall status computation (fail > warning > pass)

**Create**: `project/backend/tests/unit/test_agents/test_rule_validator.py`
- Test each business rule (premium range, fee range, method validation)
- Test cross-field validation

**Create**: `project/backend/tests/unit/test_agents/test_historical_validator.py`
- Test with mock DB session
- Test insufficient data handling

**Create**: `project/frontend/__tests__/components/extraction/ValidationBadge.test.tsx`
- Test rendering for each status
- Test tooltip with reason

---

## File Summary

### New Files (Backend - 10)
```
project/backend/app/agents/
├── __init__.py
├── base.py
├── validation_agent.py
└── tools/
    ├── __init__.py
    ├── base.py
    └── validators/
        ├── __init__.py
        ├── rule_validator.py
        ├── historical_validator.py
        └── consistency_validator.py

project/backend/tests/unit/test_agents/
├── __init__.py
├── test_validation_agent.py
├── test_rule_validator.py
└── test_historical_validator.py
```

### New Files (Frontend - 2)
```
project/frontend/components/extraction/ValidationBadge.tsx
project/frontend/__tests__/components/extraction/ValidationBadge.test.tsx
```

### Modified Files (7)
```
project/backend/database/schema.sql
project/backend/app/models/database/extraction.py
project/backend/app/services/extraction_service.py
project/backend/app/schemas/responses.py
project/frontend/lib/api/extractions.ts
project/frontend/components/extraction/DataCard.tsx
project/frontend/components/extraction/DataPanel.tsx
```

---

## Validation Rules (Phase 1)

| Validator | Field | Rule | Status |
|-----------|-------|------|--------|
| Rule | gap_insurance_premium | $100-$2000 range | warning if outside |
| Rule | cancellation_fee | $0-$100 range | warning if outside |
| Rule | cancellation_fee | < 0 | fail |
| Rule | refund_calculation_method | Known value | warning if unknown |
| Consistency | cross-field | fee < premium | warning if violated |
| Historical | gap_insurance_premium | within 2 stddev | warning if outlier |

---

## Performance Budget

- Rule validators: ~0ms (pure logic)
- Consistency validator: ~0ms (pure logic)
- Historical validator: ~50ms (single indexed query)
- **Total: <100ms** (well under 3s budget)

---

## Future Extension Points

**Phase 2 (Ambiguity Resolution)**: Add `AmbiguityResolutionAgent` that:
- Triggers when confidence < 80%
- Uses same tool infrastructure
- Adds `SimilarClauseFinder` tool

**Phase 3 (Enhanced Chat)**: Add `ChatAgent` that:
- Has access to same tools
- Can invoke ValidationAgent for "is this normal?" questions
- Uses multi-step reasoning
