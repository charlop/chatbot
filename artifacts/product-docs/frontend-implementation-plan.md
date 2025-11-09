# Frontend Implementation Plan
## Contract Refund Eligibility System - Detailed Task Breakdown

**Version:** 1.0
**Date:** 2025-11-06
**Duration:** 4 weeks (Weeks 6-9)
**Total Effort:** ~160 hours (20 days × 8 hours)

---

## Overview

This document breaks down the frontend implementation into manageable 8-hour work chunks, following TDD principles and SOLID design patterns.

---

## Tech Stack Summary

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS (Lightspeed design system)
- **PDF Viewer**: PDF.js (react-pdf)
- **State Management**: React Context API + SWR
- **Form Handling**: React Hook Form + Zod
- **HTTP Client**: Axios
- **Auth**: Auth0 React SDK
- **Testing**: Vitest + React Testing Library + Playwright

---

## Week 6: Foundation & Core UI Components (Days 1-5)

### Day 1 (8 hours): Project Setup & Configuration

**Goals**: Set up Next.js project with all dependencies and configuration

**Tasks:**
1. **Initialize Next.js Project** (1 hour)
   ```bash
   npx create-next-app@latest frontend --typescript --tailwind --app
   cd frontend
   ```
   - Configure TypeScript strict mode
   - Set up folder structure
   - Configure path aliases (`@/components`, `@/lib`, etc.)

2. **Install Dependencies** (1 hour)
   ```bash
   npm install axios swr @auth0/auth0-react react-hook-form zod
   npm install react-pdf pdf.js-dist
   npm install -D vitest @testing-library/react @testing-library/jest-dom
   npm install -D @playwright/test
   ```

3. **Configure Tailwind with Lightspeed Colors** (2 hours)
   - Create `tailwind.config.ts` with custom colors
   - Set up design tokens (spacing, typography, shadows)
   - Create base CSS utilities
   - Test color system

4. **Set up Testing Infrastructure** (2 hours)
   - Configure Vitest for unit tests
   - Set up React Testing Library
   - Configure Playwright for E2E tests
   - Create test utilities and mocks
   - Write first test (smoke test)

5. **Configure Environment Variables** (1 hour)
   - Create `.env.local` template
   - Set up Auth0 configuration
   - Set up API base URL
   - Document all required environment variables

6. **Set up CI/CD Pipeline** (1 hour)
   - Create GitHub Actions workflow for frontend
   - Configure test running on PR
   - Set up build verification
   - Configure Docker image build

**Deliverables:**
- ✅ Configured Next.js project
- ✅ Tailwind config with Lightspeed colors
- ✅ Testing infrastructure ready
- ✅ CI/CD pipeline configured

---

### Day 2 (8 hours): Base UI Components (TDD)

**Goals**: Build foundational UI components using TDD

**Tasks:**
1. **Button Component** (2 hours)
   - Write tests first (variants: primary, secondary, success, danger, outline)
   - Implement Button component with Lightspeed styles
   - Add loading state, disabled state, icons
   - Test accessibility (keyboard navigation, ARIA labels)

2. **Input Component** (2 hours)
   - Write tests first (text, number, password, search)
   - Implement Input component
   - Add validation states (error, success)
   - Add helper text and label support

3. **Card Component** (1 hour)
   - Write tests for layout and variants
   - Implement Card component with padding variants
   - Add header, body, footer slots

4. **Modal Component** (2 hours)
   - Write tests for open/close, backdrop click, ESC key
   - Implement Modal with portal rendering
   - Add focus trap, scroll lock
   - Test accessibility

5. **Toast/Notification Component** (1 hour)
   - Write tests for different toast types
   - Implement toast queue system
   - Add auto-dismiss and manual dismiss

**Deliverables:**
- ✅ `components/ui/Button.tsx` with tests
- ✅ `components/ui/Input.tsx` with tests
- ✅ `components/ui/Card.tsx` with tests
- ✅ `components/ui/Modal.tsx` with tests
- ✅ `components/ui/Toast.tsx` with tests
- ✅ Storybook stories for all components (optional but recommended)

