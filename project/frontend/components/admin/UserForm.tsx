'use client';

import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { User, CreateUserRequest, UpdateUserRequest } from '@/lib/api/admin';

const createUserSchema = z.object({
  email: z.string().email('Invalid email format'),
  firstName: z.string().optional(),
  lastName: z.string().optional(),
  role: z.enum(['admin', 'user']),
  authProvider: z.string().min(1, 'Auth provider is required'),
  authProviderUserId: z.string().min(1, 'Auth provider user ID is required'),
});

const updateUserSchema = z.object({
  email: z.string().email('Invalid email format').optional().or(z.literal('')),
  firstName: z.string().optional().or(z.literal('')),
  lastName: z.string().optional().or(z.literal('')),
  role: z.enum(['admin', 'user']).optional(),
  isActive: z.boolean().optional(),
});

type CreateUserFormData = z.infer<typeof createUserSchema>;
type UpdateUserFormData = z.infer<typeof updateUserSchema>;

export interface UserFormProps {
  user?: User;
  onSubmit: (data: CreateUserRequest | UpdateUserRequest) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

export const UserForm: React.FC<UserFormProps> = ({
  user,
  onSubmit,
  onCancel,
  isLoading = false,
}) => {
  const isEditMode = !!user;

  if (isEditMode) {
    return <EditUserForm user={user} onSubmit={onSubmit} onCancel={onCancel} isLoading={isLoading} />;
  }

  return <CreateUserForm onSubmit={onSubmit} onCancel={onCancel} isLoading={isLoading} />;
};

const CreateUserForm: React.FC<Omit<UserFormProps, 'user'>> = ({
  onSubmit,
  onCancel,
  isLoading = false,
}) => {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CreateUserFormData>({
    resolver: zodResolver(createUserSchema),
    defaultValues: {
      email: '',
      firstName: '',
      lastName: '',
      role: 'user',
      authProvider: 'auth0',
      authProviderUserId: '',
    },
  });

  const handleFormSubmit = async (data: CreateUserFormData) => {
    try {
      const payload: CreateUserRequest = {
        authProvider: data.authProvider,
        authProviderUserId: data.authProviderUserId,
        email: data.email,
        firstName: data.firstName || undefined,
        lastName: data.lastName || undefined,
        role: data.role,
      };
      await onSubmit(payload);
    } catch (error) {
      console.error('Form submission error:', error);
    }
  };

  const isFormDisabled = isLoading || isSubmitting;

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
      {/* Email */}
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-neutral-700 mb-1">
          Email <span className="text-red-500">*</span>
        </label>
        <input
          {...register('email')}
          id="email"
          type="email"
          disabled={isFormDisabled}
          className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-neutral-100 disabled:cursor-not-allowed ${
            errors.email ? 'border-red-500' : 'border-neutral-300'
          }`}
          placeholder="user@example.com"
        />
        {errors.email && (
          <p className="text-sm text-red-600 mt-1">{errors.email.message}</p>
        )}
      </div>

      {/* First Name */}
      <div>
        <label htmlFor="firstName" className="block text-sm font-medium text-neutral-700 mb-1">
          First Name
        </label>
        <input
          {...register('firstName')}
          id="firstName"
          type="text"
          disabled={isFormDisabled}
          className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-neutral-100 disabled:cursor-not-allowed"
          placeholder="John"
        />
        {errors.firstName && (
          <p className="text-sm text-red-600 mt-1">{errors.firstName.message}</p>
        )}
      </div>

      {/* Last Name */}
      <div>
        <label htmlFor="lastName" className="block text-sm font-medium text-neutral-700 mb-1">
          Last Name
        </label>
        <input
          {...register('lastName')}
          id="lastName"
          type="text"
          disabled={isFormDisabled}
          className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-neutral-100 disabled:cursor-not-allowed"
          placeholder="Doe"
        />
        {errors.lastName && (
          <p className="text-sm text-red-600 mt-1">{errors.lastName.message}</p>
        )}
      </div>

      {/* Role */}
      <div>
        <label htmlFor="role" className="block text-sm font-medium text-neutral-700 mb-1">
          Role <span className="text-red-500">*</span>
        </label>
        <select
          {...register('role')}
          id="role"
          disabled={isFormDisabled}
          className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-neutral-100 disabled:cursor-not-allowed"
        >
          <option value="user">User</option>
          <option value="admin">Admin</option>
        </select>
        {errors.role && (
          <p className="text-sm text-red-600 mt-1">{errors.role.message}</p>
        )}
      </div>

      {/* Auth Provider */}
      <div>
        <label htmlFor="authProvider" className="block text-sm font-medium text-neutral-700 mb-1">
          Auth Provider <span className="text-red-500">*</span>
        </label>
        <input
          {...register('authProvider')}
          id="authProvider"
          type="text"
          disabled={isFormDisabled}
          className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-neutral-100 disabled:cursor-not-allowed ${
            errors.authProvider ? 'border-red-500' : 'border-neutral-300'
          }`}
          placeholder="auth0"
        />
        {errors.authProvider && (
          <p className="text-sm text-red-600 mt-1">{errors.authProvider.message}</p>
        )}
      </div>

