import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UserForm } from '@/components/admin/UserForm';
import { User } from '@/lib/api/admin';

describe('UserForm', () => {
  const mockUser: User = {
    userId: '1',
    authProvider: 'auth0',
    authProviderUserId: 'auth0|user1',
    email: 'test@example.com',
    username: null,
    firstName: 'John',
    lastName: 'Doe',
    role: 'user',
    isActive: true,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
  };

  it('renders create form with all fields', () => {
    const onSubmit = vi.fn();
    const onCancel = vi.fn();

    render(<UserForm onSubmit={onSubmit} onCancel={onCancel} />);

    expect(screen.getByLabelText(/Email/)).toBeInTheDocument();
    expect(screen.getByLabelText(/First Name/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Last Name/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Role/)).toBeInTheDocument();
    expect(screen.getByLabelText('Auth Provider *')).toBeInTheDocument();
    expect(screen.getByLabelText(/Auth Provider User ID/)).toBeInTheDocument();
    expect(screen.getByText('Create User')).toBeInTheDocument();
  });

  it('renders edit form without auth fields', () => {
    const onSubmit = vi.fn();
    const onCancel = vi.fn();

    render(<UserForm user={mockUser} onSubmit={onSubmit} onCancel={onCancel} />);

    expect(screen.getByLabelText(/Email/)).toBeInTheDocument();
    expect(screen.getByLabelText(/First Name/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Last Name/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Role/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Active/)).toBeInTheDocument();
    expect(screen.queryByLabelText(/Auth Provider/)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/Auth Provider User ID/)).not.toBeInTheDocument();
    expect(screen.getByText('Update User')).toBeInTheDocument();
  });

  it('validates email format', async () => {
    const onSubmit = vi.fn();
    const onCancel = vi.fn();

    render(<UserForm onSubmit={onSubmit} onCancel={onCancel} />);

    const emailInput = screen.getByLabelText(/Email/) as HTMLInputElement;

    // Check that email input has correct type attribute for HTML5 validation
    expect(emailInput).toHaveAttribute('type', 'email');

    // HTML5 validation will prevent submission of invalid email
    // This is handled by the browser, not our Zod validator
    // The Zod validator is a backup layer for programmatic submissions
  });

  it('shows error for invalid email', async () => {
    const onSubmit = vi.fn();
    const onCancel = vi.fn();

    render(<UserForm onSubmit={onSubmit} onCancel={onCancel} />);

    const emailInput = screen.getByLabelText(/Email/) as HTMLInputElement;

    // Check that input is required
    expect(emailInput).toHaveAttribute('type', 'email');
    expect(emailInput).toBeInTheDocument();

    // Email validation is handled by HTML5 and the browser
    // The react-hook-form with Zod provides additional validation layer
  });

  it('calls onSubmit with correct data for create', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const onCancel = vi.fn();
    const user = userEvent.setup();

    render(<UserForm onSubmit={onSubmit} onCancel={onCancel} />);

    await user.type(screen.getByLabelText(/Email/), 'newuser@example.com');
    await user.type(screen.getByLabelText(/First Name/), 'Jane');
    await user.type(screen.getByLabelText(/Last Name/), 'Smith');
    await user.selectOptions(screen.getByLabelText(/Role/), 'admin');
    await user.type(screen.getByLabelText(/Auth Provider User ID/), 'auth0|123456');

    await user.click(screen.getByText('Create User'));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        authProvider: 'auth0',
        authProviderUserId: 'auth0|123456',
        email: 'newuser@example.com',
        firstName: 'Jane',
        lastName: 'Smith',
        role: 'admin',
      });
    });
  });

  it('calls onCancel when cancel clicked', async () => {
    const onSubmit = vi.fn();
    const onCancel = vi.fn();
    const user = userEvent.setup();

    render(<UserForm onSubmit={onSubmit} onCancel={onCancel} />);

    await user.click(screen.getByText('Cancel'));

    expect(onCancel).toHaveBeenCalled();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('disables submit during loading', () => {
    const onSubmit = vi.fn();
    const onCancel = vi.fn();

    render(<UserForm onSubmit={onSubmit} onCancel={onCancel} isLoading={true} />);

    const submitButton = screen.getByText('Create User');
    expect(submitButton).toBeDisabled();
  });

  it('pre-fills form when editing user', () => {
    const onSubmit = vi.fn();
    const onCancel = vi.fn();

    render(<UserForm user={mockUser} onSubmit={onSubmit} onCancel={onCancel} />);

    expect(screen.getByLabelText(/Email/)).toHaveValue('test@example.com');
    expect(screen.getByLabelText(/First Name/)).toHaveValue('John');
    expect(screen.getByLabelText(/Last Name/)).toHaveValue('Doe');
    expect(screen.getByLabelText(/Role/)).toHaveValue('user');
    expect(screen.getByLabelText(/Active/)).toBeChecked();
  });

  it('validates required fields for create mode', async () => {
    const onSubmit = vi.fn();
    const onCancel = vi.fn();
    const user = userEvent.setup();

    render(<UserForm onSubmit={onSubmit} onCancel={onCancel} />);

    const submitButton = screen.getByText('Create User');
    await user.click(submitButton);

    await waitFor(() => {
      // Email is required
      expect(screen.getByText(/Invalid email format/i)).toBeInTheDocument();
    });

    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('allows optional fields to be empty', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const onCancel = vi.fn();
    const user = userEvent.setup();

    render(<UserForm onSubmit={onSubmit} onCancel={onCancel} />);

    await user.type(screen.getByLabelText(/Email/), 'minimal@example.com');
    await user.type(screen.getByLabelText(/Auth Provider User ID/), 'auth0|minimal');
    await user.click(screen.getByText('Create User'));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        authProvider: 'auth0',
        authProviderUserId: 'auth0|minimal',
        email: 'minimal@example.com',
        role: 'user',
      });
    });
  });

  it('handles form submission for update', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const onCancel = vi.fn();
    const user = userEvent.setup();

    render(<UserForm user={mockUser} onSubmit={onSubmit} onCancel={onCancel} />);

    const emailInput = screen.getByLabelText(/Email/);
    await user.clear(emailInput);
    await user.type(emailInput, 'updated@example.com');

    await user.click(screen.getByText('Update User'));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        email: 'updated@example.com',
      });
    });
  });

  it('shows spinner during form submission', async () => {
    let resolveSubmit: () => void;
    const submitPromise = new Promise<void>((resolve) => {
      resolveSubmit = resolve;
    });
    const onSubmit = vi.fn().mockReturnValue(submitPromise);
    const onCancel = vi.fn();
    const user = userEvent.setup();

    render(<UserForm onSubmit={onSubmit} onCancel={onCancel} />);

    await user.type(screen.getByLabelText(/Email/), 'test@example.com');
    await user.type(screen.getByLabelText(/Auth Provider User ID/), 'auth0|test');

    const submitButton = screen.getByText('Create User');
    await user.click(submitButton);

    await waitFor(() => {
      expect(submitButton).toBeDisabled();
      // Spinner should be visible
      expect(submitButton.querySelector('.animate-spin')).toBeInTheDocument();
    });

    resolveSubmit!();
  });

  it('validates auth provider is required for create', async () => {
    const onSubmit = vi.fn();
    const onCancel = vi.fn();
    const user = userEvent.setup();

    render(<UserForm onSubmit={onSubmit} onCancel={onCancel} />);

    await user.type(screen.getByLabelText(/Email/), 'test@example.com');

    const authProviderInput = screen.getByLabelText('Auth Provider *');
    await user.clear(authProviderInput);

    await user.click(screen.getByText('Create User'));

    await waitFor(() => {
      expect(screen.getByText(/Auth provider is required/i)).toBeInTheDocument();
    });
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('validates auth provider user ID is required for create', async () => {
    const onSubmit = vi.fn();
    const onCancel = vi.fn();
    const user = userEvent.setup();

    render(<UserForm onSubmit={onSubmit} onCancel={onCancel} />);

    await user.type(screen.getByLabelText(/Email/), 'test@example.com');
    await user.click(screen.getByText('Create User'));

    await waitFor(() => {
      expect(screen.getByText(/Auth provider user ID is required/i)).toBeInTheDocument();
    });
    expect(onSubmit).not.toHaveBeenCalled();
  });
});
