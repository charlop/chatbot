# Dead Code Analysis Report: Old Customer-Contract Model

**Date**: 2025-11-25
**Status**: Analysis Complete

## Executive Summary

The system was migrated from a customer-contract model to a template-based model. The old model stored customer-specific data (`account_number`, `customer_name`, `vehicle_info`) directly on the contracts table. The new model:
- Stores `account_number` in `account_template_mappings` table (many-to-one relationship)
- Removes `customer_name` (templates don't have customer data)
- Removes `vehicle_info` (templates don't have vehicle data)

This analysis identifies all obsolete code that references the old model structure.

---

## 1. BACKEND DEAD CODE

### 1.1 Test Files - Old Contract Fields

#### File: `tests/integration/test_contracts_api.py`

**Lines 38-39:**
```python
assert "customer_name" in data
assert "vehicle_info" in data
```
- **Location:** Inside `test_search_contract_found` method
- **What it does:** Asserts that API response contains customer_name and vehicle_info
- **Why obsolete:** These fields no longer exist in Contract model or ContractResponse schema
- **Safe to delete:** ✅ YES - These assertions will fail since fields don't exist

**Lines 107-108:**
```python
assert "customer_name" in data
assert "vehicle_info" in data
```
- **Location:** Inside `test_get_contract_found` method
- **What it does:** Asserts that API response contains customer_name and vehicle_info
- **Why obsolete:** These fields no longer exist
- **Safe to delete:** ✅ YES

---

#### File: `tests/conftest.py`

**Line 132:**
```python
customer_name="Test Customer",
```
- **Location:** Inside `test_contract` fixture
- **What it does:** Creates a test Contract with customer_name field
- **Why obsolete:** Contract model no longer has customer_name field
- **Safe to delete:** ✅ YES - This line should be removed

---

#### File: `tests/unit/test_base_repository.py`

**Lines 122, 125, 129:**
```python
test_contract.customer_name = "Updated Customer Name"
assert updated.customer_name == "Updated Customer Name"
assert found.customer_name == "Updated Customer Name"
```
- **Location:** Inside `test_update` method
- **What it does:** Tests updating customer_name field
- **Why obsolete:** customer_name field doesn't exist
- **Safe to delete:** ⚠️ NEEDS REPLACEMENT - Replace with a different field like `contract_type` or `template_version`

---

#### File: `tests/unit/test_models.py`

**Lines 48-68:**
```python
async def test_contract_with_vehicle_info(self, db_session: AsyncSession):
    """Test contract with JSON vehicle info."""
    vehicle_info = {
        "make": "Toyota",
        "model": "Camry",
        "year": 2020,
        "vin": "1234567890",
    }
    contract = Contract(
        contract_id="TEST-002",
        account_number="ACC-67890",
        s3_bucket="test-bucket",
        s3_key="contracts/TEST-002.pdf",
        vehicle_info=vehicle_info,
    )
    # ... assertions on vehicle_info
```
- **Location:** Entire test method `test_contract_with_vehicle_info`
- **What it does:** Tests that Contract can store vehicle_info JSON field
- **Why obsolete:** vehicle_info field no longer exists, and account_number is not on Contract anymore
- **Safe to delete:** ✅ YES - Entire test method can be deleted

---

#### File: `tests/unit/test_contract_service.py`

**Lines 207-225:**
```python
contract = Contract(
    contract_id="TEST-001",
    account_number="ACC-12345",
    s3_bucket="test-bucket",
    s3_key="test.pdf",
    contract_type="GAP",
    customer_name="Test Customer",
    vehicle_info={"make": "Toyota", "model": "Camry"},
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow(),
)
# ...
assert response.customer_name == "Test Customer"
assert response.vehicle_info == {"make": "Toyota", "model": "Camry"}
```
- **Location:** Inside `test_contract_to_response` method
- **What it does:** Tests conversion of Contract ORM to response, including old fields
- **Why obsolete:** Contract no longer has account_number, customer_name, vehicle_info fields
- **Safe to delete:** ⚠️ NEEDS REPLACEMENT - Update test to use template model structure
- **Replacement needed:** Update to use `template_version`, `effective_date`, `is_active`

---

### 1.2 Service Layer - Dead Code

#### File: `app/services/chat_service.py`

**Lines 221-223:**
```python
"account_number": contract.account_number,
"policy_number": contract.policy_number,
"purchase_date": contract.purchase_date.isoformat() if contract.purchase_date else None,
```
- **Location:** Inside `_build_chat_context` method
- **What it does:** Builds chat context from Contract model, referencing fields that don't exist
- **Why obsolete:** Contract model doesn't have account_number, policy_number, or purchase_date
- **Safe to delete:** 🚨 CRITICAL - This code is BROKEN and needs immediate investigation
- **Needs investigation:** Check if this code path is even reached, might already be failing
- **Risk level:** HIGH - Could be causing runtime errors

---

### 1.3 Scripts - Dead Code

#### File: `scripts/setup_s3.py`

**Lines 166-172, 228, 250-256, 410, 421:**
```python
def generate_gap_contract_pdf(
    contract_id: str,
    account_number: str,
    customer_name: str,  # Dead parameter
    make: str,
    model: str,
    year: int,
    # ...
):
    # ...
    ["Customer Name:", customer_name],  # Dead usage
    # ...
    vehicle_info = [  # Variable name suggests old model
        ["Year:", str(year)],
        ["Make:", make],
        ["Model:", model],
        ["VIN:", vin],
    ]
    # ...
    customer_name = f"Test Customer {i+1}"  # Dead variable
    # ...
    customer_name=customer_name,  # Dead argument
```
- **Location:** PDF generation function and its usage
- **What it does:** Generates PDF contracts with customer-specific data
- **Why obsolete:** Script generates FILLED contracts, but system now stores TEMPLATES
- **Safe to delete:** ⚠️ NEEDS REVIEW - This script might be intentionally generating filled examples for testing
- **Action required:** Determine if script should generate templates instead or is kept for test data

---

## 2. FRONTEND DEAD CODE

### 2.1 TypeScript Interface References

#### File: `frontend/__tests__/lib/api/contracts.test.ts`

**Lines 26, 80, 142, 162:**
```typescript
accountNumber: '123456789012',
```
- **Location:** Mock data in multiple tests
- **What it does:** Tests expect API responses to contain accountNumber field
- **Why obsolete:** API response (ContractResponse) doesn't include accountNumber - it's only in the search request
- **Safe to delete:** ⚠️ INVESTIGATE - These are in tests; need to verify current API response structure
- **Action required:** Check if actual API returns accountNumber or if tests are outdated

---

## 3. LEGITIMATE ACCOUNT_NUMBER USAGE (NOT DEAD CODE)

### ✅ Valid Usage in Request/Response Schemas

#### File: `app/schemas/requests.py`
- `ContractSearchRequest` schema has `account_number` field
- **Status:** ✅ VALID - Used for searching templates by account number

#### File: `app/schemas/responses.py`
- `ChatResponse` schema has `detected_account_number` field
- **Status:** ✅ VALID - Used to return detected account numbers from chat

### ✅ Valid Usage in Account Mapping Infrastructure

#### File: `app/models/database/account_mapping.py`
- `AccountTemplateMapping` model with `account_number` column
- **Status:** ✅ VALID - This is the NEW location for account numbers

#### File: `app/repositories/account_mapping_repository.py`
- Repository methods using `account_number`
- **Status:** ✅ VALID - Core to the new template-based model

### ✅ Valid Usage in Service Layer

#### File: `app/services/contract_service.py`
- `search_by_account_number` method
- **Status:** ✅ VALID - Implements hybrid cache lookup by account

#### File: `app/services/audit_service.py`
- `log_search` method with `account_number` parameter
- **Status:** ✅ VALID - Audit logging for searches

### ✅ Valid Usage in Chat Service

#### File: `app/services/chat_service.py`
- `AccountNumberDetector` class
- **Status:** ✅ VALID - Detects account numbers in user messages

### ✅ Valid Usage in Frontend

#### Files: `frontend/components/chat/CollapsibleChat.tsx`, `frontend/app/dashboard/page.tsx`, `frontend/app/page.tsx`
- Display and search functionality for account numbers
- **Status:** ✅ VALID - These are UI/UX features, not tied to Contract model
- **Action:** NONE - This is legitimate functionality

---

## 4. SUMMARY OF DELETABLE CODE

### 🔴 High Priority (Definitely Dead)

1. ✅ **tests/integration/test_contracts_api.py** - Lines 38-39, 107-108
   - Remove assertions for customer_name and vehicle_info

2. ✅ **tests/conftest.py** - Line 132
   - Remove customer_name parameter from test_contract fixture

3. ✅ **tests/unit/test_models.py** - Lines 48-68
   - Delete entire `test_contract_with_vehicle_info` test method

4. ⚠️ **tests/unit/test_base_repository.py** - Lines 122, 125, 129
   - Replace customer_name with valid template field (e.g., `template_version`)

### 🟡 Medium Priority (Needs Investigation)

5. ⚠️ **tests/unit/test_contract_service.py** - Lines 207-225
   - Update `test_contract_to_response` to use template model
   - Remove account_number, customer_name, vehicle_info references
   - Add template_version, effective_date, is_active

6. 🚨 **app/services/chat_service.py** - Lines 221-223
   - **CRITICAL:** Verify if contract.account_number, contract.policy_number, contract.purchase_date exist
   - If not, this code is broken and needs immediate fix
   - Replace with template-appropriate fields

### 🟢 Low Priority (Evaluate Purpose)

7. ⚠️ **scripts/setup_s3.py** - Multiple lines
   - Determine if script should generate templates or filled contracts
   - If templates: Remove customer_name, vehicle details
   - If test data: Mark as test-only, document purpose

8. ⚠️ **Frontend tests** - `__tests__/lib/api/contracts.test.ts`
   - Verify if accountNumber should be in mock responses
   - Check against actual API contract

---

## 5. RISK ASSESSMENT

### 🔴 Code That WILL Break If Not Updated

1. **tests/unit/test_models.py:48-68** - Tries to set vehicle_info on Contract ❌
2. **tests/conftest.py:132** - Tries to set customer_name on Contract ❌
3. **tests/unit/test_base_repository.py:122** - Tries to update customer_name ❌

### 🟡 Code That MIGHT Already Be Broken

1. **app/services/chat_service.py:221-223** - References contract.account_number, contract.policy_number, contract.purchase_date
   - These fields don't exist on current Contract model
   - 🚨 Needs immediate investigation

### 🟢 Code That's Just Checking Wrong Things

1. **tests/integration/test_contracts_api.py:38-39, 107-108** - Assertions will fail
2. **tests/unit/test_contract_service.py:224-225** - Assertions expect non-existent fields

---

## 6. RECOMMENDED ACTION PLAN

### Phase 1: Fix Broken Tests (Immediate) ⏱️ 1-2 hours

1. ✅ Remove/update all test assertions for customer_name, vehicle_info
2. ✅ Update test fixtures to not use removed fields
3. ✅ Verify all tests pass after changes

**Files to modify:**
- `tests/integration/test_contracts_api.py`
- `tests/conftest.py`
- `tests/unit/test_models.py`
- `tests/unit/test_base_repository.py`
- `tests/unit/test_contract_service.py`

### Phase 2: Investigate Chat Service (Urgent) ⏱️ 30 min

1. 🚨 Check if chat_service.py lines 221-223 are causing runtime errors
2. 🔍 If broken, update to use template model fields
3. ✅ Test chat functionality thoroughly

**File to investigate:**
- `app/services/chat_service.py`

### Phase 3: Clean Up Scripts (Low Priority) ⏱️ 1 hour

1. Review setup_s3.py purpose
2. Update or document as test-only if needed

**File to review:**
- `scripts/setup_s3.py`

### Phase 4: Verify Frontend (Validation) ⏱️ 30 min

1. Check frontend tests against actual API responses
2. Update mock data to match current API contract

**File to check:**
- `frontend/__tests__/lib/api/contracts.test.ts`

---

## 7. DETAILED CLEANUP CHECKLIST

### Backend Tests

- [ ] `tests/integration/test_contracts_api.py:38-39` - Remove customer_name/vehicle_info assertions
- [ ] `tests/integration/test_contracts_api.py:107-108` - Remove customer_name/vehicle_info assertions
- [ ] `tests/conftest.py:132` - Remove customer_name parameter
- [ ] `tests/unit/test_models.py:48-68` - Delete entire test_contract_with_vehicle_info method
- [ ] `tests/unit/test_base_repository.py:122,125,129` - Replace customer_name with template_version
- [ ] `tests/unit/test_contract_service.py:207-225` - Update to template model

### Backend Services

- [ ] `app/services/chat_service.py:221-223` - **CRITICAL** - Investigate and fix

### Scripts

- [ ] `scripts/setup_s3.py` - Review purpose and update or document

### Frontend Tests

- [ ] `frontend/__tests__/lib/api/contracts.test.ts` - Verify mock data structure

---

## 8. CONCLUSION

**Total identified instances of dead code:**
- **Backend Tests:** 8 locations across 4 test files
- **Backend Services:** 1 location in chat_service (🚨 CRITICAL - might be broken)
- **Backend Scripts:** 1 script file (needs evaluation)
- **Frontend Tests:** 4 locations in 1 test file (needs verification)

**Estimated effort:** 2-4 hours to clean up all dead code and verify tests pass.

**Highest risk:** The chat_service.py code that references non-existent Contract fields - this could be causing runtime errors if that code path is executed.

**Next Steps:**
1. Start with Phase 1 (Fix Broken Tests) to get test suite passing
2. Immediately investigate Phase 2 (Chat Service) for potential runtime errors
3. Schedule Phase 3 and 4 as lower priority cleanup

---

**Report Generated:** 2025-11-25
**Last Updated:** 2025-11-25
**Status:** Ready for Implementation