---

### Day 3 (8 hours): Auth Integration & Protected Routes

**Goals**: Integrate Auth0 and implement protected routing

**Tasks:**
1. **Auth0 Setup** (1 hour)
   - Create Auth0 application
   - Configure callback URLs
   - Test Auth0 login flow manually

2. **Auth Context & Provider** (2 hours)
   - Write tests for AuthContext
   - Implement `contexts/AuthContext.tsx`
   - Wrap app with Auth0Provider
   - Create useAuth hook

3. **Protected Route Component** (2 hours)
   - Write tests for route protection
   - Implement `components/auth/ProtectedRoute.tsx`
   - Add loading states during auth check
   - Add redirect to login for unauthenticated users

4. **Login Page** (2 hours)
   - Write tests for login flow
   - Implement `app/login/page.tsx`
   - Add Auth0 login button
   - Handle auth callbacks
   - Test error states

5. **Logout Functionality** (1 hour)
   - Write tests for logout
   - Implement logout button in header
   - Clear local state on logout
   - Test session cleanup

**Deliverables:**
- ✅ Auth0 integration complete
- ✅ `contexts/AuthContext.tsx` with tests
- ✅ `components/auth/ProtectedRoute.tsx` with tests
- ✅ Login/logout functionality working
- ✅ Protected routes enforcing authentication

---

### Day 4 (8 hours): API Client & Data Fetching

**Goals**: Create API client with interceptors and SWR hooks

**Tasks:**
1. **Axios Client Setup** (2 hours)
   - Write tests for API client
   - Implement `lib/api/client.ts`
   - Add request interceptor (auth token)
   - Add response interceptor (error handling, token refresh)
   - Add retry logic with exponential backoff

2. **API Service Modules** (3 hours)
   - Write tests for each API service
   - Implement `lib/api/contracts.ts` (search, get contract)
   - Implement `lib/api/extractions.ts` (get, approve, edit, reject)
   - Implement `lib/api/chat.ts` (send message, get history)
   - Implement `lib/api/admin.ts` (user CRUD)

3. **SWR Hooks** (2 hours)
   - Write tests for custom hooks
   - Implement `hooks/useContract.ts`
   - Implement `hooks/useExtraction.ts`
   - Implement `hooks/useChat.ts`
   - Add caching, revalidation strategies

4. **Error Handling** (1 hour)
   - Write tests for error scenarios
   - Implement global error boundary
   - Create error toast notifications
   - Test network failures, 401, 403, 500 errors

**Deliverables:**
- ✅ `lib/api/client.ts` with interceptors
- ✅ API service modules with tests
- ✅ SWR hooks for data fetching
- ✅ Global error handling

---

### Day 5 (8 hours): Layout Components

**Goals**: Build application layout (sidebar, header, main content)

**Tasks:**
1. **Sidebar Component** (2 hours)
   - Write tests for navigation
   - Implement `components/layout/Sidebar.tsx` (64px width)
   - Add navigation icons (dashboard, admin)
   - Add active state styling
   - Add user profile section at bottom

2. **Header Component** (2 hours)
   - Write tests for header actions
   - Implement `components/layout/Header.tsx`
   - Add search bar integration
   - Add user menu (profile, settings, logout)
   - Make responsive (though mobile not priority)

3. **Main Layout Component** (2 hours)
   - Write tests for layout rendering
   - Implement `components/layout/Layout.tsx`
   - Combine sidebar + header + main content
   - Add proper spacing (sidebar: 64px, rest: flex)

4. **Root Layout** (1 hour)
   - Implement `app/layout.tsx`
   - Add global providers (Auth, Toast, etc.)
   - Add global styles
   - Add meta tags, favicon

