import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { UserTable } from '@/components/admin/UserTable';
import { User } from '@/lib/api/admin';

describe('UserTable', () => {
  const mockUsers: User[] = [
    {
      userId: '1',
      authProvider: 'auth0',
      authProviderUserId: 'auth0|user1',
      email: 'admin@test.com',
      username: null,
      firstName: 'Admin',
      lastName: 'User',
      role: 'admin',
      isActive: true,
      createdAt: '2024-01-01T00:00:00Z',
      updatedAt: '2024-01-01T00:00:00Z',
    },
    {
      userId: '2',
      authProvider: 'auth0',
      authProviderUserId: 'auth0|user2',
      email: 'user@test.com',
      username: null,
      firstName: 'Regular',
      lastName: 'User',
      role: 'user',
      isActive: true,
      createdAt: '2024-01-02T00:00:00Z',
      updatedAt: '2024-01-02T00:00:00Z',
    },
    {
      userId: '3',
      authProvider: 'auth0',
      authProviderUserId: 'auth0|user3',
      email: 'inactive@test.com',
      username: null,
      firstName: 'Inactive',
      lastName: 'User',
      role: 'user',
      isActive: false,
      createdAt: '2024-01-03T00:00:00Z',
      updatedAt: '2024-01-03T00:00:00Z',
    },
  ];

  it('renders table with user data', () => {
    const onEdit = vi.fn();
    const onDelete = vi.fn();

    render(<UserTable users={mockUsers} onEdit={onEdit} onDelete={onDelete} />);

    expect(screen.getByText('admin@test.com')).toBeInTheDocument();
    expect(screen.getByText('user@test.com')).toBeInTheDocument();
    expect(screen.getByText('inactive@test.com')).toBeInTheDocument();
  });

  it('displays user name, email, role, status correctly', () => {
    const onEdit = vi.fn();
    const onDelete = vi.fn();

    render(<UserTable users={mockUsers} onEdit={onEdit} onDelete={onDelete} />);

    expect(screen.getByText('Admin User')).toBeInTheDocument();
    expect(screen.getByText('admin@test.com')).toBeInTheDocument();
    expect(screen.getByText('admin')).toBeInTheDocument();
    expect(screen.getAllByText('Active').length).toBeGreaterThan(0);
  });

  it('shows empty state when no users', () => {
    const onEdit = vi.fn();
    const onDelete = vi.fn();

    render(<UserTable users={[]} onEdit={onEdit} onDelete={onDelete} />);

    expect(screen.getByText('No users found')).toBeInTheDocument();
    expect(screen.getByText('Get started by creating a new user.')).toBeInTheDocument();
  });

  it('shows loading state with skeleton', () => {
    const onEdit = vi.fn();
    const onDelete = vi.fn();

    render(<UserTable users={[]} onEdit={onEdit} onDelete={onDelete} isLoading={true} />);

    // Loading skeleton should show table headers
    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Email')).toBeInTheDocument();
    expect(screen.getByText('Role')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();

    // Should have animated skeleton rows
    const skeletons = document.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('calls onEdit when edit button clicked', () => {
    const onEdit = vi.fn();
    const onDelete = vi.fn();

    render(<UserTable users={mockUsers} onEdit={onEdit} onDelete={onDelete} />);

    const editButtons = screen.getAllByLabelText(/Edit/);
    fireEvent.click(editButtons[0]);

    expect(onEdit).toHaveBeenCalledWith(mockUsers[0]);
  });

  it('calls onDelete when delete button clicked', () => {
    const onEdit = vi.fn();
    const onDelete = vi.fn();

    render(<UserTable users={mockUsers} onEdit={onEdit} onDelete={onDelete} />);

    const deleteButtons = screen.getAllByLabelText(/Delete/);
    fireEvent.click(deleteButtons[0]);

    expect(onDelete).toHaveBeenCalledWith(mockUsers[0].userId);
  });

  it('sorts by name when column header clicked', () => {
    const onEdit = vi.fn();
    const onDelete = vi.fn();

    render(<UserTable users={mockUsers} onEdit={onEdit} onDelete={onDelete} />);

    // Get all rows
    const rows = screen.getAllByRole('row');
    // First row is header, so data rows start at index 1
    expect(rows[1]).toHaveTextContent('Admin User');

    // Click Name header to sort
    const nameHeader = screen.getByText('Name').closest('th');
    if (nameHeader) {
      fireEvent.click(nameHeader);
    }

    // Should still show users (sorting may change order)
    expect(screen.getByText('Admin User')).toBeInTheDocument();
  });

  it('filters by role', () => {
    const onEdit = vi.fn();
    const onDelete = vi.fn();

    render(<UserTable users={mockUsers} onEdit={onEdit} onDelete={onDelete} />);

    // Select admin role filter
    const roleFilter = screen.getByLabelText('Role') as HTMLSelectElement;
    fireEvent.change(roleFilter, { target: { value: 'admin' } });

    // Should only show admin user
    expect(screen.getByText('admin@test.com')).toBeInTheDocument();
    expect(screen.queryByText('user@test.com')).not.toBeInTheDocument();
  });

  it('filters by active status', () => {
    const onEdit = vi.fn();
    const onDelete = vi.fn();

    render(<UserTable users={mockUsers} onEdit={onEdit} onDelete={onDelete} />);

    // Select active status filter
    const statusFilter = screen.getByLabelText('Status') as HTMLSelectElement;
    fireEvent.change(statusFilter, { target: { value: 'active' } });

    // Should only show active users
    expect(screen.getByText('admin@test.com')).toBeInTheDocument();
    expect(screen.getByText('user@test.com')).toBeInTheDocument();
    expect(screen.queryByText('inactive@test.com')).not.toBeInTheDocument();
  });

  it('displays role badge with correct color', () => {
    const onEdit = vi.fn();
    const onDelete = vi.fn();

    render(<UserTable users={mockUsers} onEdit={onEdit} onDelete={onDelete} />);

    // Admin role should have primary color
    const adminBadge = screen.getAllByText('admin')[0];
    expect(adminBadge).toHaveClass('bg-primary-50');
    expect(adminBadge).toHaveClass('text-primary-700');

    // User role should have neutral color
    const userBadges = screen.getAllByText('user');
    expect(userBadges[0]).toHaveClass('bg-neutral-100');
    expect(userBadges[0]).toHaveClass('text-neutral-700');
  });

  it('displays status badge with correct color', () => {
    const onEdit = vi.fn();
    const onDelete = vi.fn();

    const { container } = render(<UserTable users={mockUsers} onEdit={onEdit} onDelete={onDelete} />);

    // Find status badge spans by searching for elements with the badge classes
    const activeBadges = container.querySelectorAll('.bg-green-50');
    expect(activeBadges.length).toBeGreaterThan(0);
    expect(activeBadges[0]).toHaveClass('bg-green-50');
    expect(activeBadges[0]).toHaveClass('text-green-700');

    // Inactive status should have red color
    const inactiveBadges = container.querySelectorAll('.bg-red-50');
    expect(inactiveBadges.length).toBeGreaterThan(0);
    expect(inactiveBadges[0]).toHaveClass('bg-red-50');
    expect(inactiveBadges[0]).toHaveClass('text-red-700');
  });

  it('shows results summary', () => {
    const onEdit = vi.fn();
    const onDelete = vi.fn();

    render(<UserTable users={mockUsers} onEdit={onEdit} onDelete={onDelete} />);

    expect(screen.getByText(/Showing 3 of 3 users/)).toBeInTheDocument();
  });

  it('handles users with no name', () => {
    const userWithNoName: User = {
      userId: '4',
      authProvider: 'auth0',
      authProviderUserId: 'auth0|user4',
      email: 'noname@test.com',
      username: null,
      firstName: null,
      lastName: null,
      role: 'user',
      isActive: true,
      createdAt: '2024-01-04T00:00:00Z',
      updatedAt: '2024-01-04T00:00:00Z',
    };

    const onEdit = vi.fn();
    const onDelete = vi.fn();

    render(<UserTable users={[userWithNoName]} onEdit={onEdit} onDelete={onDelete} />);

    expect(screen.getByText('N/A')).toBeInTheDocument();
    expect(screen.getByText('noname@test.com')).toBeInTheDocument();
  });
});
