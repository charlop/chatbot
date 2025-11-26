# Backend LLM Prompt Updates for PDF Highlighting

**Date**: 2025-11-26
**Status**: ✅ Complete
**Duration**: ~30 minutes

## Summary

Updated both LLM providers (Anthropic and OpenAI) to return exact text snippets in extraction responses. This enables the frontend PDF highlighting feature to locate and highlight extracted fields in the PDF viewer.

## Changes Made

### 1. Base Schema Documentation (`app/integrations/llm_providers/base.py`)

**Updated**: `FieldExtraction` source field description to include "text" requirement
**Updated**: Example JSON to demonstrate new format with text snippets

**Example**:
```python
"source": {
    "page": 3,
    "text": "GAP Insurance Premium: $1,249.00",  # New required field
    "section": "Pricing",
    "line": 18
}
```

### 2. Anthropic Provider (`app/integrations/llm_providers/anthropic_provider.py`)

**Modified Function**: `_build_extraction_tool()`
- Updated source schema for all three fields (gap_insurance_premium, refund_calculation_method, cancellation_fee)
- Added "text" field as required alongside "page"
- Added detailed descriptions for each source property

**Schema Changes**:
```python
"source": {
    "type": "object",
    "properties": {
        "page": {
            "type": "integer",
            "description": "Page number where the text was found",
        },
        "text": {
            "type": "string",
            "description": "Exact text snippet extracted from the PDF (e.g., 'GAP Insurance Premium: $500.00')",
        },
        "section": {
            "type": "string",
            "description": "Section name (optional)",
        },
        "line": {
            "type": "integer",
            "description": "Approximate line number (optional)",
        },
    },
    "required": ["page", "text"],  # Text is now required
    "description": "Source location in the PDF document with exact text snippet",
}
```

**Modified Prompt**: Updated extraction prompt to emphasize exact text extraction
```python
prompt = f"""...
For each field, provide:
- The exact value (or null if not found)
- Your confidence level (0-100)
- Source location:
  * page: The page number where you found this information
  * text: The EXACT text snippet from the document as written (e.g., "GAP Insurance Premium: $500.00")
  * section: Optional section name
  * line: Optional approximate line number

IMPORTANT: For the "text" field, copy the exact wording from the document verbatim. Do not paraphrase or summarize.
This text will be used to locate and highlight the information in the PDF viewer.
..."""
```

### 3. OpenAI Provider (`app/integrations/llm_providers/openai_provider.py`)

**Modified Function**: `_build_extraction_function()`
- Updated source schema for all three fields (identical to Anthropic)
- Made "text" field required in source objects

**Modified Function**: `_build_extraction_prompt()`
- Updated prompt with same instructions as Anthropic provider
- Emphasizes verbatim text copying for PDF highlighting

## Testing

### Backend Tests
✅ **All 23 LLM provider tests passing**

Test command:
```bash
cd /Users/chris/dev/chatbot/project/backend
source .venv/bin/activate
python3 -m pytest tests/unit/test_llm_providers.py -v
```

Results:
- OpenAIProvider: 9 tests passed
- AnthropicProvider: 8 tests passed
- FieldExtraction: 4 tests passed
- ExtractionResult: 2 tests passed

### Frontend Tests
✅ **All 49 PDF highlighting tests passing**

Test command:
```bash
cd /Users/chris/dev/chatbot/project/frontend
npm test -- __tests__/lib/pdf/ __tests__/components/pdf/ __tests__/hooks/useHighlights.test.ts __tests__/integration/pdf-highlighting.test.tsx --run
```

Results:
- PDFTextExtractor: 4 tests
- TextLocationCache: 7 tests
- HighlightOverlay: 9 tests
- PDFControls: 15 tests
- useHighlights: 6 tests
- Integration: 8 tests

### TypeScript Compilation
✅ **No errors** - `npx tsc --noEmit` passed

## Data Flow

### Before (Old Format):
```json
{
  "gap_insurance_premium": {
    "value": 500.00,
    "confidence": 95.5,
    "source": {
      "page": 1,
      "section": "Coverage Details",
      "line": 42
    }
  }
}
```

**Problem**: Frontend has page number but must search entire page for text to highlight

### After (New Format):
```json
{
  "gap_insurance_premium": {
    "value": 500.00,
    "confidence": 95.5,
    "source": {
      "page": 1,
      "text": "GAP Insurance Premium: $500.00",
      "section": "Coverage Details"
    }
  }
}
```

**Benefit**: Frontend can search for exact text snippet, enabling precise highlighting

## Frontend Integration

The frontend `useHighlights` hook uses the "text" field for precise text search:

```typescript
// Check if we have cached bbox from backend
if (source.bbox) {
  // Use pre-calculated coordinates (instant)
  return createHighlight(source.bbox, confidence);
}

// Check in-memory cache
let location = textLocationCache.get(contractId, page, text);
if (location) {
  // Cache hit (~1ms)
  return createHighlight(location.bbox, confidence);
}

// Cache miss - search for text in PDF
location = await extractor.findTextLocation(text, page);
if (location) {
  textLocationCache.set(contractId, page, text, location);
  return createHighlight(location.bbox, confidence);
}
```

## Backward Compatibility

✅ The frontend is fully backward compatible:
- If `source` is a string (old format): Uses page-level fallback
- If `source.text` exists (new format): Uses precise text search
- If neither: Gracefully degrades without highlights

## Next Steps

### Optional Backend Enhancement:
Save frontend-calculated bbox back to database for faster subsequent loads:

```python
# In extraction service after frontend returns bbox
extraction.gap_premium_source = {
    "page": 1,
    "text": "GAP Insurance Premium: $500.00",
    "bbox": {"x": 72, "y": 150, "width": 200, "height": 12}  # Cached from frontend
}
```

This creates a three-tier caching system:
1. **Backend bbox cache** (instant) ← Optional future enhancement
2. **Frontend in-memory cache** (~1ms) ← Already implemented
3. **PDF text search** (100-200ms) ← Fallback

### Manual Testing Recommendations:
1. Upload a new contract to trigger LLM extraction
2. Verify extraction response includes "text" field in source objects
3. Verify PDF viewer highlights extracted fields correctly
4. Check that exact text matches between extraction and PDF

## Files Modified

1. `/project/backend/app/integrations/llm_providers/base.py`
   - Updated FieldExtraction source documentation
   - Updated example JSON

2. `/project/backend/app/integrations/llm_providers/anthropic_provider.py`
   - Updated `_build_extraction_tool()` schema (lines 43-163)
   - Updated extraction prompt (lines 188-212)

3. `/project/backend/app/integrations/llm_providers/openai_provider.py`
   - Updated `_build_extraction_function()` schema (lines 61-138)
   - Updated `_build_extraction_prompt()` (lines 38-66)

## Success Criteria

- [x] Anthropic provider requires "text" field in all source objects
- [x] OpenAI provider requires "text" field in all source objects
- [x] Prompts instruct LLMs to extract exact text verbatim
- [x] All 23 backend LLM tests passing
- [x] All 49 frontend PDF tests passing
- [x] TypeScript compilation successful
- [x] Backward compatible with existing data

---

**Status**: ✅ **COMPLETE AND TESTED**
**Ready for**: Manual testing with real contract uploads