5. **Dashboard Page Shell** (1 hour)
   - Implement `app/dashboard/page.tsx` (empty for now)
   - Add protected route wrapper
   - Add layout wrapper
   - Test routing

**Deliverables:**
- ✅ `components/layout/Sidebar.tsx` with tests
- ✅ `components/layout/Header.tsx` with tests
- ✅ `components/layout/Layout.tsx` with tests
- ✅ Root layout configured
- ✅ Navigation working

---

## Week 7: Contract Search & Data Display (Days 6-10)

### Day 6 (8 hours): Search Functionality

**Goals**: Implement contract search feature

**Tasks:**
1. **SearchBar Component** (3 hours)
   - Write tests for search input, validation, submission
   - Implement `components/search/SearchBar.tsx`
   - Add account number formatting (XXXX-XXXX-XXXX)
   - Add loading state during search
   - Add error state display
   - Auto-focus on mount

2. **Recent Searches** (2 hours)
   - Write tests for local storage
   - Implement recent searches dropdown
   - Store in localStorage (max 10)
   - Add click to re-search

3. **Search Results Handling** (2 hours)
   - Write tests for different search outcomes
   - Implement success state (redirect to contract view)
   - Implement not found state
   - Implement error state
   - Add loading skeleton

4. **Integration with Dashboard** (1 hour)
   - Add SearchBar to dashboard page
   - Wire up search to API
   - Test end-to-end search flow

**Deliverables:**
- ✅ `components/search/SearchBar.tsx` with tests
- ✅ Recent searches functionality
- ✅ Search integrated with dashboard
- ✅ Error handling for search

---

### Day 7 (8 hours): PDF Viewer Component

**Goals**: Implement PDF viewer with highlighting

**Tasks:**
1. **Basic PDF Viewer** (3 hours)
   - Write tests for PDF loading
   - Implement `components/pdf/PDFViewer.tsx`
   - Integrate react-pdf
   - Add page rendering
   - Handle PDF loading errors

2. **PDF Controls** (2 hours)
   - Write tests for controls
   - Implement `components/pdf/PDFControls.tsx`
   - Add zoom controls (50%, 100%, 150%, 200%, fit-width)
   - Add page navigation (prev, next, jump to page)
   - Add download button

3. **Highlight Overlays** (3 hours)
   - Write tests for highlight positioning
   - Implement highlight overlay system
   - Calculate positions based on page coordinates
   - Add color-coding (green, orange, red by confidence)
   - Add hover effects
   - Test with different PDF sizes

**Deliverables:**
- ✅ `components/pdf/PDFViewer.tsx` with tests
- ✅ `components/pdf/PDFControls.tsx` with tests
- ✅ PDF highlighting working
- ✅ All zoom and navigation features

---

### Day 8 (8 hours): Data Display Components

**Goals**: Build components for displaying extracted data

**Tasks:**
1. **ConfidenceBadge Component** (1 hour)
   - Write tests for color logic
   - Implement `components/extraction/ConfidenceBadge.tsx`
   - Color-code by confidence (green ≥90%, orange 70-89%, red <70%)
   - Add tooltip with explanation

2. **DataCard Component** (3 hours)
   - Write tests for data display, edit mode
   - Implement `components/extraction/DataCard.tsx`
   - Display label, value, confidence badge
   - Add source location link
   - Add "View in document" button
   - Add "Edit" button

3. **DataPanel Component** (2 hours)
   - Write tests for panel layout
   - Implement `components/extraction/DataPanel.tsx` (464px width)
   - Display all 3 data cards
   - Add spacing between cards
   - Make scrollable if needed

4. **EditField Component** (2 hours)
   - Write tests for inline editing
   - Implement `components/extraction/EditField.tsx`
   - Add input field with validation
   - Add save/cancel buttons
   - Add optional reason textarea
   - Handle optimistic updates

