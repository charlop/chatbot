# Frontend Admin Panel - Detailed Implementation Plan

**Sprint**: 1.2 Frontend: Admin Panel - User Management
**Status**: In Progress (API client complete)
**Created**: 2025-11-29
**Estimated Effort**: 1-2 days remaining

---

## Current Status

### ✅ Completed Components

1. **Admin API Client** (`lib/api/admin.ts`)
   - Full TypeScript interfaces for User, UserListResponse
   - CRUD operations: getUsers, getUser, createUser, updateUser, deleteUser
   - Proper error handling via apiClient
   - Ready for consumption by React components

2. **Sidebar Navigation** (`components/layout/Sidebar.tsx`)
   - Admin link already configured with settings icon
   - Route: `/admin`
   - Proper active state styling

---

## Remaining Implementation

### 1. UserTable Component

**File**: `project/frontend/components/admin/UserTable.tsx`

**Purpose**: Display users in a sortable, filterable table

**Props Interface**:
```typescript
interface UserTableProps {
  users: User[];
  onEdit: (user: User) => void;
  onDelete: (userId: string) => void;
  isLoading?: boolean;
}
```

**Features**:
- Table columns: Name (First + Last), Email, Role, Status (Active/Inactive), Actions
- Sort by: Name, Email, Role, Status
- Filter by: Role (admin/user), Active status
- Action buttons: Edit (pencil icon), Delete (trash icon)
- Empty state when no users
- Loading state with skeleton rows

**Styling Pattern** (from existing components):
- Use Tailwind classes
- Table: `border border-neutral-200 rounded-lg`
- Headers: `bg-neutral-50 text-neutral-700 font-semibold`
- Rows: `hover:bg-neutral-50 border-b border-neutral-200`
- Badges for role/status with color coding

**Dependencies**:
- User type from `lib/api/admin.ts`
- No external table library (use native HTML table)

---

### 2. UserForm Component

**File**: `project/frontend/components/admin/UserForm.tsx`

**Purpose**: Form for creating/editing users with validation

**Props Interface**:
```typescript
interface UserFormProps {
  user?: User; // undefined for create, provided for edit
  onSubmit: (data: CreateUserRequest | UpdateUserRequest) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}
```

**Form Fields**:
1. Email (required for create, optional for update)
   - Type: email input
   - Validation: Email format
2. First Name (optional)
   - Type: text input
3. Last Name (optional)
   - Type: text input
4. Role (required for create, defaults to 'user')
   - Type: select dropdown
   - Options: 'admin', 'user'
5. Auth Provider (required for create only)
   - Type: text input
   - Hidden on edit
6. Auth Provider User ID (required for create only)
   - Type: text input
   - Hidden on edit

**Validation Schema** (Zod):
```typescript
const createUserSchema = z.object({
  email: z.string().email('Invalid email format'),
  firstName: z.string().optional(),
  lastName: z.string().optional(),
  role: z.enum(['admin', 'user']),
  authProvider: z.string().min(1, 'Auth provider is required'),
  authProviderUserId: z.string().min(1, 'Auth provider user ID is required'),
});

const updateUserSchema = z.object({
  email: z.string().email('Invalid email format').optional(),
  firstName: z.string().optional(),
  lastName: z.string().optional(),
  role: z.enum(['admin', 'user']).optional(),
  isActive: z.boolean().optional(),
});
```

**Styling Pattern**:
- Form: `space-y-4`
- Labels: `block text-sm font-medium text-neutral-700 mb-1`
- Inputs: `w-full px-3 py-2 border border-neutral-300 rounded-md focus:ring-2 focus:ring-primary-500`
- Buttons: Primary for submit, secondary for cancel
- Error messages: `text-sm text-red-600 mt-1`

**State Management**:
- Use `react-hook-form` with Zod resolver
- Display validation errors inline
- Disable submit during loading

---

### 3. Admin Page

**File**: `project/frontend/app/admin/page.tsx`

**Purpose**: Main admin page combining table and form

