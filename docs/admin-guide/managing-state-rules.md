# Admin Guide: Managing State Validation Rules

## Overview

This guide explains how to manage state-specific validation rules via the API.

**Prerequisites:**
- Admin role in the system
- API access token with admin privileges
- Basic understanding of REST APIs

---

## Authentication

All endpoints require admin authentication. Set your token in an environment variable:

```bash
export ADMIN_TOKEN="your-admin-token-here"
```

Then use in requests:

```bash
-H "Authorization: ${ADMIN_TOKEN}"
```

---

## API Endpoints

Base URL: `https://api.example.com/api/v1/state-rules`

---

## List All Jurisdictions

```bash
curl -X GET "${API_BASE}/jurisdictions" \
  -H "Authorization: ${ADMIN_TOKEN}"
```

Response includes all 50 US states plus federal jurisdiction.

---

## Get Rules for Jurisdiction

```bash
curl -X GET "${API_BASE}/jurisdictions/US-CA/rules" \
  -H "Authorization: ${ADMIN_TOKEN}"
```

Optional parameters:
- `active_only=false` - include expired rules
- `as_of_date=2024-01-01` - rules effective on date

---

## Create New Rule

```bash
curl -X POST "${API_BASE}/rules" \
  -H "Authorization: ${ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "jurisdiction_id": "US-CA",
    "rule_category": "gap_premium",
    "rule_config": {"min": 200, "max": 1500, "strict": true},
    "effective_date": "2025-07-01",
    "rule_description": "California GAP premium limits"
  }'
```

---

## Update Existing Rule

Updating creates a new version. The old version is automatically expired.

```bash
curl -X PUT "${API_BASE}/rules/${RULE_ID}" \
  -H "Authorization: ${ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_config": {"min": 250, "max": 1400, "strict": true},
    "effective_date": "2025-09-01",
    "rule_description": "Updated limits"
  }'
```

---

## Rule Configuration Examples

### GAP Premium (Numeric Range)

```json
{
  "min": 200,
  "max": 1500,
  "strict": true,
  "warning_threshold": 1200,
  "reason": "California Insurance Code §1758.7"
}
```

### Refund Method (Value List)

```json
{
  "allowed_values": ["pro-rata", "prorata", "pro rata"],
  "prohibited_values": ["rule of 78s"],
  "strict": true,
  "reason": "NY Insurance Law §3426"
}
```

---

## Rule Categories

Valid categories:
- `gap_premium` - GAP Insurance Premium validation
- `cancellation_fee` - Cancellation fee validation
- `refund_method` - Refund calculation method validation

---

## Rule Versioning

Rules are versioned by effective date. Updating a rule:
1. Creates new version with new rule_id
2. Expires old version automatically
3. Preserves audit trail

View historical rules:
```bash
curl -X GET "${API_BASE}/jurisdictions/US-CA/rules?active_only=false" \
  -H "Authorization: ${ADMIN_TOKEN}"
```

---

## Best Practices

1. **Test in staging first** before production
2. **Set future effective dates** for review time
3. **Document the reason** with regulatory citations
4. **Monitor validation results** after changes
5. **Review multi-state conflicts** periodically

---

## Troubleshooting

**422 Validation Error**
- Check rule category is valid
- Ensure all required fields present

**404 Not Found**
- Verify jurisdiction ID format (US-XX)
- Confirm rule ID exists

**403 Forbidden**
- Ensure using admin token
- Check token hasn't expired

---

## Security

- All operations require admin role
- Changes logged with user ID
- Rules cannot be deleted (audit trail)
- Updates create new versions (versioning)

---

**Related Documentation:**
- User Guide: `/docs/user-guide/state-specific-validation.md`
- Security Review: `/docs/deployment/security-review-checklist.md`