**Deliverables:**
- ✅ `components/extraction/ConfidenceBadge.tsx` with tests
- ✅ `components/extraction/DataCard.tsx` with tests
- ✅ `components/extraction/DataPanel.tsx` with tests
- ✅ `components/extraction/EditField.tsx` with tests

---

### Day 9 (8 hours): Audit Trail & Action Buttons

**Goals**: Display audit information and implement approval actions

**Tasks:**
1. **AuditTrail Component** (2 hours)
   - Write tests for audit display
   - Implement `components/audit/AuditTrail.tsx`
   - Display processed by, processed at, model version
   - Display processing time
   - Display corrections made (if any)
   - Format timestamps nicely

2. **Action Buttons** (3 hours)
   - Write tests for approve, reject actions
   - Implement action buttons in DataPanel
   - Add "Approve" button (green, primary)
   - Add "Reject" button (red, outline)
   - Add confirmation modals
   - Handle loading states
   - Show success/error toasts

3. **Contract Context** (2 hours)
   - Write tests for ContractContext
   - Implement `contexts/ContractContext.tsx`
   - Store current contract state
   - Store extraction data
   - Provide update methods

4. **Integration** (1 hour)
   - Wire up all components with context
   - Test complete flow (search → view → approve)

**Deliverables:**
- ✅ `components/audit/AuditTrail.tsx` with tests
- ✅ Action buttons with confirmations
- ✅ `contexts/ContractContext.tsx` with tests
- ✅ End-to-end approval flow working

---

### Day 10 (8 hours): Main Dashboard Integration

**Goals**: Integrate all components into main dashboard view

**Tasks:**
1. **Dashboard Layout** (3 hours)
   - Implement 3-column layout (sidebar 64px + PDF 840px + data 464px)
   - Add responsive behavior (desktop only for now)
   - Test different screen sizes (1440px, 1920px, 2560px)

2. **State Management** (2 hours)
   - Wire up search → contract loading → data display
   - Handle loading states
   - Handle error states
   - Add skeleton loaders

3. **PDF-to-Data Linking** (2 hours)
   - Implement "View in document" functionality
   - Scroll PDF to source location when clicked
   - Highlight correct section in PDF
   - Test with different page numbers

4. **Polish & Testing** (1 hour)
   - Fix any styling issues
   - Test complete user flow
   - Write E2E test for happy path

**Deliverables:**
- ✅ Complete dashboard view functional
- ✅ All components integrated
- ✅ PDF-data linking working
- ✅ E2E test passing

---

## Week 8: Chat Interface & Admin Panel (Days 11-15)

### Day 11 (8 hours): Chat Interface - Basic

**Goals**: Build basic AI chat interface

**Tasks:**
1. **ChatMessage Component** (2 hours)
   - Write tests for user/assistant messages
   - Implement `components/chat/ChatMessage.tsx`
   - Style user messages (right-aligned, purple)
   - Style assistant messages (left-aligned, gray)
   - Add timestamp
   - Add loading indicator for assistant

2. **ChatInterface Component** (4 hours)
   - Write tests for chat functionality
   - Implement `components/chat/ChatInterface.tsx`
   - Add message list (scrollable)
   - Add input box at bottom
   - Add send button
   - Handle message submission
   - Auto-scroll to new messages

3. **Chat API Integration** (2 hours)
   - Wire up chat to API
   - Handle streaming responses (if supported)
   - Add error handling
   - Test with mock data

**Deliverables:**
- ✅ `components/chat/ChatMessage.tsx` with tests
- ✅ `components/chat/ChatInterface.tsx` with tests
- ✅ Basic chat functionality working

---

### Day 12 (8 hours): Chat Interface - Advanced

**Goals**: Add collapsible chat and context features

**Tasks:**
1. **Collapsible Chat** (3 hours)
   - Write tests for expand/collapse
   - Add collapsed state (92px height, input only)
   - Add expanded state (400px height, full chat)
   - Add smooth animation
   - Add expand/collapse button
   - Preserve input text when collapsing