**Layout Structure**:
```
┌─────────────────────────────────────────┐
│ Admin Panel Header                       │
│ [+ Create User Button]                   │
├─────────────────────────────────────────┤
│                                          │
│ UserTable                                │
│ - List of users                          │
│ - Edit/Delete actions                    │
│                                          │
└─────────────────────────────────────────┘

Modal (when create/edit clicked):
┌─────────────────────────────────────────┐
│ [X] Create User / Edit User             │
├─────────────────────────────────────────┤
│ UserForm                                 │
│ - Form fields                            │
│ - Submit/Cancel buttons                  │
└─────────────────────────────────────────┘
```

**State Management**:
```typescript
const [users, setUsers] = useState<User[]>([]);
const [isModalOpen, setIsModalOpen] = useState(false);
const [editingUser, setEditingUser] = useState<User | undefined>();
const [isLoading, setIsLoading] = useState(false);
```

**Key Functions**:
1. `loadUsers()` - Fetch users from API on mount
2. `handleCreateClick()` - Open modal in create mode
3. `handleEditClick(user)` - Open modal in edit mode with user data
4. `handleDeleteClick(userId)` - Show confirmation, then delete
5. `handleFormSubmit(data)` - Create or update user, refresh list
6. `handleModalClose()` - Close modal, reset state

**Modal Component**:
- Use a simple custom modal or headlessui Dialog
- Backdrop: `bg-black bg-opacity-50`
- Modal: `bg-white rounded-lg shadow-xl max-w-md w-full p-6`
- Close on backdrop click
- Close on Escape key

**Error Handling**:
- Toast notifications for success/error
- Display API errors from backend

**Auth Check** (stub for now):
```typescript
// TODO: Add proper auth check when auth is implemented
// For now, allow all users to access
```

---

### 4. Component Tests

#### 4.1 UserTable Tests

**File**: `project/frontend/__tests__/components/admin/UserTable.test.tsx`

**Test Cases**:
1. ✓ Renders table with user data
2. ✓ Displays user name, email, role, status correctly
3. ✓ Shows empty state when no users
4. ✓ Shows loading state with skeleton
5. ✓ Calls onEdit when edit button clicked
6. ✓ Calls onDelete when delete button clicked
7. ✓ Sorts by name when column header clicked
8. ✓ Filters by role
9. ✓ Filters by active status
10. ✓ Displays role badge with correct color

**Test Pattern**:
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { UserTable } from '@/components/admin/UserTable';

describe('UserTable', () => {
  const mockUsers = [
    { userId: '1', email: 'admin@test.com', role: 'admin', ... },
    { userId: '2', email: 'user@test.com', role: 'user', ... },
  ];

  it('renders table with user data', () => {
    render(<UserTable users={mockUsers} onEdit={vi.fn()} onDelete={vi.fn()} />);
    expect(screen.getByText('admin@test.com')).toBeInTheDocument();
  });
});
```

#### 4.2 UserForm Tests

**File**: `project/frontend/__tests__/components/admin/UserForm.test.tsx`

**Test Cases**:
1. ✓ Renders create form with all fields
2. ✓ Renders edit form without auth fields
3. ✓ Validates email format
4. ✓ Shows error for invalid email
5. ✓ Calls onSubmit with correct data
6. ✓ Calls onCancel when cancel clicked
7. ✓ Disables submit during loading
8. ✓ Pre-fills form when editing user
9. ✓ Validates required fields for create mode
10. ✓ Allows optional fields to be empty

**Test Pattern**:
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { UserForm } from '@/components/admin/UserForm';

describe('UserForm', () => {
  it('validates email format', async () => {
    const onSubmit = vi.fn();
    render(<UserForm onSubmit={onSubmit} onCancel={vi.fn()} />);

    const emailInput = screen.getByLabelText(/email/i);
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
    fireEvent.click(screen.getByText(/submit/i));

    await waitFor(() => {
      expect(screen.getByText(/invalid email format/i)).toBeInTheDocument();
    });
    expect(onSubmit).not.toHaveBeenCalled();
  });
});
```

#### 4.3 Admin API Tests

**File**: `project/frontend/__tests__/lib/api/admin.test.ts`

