# UI Mockup - Finance Specialist Interface

## Design Overview

Clean, modern split-screen layout optimized for finance specialists conducting detailed reviews of contract refund eligibility. The design prioritizes whitespace, subtle shadows over borders, and a conversational AI interface integrated directly into the workflow.

## Color System - Lightspeed Design System

**Primary Colors:**
- Purple: `#954293` (interactive elements, brand)
- Deep Purple: `#650360` (emphasized text, highlights)
- Dark Purple: `#300942` (reserved for future use)
- Light Purple: `#fee6ff` (backgrounds, highlights)
- Purple Accent: `#df9dde` (reserved for future use)

**Secondary Colors:**
- Teal: `#00857f` (reserved for future use)
- Seafoam: `#1c988a` (reserved for future use)
- Light Teal: `#5de2cc` (reserved for future use)
- Seafoam Light: `#e3fffa` (reserved for future use)

**Neutral Palette:**
- White: `#ffffff` (cards, panels, document background)
- Gray 100: `#f4f4f4` (page background, card backgrounds)
- Gray 200: `#e7eaf7` (borders, inactive UI elements)
- Gray 300: `#f2f2f2` (data field backgrounds)
- Gray 400: `#909090` (muted text, placeholders)
- Gray 500: `#737373` (tertiary text, labels)
- Gray 800: `#2a2a2a` (secondary text, headings)
- Gray 900: `#1a1a1a` (primary text, titles)

**Semantic Colors:**
- Success: `#2da062` / `#40bd70` / `#e3f5ec` (high confidence, approvals)
- Warning: `#fe8700` / `#feb13c` / `#fff4e6` (medium confidence, alerts)
- Error: `#d63440` / `#c02e39` (low confidence, rejections)
- Info: `#2a97da` / `#4ca9d8` (links, informational elements)

**Design Philosophy:** Clean corporate aesthetic with generous spacing, rounded corners (8-12px), and shadow-based depth. Purple-based brand identity maintains professional trust while standing out from typical blue corporate applications.

---

## Layout Structure

### Left Sidebar (64px)
- **Logo/Brand** at top (purple circle with "R")
- **Primary Navigation Icons:**
  - ⚡ Active view (purple highlight)
  - ⏱ History
  - ⚙ Settings
  - 👤 User profile (bottom)
- Minimal width for desktop-focused workflow
- Icons only, no labels (clean aesthetic)

