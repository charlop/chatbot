# User Guide: State-Specific Validation

## Overview

The contract extraction system now validates extracted data against state-specific rules. This ensures compliance with state regulations and highlights potential issues before you approve an extraction.

## Understanding State Information

### State Indicator

When you view a contract, you'll see a **teal badge** showing the primary state:

```
🗺️ CA
```

This badge appears in the contract details section at the top of the data panel.

For multi-state contracts, you'll also see additional states:

```
🗺️ CA  Also: NY, TX
```

### How States Are Determined

The state information comes from your external contract database. When you search by account number, the system automatically retrieves and applies the correct state rules.

The primary state is the main jurisdiction where the contract applies. Additional states are secondary jurisdictions that may have different requirements.

---

## Validation with State Rules

### State-Specific Validation Messages

Each extracted field is validated against the rules for your contract's state. After extraction completes, you'll see validation badges next to each field:

- **✓ Pass (Green):** The value complies with state rules
- **⚠ Warning (Yellow):** The value is acceptable but may need review
- **✗ Fail (Red):** The value violates state regulations

Example validation messages:

- **Pass:** "Premium $500 complies with California limits ($200-$1500)"
- **Warning:** "Fee $45 exceeds Texas recommended threshold ($40)"
- **Fail:** "New York prohibits Rule of 78s refund method"

### Validation Context

Click on a validation badge to see more details about the state-specific rule that was applied. This includes:

- The jurisdiction that was checked (e.g., "US-CA")
- The specific rule or regulation
- Why the value passed, warned, or failed

---

## Multi-State Contracts

### Understanding Multi-State Validation

If your contract applies to multiple states, the system:
1. **Validates against the primary state** rules (shown in the main badge)
2. **Checks other states for conflicts** (shown in expandable section)
3. **Displays any conflicts** below the affected fields

### Viewing Multi-State Conflicts

When conflicts are detected, you'll see an expandable section labeled:

```
ℹ️ Multi-State Conflicts (2)
```

Click to expand and see details:

```
US-NY: Rule of 78s prohibited by NY Insurance Law §3426
US-TX: Cancellation fee must be under $50 per TX regulations
```

### What to Do About Conflicts

**If your extraction has multi-state conflicts:**

1. **Review the conflict details** to understand which states have different requirements
2. **Verify the extracted values** are correct for your contract
3. **Consult with compliance** if you're unsure how to handle the conflict
4. **Document your decision** in the submission notes

**Important:** The system validates against the **primary state** rules. Conflicts are informational only and don't prevent submission.

---

## Common Scenarios

### Scenario 1: Single-State Contract

**What you see:**
- State badge shows "CA"
- All validations reference California rules
- No conflict warnings

**What this means:**
- Your contract only applies to California
- All extracted values must comply with CA regulations

---

### Scenario 2: Multi-State Contract (No Conflicts)

**What you see:**
- State badge shows "CA (Also: NY, TX)"
- Validations reference California rules
- No conflict warnings

**What this means:**
- Your contract applies to multiple states
- The extracted values comply with all applicable state rules

---

### Scenario 3: Multi-State Contract (With Conflicts)

**What you see:**
- State badge shows "CA (Also: NY)"
- Validation shows "Warning" or "Fail" for a field
- Conflict section shows "US-NY: [conflict description]"

**What this means:**
- Your contract applies to both CA and NY
- The value is valid in CA (primary) but conflicts with NY rules
- You need to review and potentially adjust the value

---

## FAQs

**Q: Can I override state-specific validation?**

A: Yes. Warnings are informational and don't prevent submission. For failures, you can still edit the value and submit. However, failing values should be carefully reviewed before approval.

---

**Q: What if my contract doesn't have a state?**

A: The system will use federal default rules as a fallback. Most contracts should have state information from the external database.

---

**Q: Can I see which specific rule was applied?**

A: Yes. Click on the validation badge to see details including:
- The jurisdiction (e.g., "California")
- The rule category (e.g., "GAP Premium Limits")
- The specific regulation or law citation

---

**Q: Who can change state rules?**

A: Only system administrators can create or update state validation rules. If you believe a rule is incorrect, contact your system administrator.

---

**Q: What if I disagree with a validation result?**

A: You can edit the value and add a note explaining your reasoning when you submit. Your submission notes are logged for audit purposes.

---

**Q: Do state rules change over time?**

A: Yes. State regulations can change. The system uses the rules that were effective at the time of extraction. Historical extractions show which rule version was applied.

---

**Q: How do I know if a rule has changed?**

A: Administrators receive notifications when new rules are added or updated. If you're re-extracting an old contract, you may see different validation results if rules have changed.

---

## Getting Help

If you encounter issues with state-specific validation:

1. **Check the validation message details** for specific guidance
2. **Review the Admin Guide** (for administrators)
3. **Contact your system administrator** for rule-related questions
4. **Submit a support ticket** for technical issues

---

## Best Practices

1. **Always review state indicators** when starting an extraction
2. **Pay attention to validation warnings** - they may indicate regulatory concerns
3. **Document your decisions** in submission notes, especially for conflicts
4. **Don't ignore failures** - they indicate potential compliance issues
5. **Consult compliance team** for multi-state conflicts you're unsure about

---

**Need More Help?**

- **Admin Guide:** See `/docs/admin-guide/managing-state-rules.md`
- **API Documentation:** See `/docs/api/state-rules-api.md`
- **Support:** Contact your system administrator