**Test Cases**:
1. ✓ getUsers() calls correct endpoint with params
2. ✓ getUser() calls correct endpoint with userId
3. ✓ createUser() posts to correct endpoint
4. ✓ updateUser() puts to correct endpoint
5. ✓ deleteUser() deletes correct endpoint
6. ✓ Handles API errors correctly
7. ✓ Transforms response data correctly

**Test Pattern**:
```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { adminApi } from '@/lib/api/admin';
import { apiClient } from '@/lib/api/client';

vi.mock('@/lib/api/client');

describe('adminApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('getUsers calls correct endpoint', async () => {
    const mockResponse = { data: { users: [], total: 0, offset: 0, limit: 100 } };
    vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

    await adminApi.getUsers({ limit: 10 });

    expect(apiClient.get).toHaveBeenCalledWith('/admin/users', {
      params: { limit: 10 }
    });
  });
});
```

---

## Implementation Order

**Phase 1: Core Components** (4-6 hours)
1. Create UserTable component with basic display
2. Create UserForm component with validation
3. Write component tests (TDD approach)

**Phase 2: Integration** (2-3 hours)
1. Create admin page connecting components
2. Add modal functionality
3. Integrate with admin API

**Phase 3: Polish** (1-2 hours)
1. Add loading states
2. Add error handling
3. Add success/error notifications
4. Ensure responsive design

**Phase 4: Testing** (1-2 hours)
1. Write admin API tests
2. Test full user flow end-to-end
3. Fix any bugs found

**Total Estimated Time**: 8-13 hours (1-2 days)

---

## Design System Reference

### Colors (from existing components)
- Primary: `bg-primary-500`, `text-primary-500`, `border-primary-500`
- Neutral: `bg-neutral-50` (backgrounds), `text-neutral-700` (text), `border-neutral-200` (borders)
- Success: `bg-green-50`, `text-green-700`, `border-green-200`
- Error: `bg-red-50`, `text-red-700`, `border-red-200`
- Warning: `bg-yellow-50`, `text-yellow-700`, `border-yellow-200`

### Typography
- Page title: `text-2xl font-bold text-neutral-900`
- Section title: `text-lg font-semibold text-neutral-900`
- Body text: `text-base text-neutral-700`
- Small text: `text-sm text-neutral-600`

### Spacing
- Page padding: `p-6`
- Section gap: `space-y-6`
- Form field gap: `space-y-4`
- Inline gap: `gap-2` or `gap-4`

### Buttons
- Primary: `bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-md`
- Secondary: `bg-white hover:bg-neutral-50 text-neutral-700 border border-neutral-300 px-4 py-2 rounded-md`
- Danger: `bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-md`

---

## Success Criteria

Sprint 1.2 is complete when:
- [ ] UserTable displays users correctly with sorting and filtering
- [ ] UserForm validates and submits data correctly
- [ ] Admin page integrates all components
- [ ] Users can create new users via the form
- [ ] Users can edit existing users
- [ ] Users can delete users (soft delete)
- [ ] All components have >80% test coverage
- [ ] No TypeScript errors
- [ ] Responsive on mobile and desktop
- [ ] Follows existing design patterns

---

## Next Steps After Completion

After Sprint 1.2 is done, the backlog shows:
- **Sprint 2**: Docker & Deployment (Backend Dockerfile, docker-compose update)
- **Sprint 3**: Testing Improvements (Integration tests, E2E tests)
- **Sprint 4**: Agentic AI Phase 1 (Validation Agent)

---

## Notes

1. **Auth Integration**: Currently stubbed. When auth is implemented, add admin role check to the page.
2. **Pagination**: UserTable doesn't implement client-side pagination yet. Can be added if user list grows large.
3. **Search**: Not in current scope, but could be added as enhancement.
4. **Bulk Actions**: Not in current scope.
5. **Audit Log**: Not in current scope, but backend supports it via audit_events table.

---

## Dependencies

- **Backend**: Sprint 1.1 must be complete (admin API endpoints) ✅
- **Frontend Libraries**:
  - react-hook-form (should already be installed)
  - zod (should already be installed)
  - @headlessui/react (for modal, should be installed or use custom modal)
- **No new dependencies needed**