### Main Content (840px)
- **PDF Viewer** occupies primary real estate
- Large rounded container (12px radius)
- Clean toolbar with filename and page controls (zoom, download, options)
- Subtle background (#f2f2f2) with white document area
- In-document annotations with callout boxes

### Right Panel (464px)
- **Contract metadata** (account, contract ID, state, template)
- **Extracted data fields** with per-field confidence
- **Processing audit trail** (timestamp, model, duration)
- **Action buttons** (Approve All, Edit, Reject)
- **Expandable AI Chat** at bottom
- Scrollable if content exceeds height

---

## Finance Specialist UI Features

**File:** `finance-specialist-ui.svg`

### Target Workflow
Detailed review of complex or flagged contracts requiring thorough analysis and documentation.

### Key Features

#### 1. Enhanced Data Display
- **Per-field confidence badges**
  - High (96%, 98%): Green badge (`#2da062` / `#e3f5ec`)
  - Medium (87%): Orange badge (`#fe8700` / `#fff4e6`)
  - Low: Red badge (reserved)
- **Detailed source citations** (page, section, line number)
- **Interactive "View in document" links** for each field
- **Warning highlights** for medium/low confidence items
- **Large, readable values** (26px font) for quick scanning

#### 2. Rich PDF Annotations
- **Callout boxes** directly on PDF for each extracted field
- **Color-coded by confidence level:**
  - High confidence: Light purple background (`#fee6ff`)
  - Medium confidence: Light orange background (`#fff4e6`)
- **Annotation details include:**
  - Confidence indicator (✓ HIGH CONFIDENCE / ⚠ MEDIUM)
  - Extracted value
  - Confidence percentage
  - Link to detailed view
- **Synchronized highlighting** - PDF sections match data cards

#### 3. Multiple Action Paths
- **"Approve All"** (green button, `#2da062`) - Standard approval for high-confidence results
- **"Edit"** (purple button, `#954293`) - Modify and resubmit corrections
- **"Reject"** (outlined button) - Deny with justification
- **Future**: "Request Review" - Escalate to senior staff

#### 4. Comprehensive Audit Trail
Dedicated audit card showing:
- **Full timestamp** with timezone (Nov 4, 2025 10:23:47 AM EST)
- **Model version** identification (GPT-4 v2.1)
- **Processing time** metrics (8.3s)
- **Link to full audit log** for compliance reporting
- Supports event sourcing and immutable audit requirements

#### 5. Expandable AI Chat Interface
- **Collapsed state** (92px height) shown in mockup
- **Previous search context** visible
- **Multi-purpose input:**
  - Search for another contract by account number
  - Ask questions about current contract
  - Request clarification on extracted data
  - General AI assistance with refund calculations
- **Toolbar icons:** 📎 Attachment, 🔍 Search
- **Purple send button** with arrow (`#954293`)
- **Expand indicator** shows it can grow to ~300-400px

#### 6. Confidence-Driven Design
- **Visual hierarchy** based on confidence levels
- **High confidence** = clean, minimal styling
- **Medium confidence** = yellow/orange warning treatment
- **Low confidence** = prominent red warnings (not shown in current data)
- **Helps users prioritize attention** on uncertain extractions

---

## Layout Proportions

- **Sidebar:** 64px (4.4% of screen)
- **PDF Viewer:** 840px (58.3% of screen)
- **Right Panel:** 464px (32.2% of screen)
- **Gap:** 24px between panels
- **Total Width:** 1440px (standard desktop)
- **Height:** 900px (comfortable viewing)

---

## Navigation Menu Mapping

### Sidebar Icons
- **⚡ (Active/Primary)** → Main review interface (current view)
- **⏱ (History)** → Previously processed contracts, search history, audit logs
- **⚙ (Settings)** → User preferences, notification settings, template management
- **👤 (User)** → Profile, logout, admin access (role-based)

### Future Admin Access
Admin section accessible through user menu for permission-based access:
- User management and role assignments
- System configuration and API settings
- Analytics dashboard with accuracy metrics
- Template library management

---

## Design Rationale

### Why This Layout Works

1. **PDF as Primary Focus**
   - Finance specialists need to verify AI extractions against source document
   - Large PDF viewer (840px) provides comfortable reading experience
   - In-document annotations create immediate visual connection
   - Highlighted sections eliminate searching for source data

2. **Confidence-First Approach**
   - Per-field confidence scores enable granular review
   - Color-coded system (green/orange/red) provides instant visual cues
   - Medium/low confidence items get prominent warning treatment
   - Reduces time spent on high-confidence extractions

3. **Audit Trail Visibility**
   - Dedicated audit card satisfies regulatory requirements
   - Model version tracking enables rollback and comparison
   - Timestamp precision supports compliance reporting
   - "View full audit log" provides deep-dive capability

4. **Conversational AI Integration**
   - Expandable chat doesn't interrupt main workflow
   - Positioned at bottom (natural reading flow)
   - Maintains context of current contract
   - Supports both search and analytical queries

5. **Whitespace as Design Element**
   - Generous padding (20-24px) reduces cognitive load
   - Clean cards with rounded corners feel modern
   - Shadow-based depth (not borders) creates hierarchy
   - Purple accents provide visual interest without overwhelming

6. **Role-Specific Optimization**
   - Finance specialists need detail, not speed
   - Multiple action paths support complex workflows
   - Detailed citations enable thorough verification
   - Warning system prevents costly errors

---

## Technical Implementation Notes

### Next.js / React Components

**Core Components:**
```tsx
<Sidebar /> // Navigation with icon mapping
<PDFViewer /> // PDF.js integration with highlighting and annotations
<DataCard /> // Reusable extracted data display with confidence badge
<ConfidenceBadge /> // Color-coded confidence indicator
<ExpandableChat /> // AI chat interface with expand/collapse
<Button /> // Consistent button styles (primary, secondary, outlined)
<AuditTrail /> // Processing metadata display
<AnnotationCallout /> // PDF overlay annotations
```

**Layout Components:**
```tsx
<FinanceReviewLayout>
  <Sidebar />
  <PDFPanel>
    <PDFViewer />
  </PDFPanel>
  <DataPanel>
    <ContractMetadata />
    <ExtractedFields />
    <AuditTrail />
    <ActionButtons />
    <ExpandableChat />
  </DataPanel>
</FinanceReviewLayout>
```

### Tailwind CSS Implementation

Using the Lightspeed design system colors:

```tsx
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          purple: '#954293',
          deep: '#650360',
          dark: '#300942',
          light: '#fee6ff',
          accent: '#df9dde'
        },
        neutral: {
          100: '#f4f4f4',
          200: '#e7eaf7',
          300: '#f2f2f2',
          400: '#909090',
          500: '#737373',
          800: '#2a2a2a',
          900: '#1a1a1a'
        },
        success: {
          primary: '#2da062',
          secondary: '#40bd70',
          light: '#e3f5ec'
        },
        warning: {
          primary: '#fe8700',
          secondary: '#feb13c',
          light: '#fff4e6'
        },
        info: {
          primary: '#2a97da',
          secondary: '#4ca9d8'
        }
      }
    }
  }
}
```

**Example Component Styles:**
```jsx
// Card styling
"bg-white rounded-xl shadow-sm p-6"

// Data field
"bg-neutral-300 rounded-lg p-5"

// High confidence badge
"bg-success-light text-success-primary rounded-full px-3 py-1 text-xs font-semibold"

// Warning badge
"bg-warning-light text-warning-primary rounded-full px-3 py-1 text-xs font-semibold"

// Primary action button
"bg-success-primary hover:bg-success-secondary text-white rounded-lg px-6 py-3 font-semibold"

// Secondary action button (Edit)
"bg-primary-purple hover:bg-primary-deep text-white rounded-lg px-6 py-3 font-semibold"

// Outlined button (Reject)
"bg-white border border-neutral-200 text-neutral-500 hover:border-neutral-400 rounded-lg px-6 py-3 font-semibold"

// Chat input
"bg-white border border-neutral-200 rounded-lg p-4 focus:border-primary-purple"

// Info link
"text-info-primary hover:text-info-secondary"
```

### State Management Considerations

```tsx
// Contract context
const ContractContext = {
  contractId: string
  accountNumber: string
  extractedFields: ExtractedField[]
  confidenceScores: Record<string, number>
  auditLog: AuditEntry[]
  pdfUrl: string
}

// UI state
const [chatExpanded, setChatExpanded] = useState(false)
const [selectedField, setSelectedField] = useState<string | null>(null)
const [pdfScrollPosition, setPdfScrollPosition] = useState(0)

// Sync PDF scroll with data card clicks
const handleFieldClick = (fieldId: string) => {
  setSelectedField(fieldId)
  // Scroll PDF to field location
  pdfViewerRef.current?.scrollToPage(field.pageNumber)
}
```

---

## Responsive Considerations (Future Phase)

While Phase 1 is desktop-only (1440x900), the design adapts naturally for future mobile support:

- **Tablet (768-1024px):** Stack PDF and data panel vertically, maintain sidebar
- **Mobile (<768px):**
  - Collapse sidebar to hamburger menu
  - Full-width PDF viewer
  - Data cards below PDF
  - Chat expands to full-screen modal
  - Touch-friendly button sizes (44px minimum)

---

## Next Steps

1. **Interactive Prototype**
   - Build clickable prototype in Next.js
   - Implement expand/collapse chat transition
   - Add PDF-to-data card synchronization
   - Test hover states and tooltips

2. **User Testing**
   - Validate with 3-5 finance specialists
   - Test confidence scoring comprehension
   - Gather feedback on chat discoverability
   - Measure time-to-approval for test contracts

3. **Additional Screens Needed**
   - **Search/Landing Page** - Initial search interface
   - **History View** - Previously processed contracts with filters
   - **Settings Page** - User preferences, notifications, template management
   - **Admin Interface** - User management (if user has admin role)
   - **Empty States** - No results, loading, errors
   - **Edit Modal** - Interface for correcting extracted values
   - **Rejection Modal** - Capture rejection reason with codes

4. **Interaction Details**
   - Hover state for "View in document" links (highlight PDF section)
   - Loading state during LLM processing (skeleton screens)
   - Success/error toast notifications
   - Keyboard shortcuts for power users (Tab, Enter, Esc)
   - Confidence badge tooltips with methodology explanation

5. **Accessibility**
   - Ensure WCAG 2.1 AA compliance
   - Screen reader optimization
   - Keyboard navigation
   - Color contrast validation (all text meets 4.5:1 minimum)
   - Focus indicators on all interactive elements