      {/* Auth Provider User ID */}
      <div>
        <label htmlFor="authProviderUserId" className="block text-sm font-medium text-neutral-700 mb-1">
          Auth Provider User ID <span className="text-red-500">*</span>
        </label>
        <input
          {...register('authProviderUserId')}
          id="authProviderUserId"
          type="text"
          disabled={isFormDisabled}
          className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-neutral-100 disabled:cursor-not-allowed ${
            errors.authProviderUserId ? 'border-red-500' : 'border-neutral-300'
          }`}
          placeholder="auth0|123456789"
        />
        {errors.authProviderUserId && (
          <p className="text-sm text-red-600 mt-1">{errors.authProviderUserId.message}</p>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end gap-3 pt-4">
        <button
          type="button"
          onClick={onCancel}
          disabled={isFormDisabled}
          className="bg-white hover:bg-neutral-50 text-neutral-700 border border-neutral-300 px-4 py-2 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isFormDisabled}
          className="bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-md disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isFormDisabled && (
            <svg
              className="animate-spin h-4 w-4 text-white"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              ></circle>
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
          )}
          Create User
        </button>
      </div>
    </form>
  );
};

const EditUserForm: React.FC<Required<Pick<UserFormProps, 'user'>> & Omit<UserFormProps, 'user'>> = ({
  user,
  onSubmit,
  onCancel,
  isLoading = false,
}) => {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<UpdateUserFormData>({
    resolver: zodResolver(updateUserSchema),
    defaultValues: {
      email: user.email,
      firstName: user.firstName || '',
      lastName: user.lastName || '',
      role: user.role,
      isActive: user.isActive,
    },
  });

  const handleFormSubmit = async (data: UpdateUserFormData) => {
    try {
      const payload: UpdateUserRequest = {};

      if (data.email && data.email !== user.email) {
        payload.email = data.email;
      }
      if (data.firstName !== undefined && data.firstName !== user.firstName) {
        payload.firstName = data.firstName || undefined;
      }
      if (data.lastName !== undefined && data.lastName !== user.lastName) {
        payload.lastName = data.lastName || undefined;
      }
      if (data.role && data.role !== user.role) {
        payload.role = data.role;
      }
      if (data.isActive !== undefined && data.isActive !== user.isActive) {
        payload.isActive = data.isActive;
      }

      await onSubmit(payload);
    } catch (error) {
      console.error('Form submission error:', error);
    }
  };

  const isFormDisabled = isLoading || isSubmitting;

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
      {/* Email */}
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-neutral-700 mb-1">
          Email
        </label>
        <input
          {...register('email')}
          id="email"
          type="email"
          disabled={isFormDisabled}
          className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-neutral-100 disabled:cursor-not-allowed ${
            errors.email ? 'border-red-500' : 'border-neutral-300'
          }`}
          placeholder="user@example.com"
        />
        {errors.email && (
          <p className="text-sm text-red-600 mt-1">{errors.email.message}</p>
        )}
      </div>

      {/* First Name */}
      <div>
        <label htmlFor="firstName" className="block text-sm font-medium text-neutral-700 mb-1">
          First Name
        </label>
        <input
          {...register('firstName')}
          id="firstName"
          type="text"
          disabled={isFormDisabled}
          className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-neutral-100 disabled:cursor-not-allowed"
          placeholder="John"
        />
        {errors.firstName && (
          <p className="text-sm text-red-600 mt-1">{errors.firstName.message}</p>
        )}
      </div>

      {/* Last Name */}
      <div>
        <label htmlFor="lastName" className="block text-sm font-medium text-neutral-700 mb-1">
          Last Name
        </label>
        <input
          {...register('lastName')}
          id="lastName"
          type="text"
          disabled={isFormDisabled}
          className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-neutral-100 disabled:cursor-not-allowed"
          placeholder="Doe"
        />
        {errors.lastName && (
          <p className="text-sm text-red-600 mt-1">{errors.lastName.message}</p>
        )}
      </div>

      {/* Role */}
      <div>
        <label htmlFor="role" className="block text-sm font-medium text-neutral-700 mb-1">
          Role
        </label>
        <select
          {...register('role')}
          id="role"
          disabled={isFormDisabled}
          className="w-full px-3 py-2 border border-neutral-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:bg-neutral-100 disabled:cursor-not-allowed"
        >
          <option value="user">User</option>
          <option value="admin">Admin</option>
        </select>
        {errors.role && (
          <p className="text-sm text-red-600 mt-1">{errors.role.message}</p>
        )}
      </div>

      {/* Active Status */}
      <div>
        <label htmlFor="isActive" className="flex items-center gap-2">
          <input
            {...register('isActive')}
            id="isActive"
            type="checkbox"
            disabled={isFormDisabled}
            className="w-4 h-4 text-primary-600 border-neutral-300 rounded focus:ring-primary-500 disabled:cursor-not-allowed"
          />
          <span className="text-sm font-medium text-neutral-700">Active</span>
        </label>
        {errors.isActive && (
          <p className="text-sm text-red-600 mt-1">{errors.isActive.message}</p>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end gap-3 pt-4">
        <button
          type="button"
          onClick={onCancel}
          disabled={isFormDisabled}
          className="bg-white hover:bg-neutral-50 text-neutral-700 border border-neutral-300 px-4 py-2 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isFormDisabled}
          className="bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-md disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {isFormDisabled && (
            <svg
              className="animate-spin h-4 w-4 text-white"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              ></circle>
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
          )}
          Update User
        </button>
      </div>
    </form>
  );
};