2. **Context Indicator** (2 hours)
   - Show current contract ID in chat
   - Show contract account number
   - Add visual indicator when contract changes

3. **Account Number Detection** (2 hours)
   - Detect when user types account number in chat
   - Trigger contract search automatically
   - Add confirmation before switching contracts
   - Handle search errors

4. **Chat History Persistence** (1 hour)
   - Store chat history in session
   - Restore on page refresh
   - Clear on logout

**Deliverables:**
- ✅ Collapsible chat with smooth animation
- ✅ Contract context indicator
- ✅ Auto-search from chat
- ✅ Chat history persistence

---

### Day 13 (8 hours): Admin Panel - User Management

**Goals**: Build admin panel for user management

**Tasks:**
1. **UserTable Component** (3 hours)
   - Write tests for table display, sorting, filtering
   - Implement `components/admin/UserTable.tsx`
   - Display users with columns: username, email, role, status, actions
   - Add sorting (by username, email, role)
   - Add filtering (by role, status)
   - Add pagination (if many users)

2. **UserForm Component** (3 hours)
   - Write tests for form validation, submission
   - Implement `components/admin/UserForm.tsx`
   - Add fields: email, first name, last name, role
   - Add validation (Zod schema)
   - Handle create and edit modes
   - Add error handling

3. **Admin Page** (2 hours)
   - Implement `app/admin/page.tsx`
   - Add protected route (admin role only)
   - Wire up UserTable
   - Add "Create User" button → modal with UserForm
   - Add edit/delete actions in table

**Deliverables:**
- ✅ `components/admin/UserTable.tsx` with tests
- ✅ `components/admin/UserForm.tsx` with tests
- ✅ Admin page functional
- ✅ Role-based access control working

---

### Day 14 (8 hours): Admin Panel - System Metrics

**Goals**: Add system metrics dashboard to admin panel

**Tasks:**
1. **MetricsCard Component** (2 hours)
   - Write tests for metrics display
   - Implement `components/admin/MetricsCard.tsx`
   - Display metric name, value, change indicator
   - Add icon support
   - Add trend indicator (up/down arrow with %)

2. **Metrics Dashboard** (4 hours)
   - Create metrics API endpoint calls
   - Implement metrics display in admin page
   - Show total contracts processed
   - Show average extraction time
   - Show cache hit rate
   - Show daily active users
   - Add date range picker

3. **Charts** (2 hours)
   - Add lightweight chart library (e.g., Recharts)
   - Implement extraction trend chart (last 7 days)
   - Implement confidence score chart

**Deliverables:**
- ✅ `components/admin/MetricsCard.tsx` with tests
- ✅ System metrics dashboard
- ✅ Charts displaying trends

---

### Day 15 (8 hours): Polish & Responsiveness

**Goals**: Polish UI, add micro-interactions, improve UX

**Tasks:**
1. **Loading States** (2 hours)
   - Add skeleton loaders for all async content
   - Add loading spinners for actions
   - Add progress indicators for PDF loading

2. **Empty States** (1 hour)
   - Add empty state for no search results
   - Add empty state for no chat history
   - Add empty state for no users (admin panel)

3. **Micro-interactions** (2 hours)
   - Add hover effects to buttons
   - Add transition animations
   - Add fade-in animations for content
   - Add success animations (checkmark, etc.)

4. **Accessibility** (2 hours)
   - Test keyboard navigation
   - Add ARIA labels where missing
   - Test with screen reader
   - Fix contrast issues

5. **Cross-browser Testing** (1 hour)
   - Test in Chrome, Edge, Safari
   - Fix any browser-specific issues

**Deliverables:**
- ✅ Loading states everywhere
- ✅ Empty states for all scenarios
- ✅ Smooth micro-interactions
- ✅ Accessibility improvements
- ✅ Cross-browser compatibility

---

## Week 9: Testing, Documentation, & Deployment (Days 16-20)

### Day 16 (8 hours): Unit Test Coverage

**Goals**: Achieve >90% unit test coverage

**Tasks:**
1. **Component Tests** (4 hours)
   - Write missing tests for all components
   - Test edge cases
   - Test error scenarios
   - Test accessibility

2. **Hook Tests** (2 hours)
   - Test all custom hooks
   - Test error handling in hooks
   - Test caching behavior (SWR)

3. **Utility Tests** (1 hour)
   - Test formatters (currency, date)
   - Test validators

4. **Coverage Report** (1 hour)
   - Generate coverage report
   - Identify gaps
   - Write tests for uncovered code

**Deliverables:**
- ✅ >90% code coverage
- ✅ All edge cases tested
- ✅ Coverage report generated

---

### Day 17 (8 hours): Integration Tests

**Goals**: Write integration tests for key user flows

**Tasks:**
1. **Auth Flow Tests** (2 hours)
   - Test login flow
   - Test logout flow
   - Test protected routes
   - Test token expiration

2. **Search-to-View Flow** (2 hours)
   - Test searching for contract
   - Test contract display
   - Test PDF loading
   - Test data display

3. **Approval Flow** (2 hours)
   - Test editing extraction
   - Test approving extraction
   - Test rejecting extraction
   - Test error handling

4. **Admin Flow** (2 hours)
   - Test user creation
   - Test user editing
   - Test role changes
   - Test metrics display

**Deliverables:**
- ✅ Integration tests for all major flows
- ✅ All tests passing

---

### Day 18 (8 hours): End-to-End Tests (Playwright)

**Goals**: Write E2E tests for critical paths

**Tasks:**
1. **E2E Test Setup** (1 hour)
   - Configure Playwright
   - Set up test fixtures
   - Set up mock auth

2. **Happy Path Test** (3 hours)
   - Test: Login → Search → View → Approve
   - Test with real API (or comprehensive mocks)
   - Verify all UI elements present
   - Verify data persistence

3. **Error Path Tests** (2 hours)
   - Test: Contract not found
   - Test: API error during search
   - Test: Network failure during approval

4. **Admin E2E Test** (2 hours)
   - Test: Admin login → User management → Create user
   - Verify new user appears in table

**Deliverables:**
- ✅ E2E tests for critical paths
- ✅ All E2E tests passing
- ✅ Screenshots/videos of test runs

---

### Day 19 (8 hours): Documentation & Storybook

**Goals**: Create comprehensive documentation

**Tasks:**
1. **Component Documentation** (3 hours)
   - Set up Storybook
   - Create stories for all UI components
   - Add controls and variations
   - Add documentation notes

2. **Developer Documentation** (3 hours)
   - Write README.md for frontend
   - Document project structure
   - Document available scripts
   - Document environment variables
   - Create developer onboarding guide

3. **User Documentation** (2 hours)
   - Create user guide (screenshots + instructions)
   - Document search functionality
   - Document review process
   - Document admin panel

**Deliverables:**
- ✅ Storybook with all components
- ✅ Developer README
- ✅ User guide

---

### Day 20 (8 hours): Build, Docker, & Deployment

**Goals**: Prepare frontend for production deployment

**Tasks:**
1. **Production Build** (2 hours)
   - Optimize bundle size
   - Add environment-specific configs
   - Test production build locally
   - Fix any build warnings

2. **Docker Image** (2 hours)
   - Create Dockerfile
   - Create .dockerignore
   - Build Docker image
   - Test Docker image locally
   - Push to ECR

3. **Deployment Configuration** (2 hours)
   - Configure ECS task definition
   - Set up ALB routing
   - Configure CloudFront (if needed)
   - Set up environment variables in ECS

4. **Health Checks & Monitoring** (1 hour)
   - Add health check endpoint
   - Configure CloudWatch logs
   - Set up error tracking (Sentry or similar)

5. **Final Testing** (1 hour)
   - Deploy to staging
   - Smoke test all features
   - Verify authentication works
   - Verify API integration works

**Deliverables:**
- ✅ Production-ready build
- ✅ Docker image in ECR
- ✅ Deployed to staging environment
- ✅ All features working in staging

---

## Summary: Task Checklist

### Week 6: Foundation (Days 1-5)
- [ ] Day 1: Project setup, dependencies, testing infrastructure
- [ ] Day 2: Base UI components (Button, Input, Card, Modal, Toast)
- [ ] Day 3: Auth integration (Auth0, protected routes)
- [ ] Day 4: API client, SWR hooks, error handling
- [ ] Day 5: Layout components (Sidebar, Header, Layout)

### Week 7: Contract Display (Days 6-10)
- [ ] Day 6: Search functionality
- [ ] Day 7: PDF viewer with highlighting
- [ ] Day 8: Data display components (ConfidenceBadge, DataCard, DataPanel, EditField)
- [ ] Day 9: Audit trail, action buttons, contract context
- [ ] Day 10: Dashboard integration, PDF-data linking

### Week 8: Chat & Admin (Days 11-15)
- [ ] Day 11: Chat interface - basic
- [ ] Day 12: Chat interface - advanced (collapsible, context)
- [ ] Day 13: Admin panel - user management
- [ ] Day 14: Admin panel - system metrics
- [ ] Day 15: Polish, responsiveness, accessibility

### Week 9: Testing & Deploy (Days 16-20)
- [ ] Day 16: Unit test coverage (>90%)
- [ ] Day 17: Integration tests
- [ ] Day 18: E2E tests (Playwright)
- [ ] Day 19: Documentation & Storybook
- [ ] Day 20: Build, Docker, deployment

---

## Dependencies & Risks

### Dependencies
- [ ] Auth0 account configured (Day 3)
- [ ] Backend API available (mock or real) (Day 4)
- [ ] Lightspeed design assets/guidelines (Day 1)
- [ ] Sample PDF files for testing (Day 7)

### Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| PDF.js performance issues with large PDFs | Medium | Medium | Implement virtual scrolling, lazy loading |
| Auth0 integration complexity | Low | High | Follow official docs, use provided SDK |
| Backend API not ready | Medium | High | Use MSW (Mock Service Worker) for API mocking |
| Highlighting accuracy on PDFs | Medium | Medium | Test with variety of PDF formats, fallback to page-level |
| Scope creep (adding features) | High | Medium | Strict adherence to PRD, defer enhancements to Phase 2 |

---

## Testing Strategy

### Unit Tests (Vitest + React Testing Library)
- Test all components in isolation
- Test all hooks
- Test all utility functions
- Target: >90% coverage

### Integration Tests
- Test component interactions
- Test data flow (context → components)
- Test form submissions
- Test error handling

### E2E Tests (Playwright)
- Test critical user paths
- Test on Chrome, Firefox, Safari
- Generate test reports with screenshots

### Manual Testing
- Test on different screen sizes (1440px, 1920px, 2560px)
- Test accessibility (keyboard navigation, screen reader)
- Test performance (Lighthouse scores)

---

## Performance Targets

| Metric | Target | How to Measure |
|--------|--------|----------------|
| First Contentful Paint (FCP) | < 1.5s | Lighthouse |
| Largest Contentful Paint (LCP) | < 2.5s | Lighthouse |
| Time to Interactive (TTI) | < 3.5s | Lighthouse |
| Bundle Size (gzipped) | < 300KB | webpack-bundle-analyzer |
| Lighthouse Score | > 90 | Lighthouse |

---

## Next Steps After Frontend Complete

1. Integration testing with real backend
2. UAT with 5-10 finance users
3. Performance optimization based on real usage
4. Bug fixes from UAT feedback
5. Production deployment
6. Post-launch monitoring

---

**Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-06 | Claude Code | Initial frontend implementation plan with 20-day breakdown |

---

**End of Frontend Implementation Plan**
