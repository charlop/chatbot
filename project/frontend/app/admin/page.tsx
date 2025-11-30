'use client';

import { useState, useEffect } from 'react';
import { Layout } from '@/components/layout/Layout';
import { UserTable } from '@/components/admin/UserTable';
import { UserForm } from '@/components/admin/UserForm';
import { Modal } from '@/components/ui/Modal';
import { useToast } from '@/components/ui/Toast';
import { adminApi, User, CreateUserRequest, UpdateUserRequest } from '@/lib/api/admin';

export default function AdminPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | undefined>();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const toast = useToast();

  // Load users on mount
  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setIsLoading(true);
      const response = await adminApi.getUsers();
      setUsers(response.users);
    } catch (error) {
      console.error('Failed to load users:', error);
      toast.error('Failed to load users. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateClick = () => {
    setEditingUser(undefined);
    setIsModalOpen(true);
  };

  const handleEditClick = (user: User) => {
    setEditingUser(user);
    setIsModalOpen(true);
  };

  const handleDeleteClick = async (userId: string) => {
    const user = users.find((u) => u.userId === userId);
    if (!user) return;

    const userName = `${user.firstName || ''} ${user.lastName || ''}`.trim() || user.email;

    // Confirm deletion
    if (!confirm(`Are you sure you want to delete user "${userName}"? This will deactivate their account.`)) {
      return;
    }

    try {
      await adminApi.deleteUser(userId);
      toast.success(`User "${userName}" has been deactivated successfully.`);
      await loadUsers();
    } catch (error) {
      console.error('Failed to delete user:', error);
      toast.error('Failed to delete user. Please try again.');
    }
  };

  const handleFormSubmit = async (data: CreateUserRequest | UpdateUserRequest) => {
    try {
      setIsSubmitting(true);

      if (editingUser) {
        // Update existing user
        await adminApi.updateUser(editingUser.userId, data as UpdateUserRequest);
        toast.success('User updated successfully.');
      } else {
        // Create new user
        await adminApi.createUser(data as CreateUserRequest);
        toast.success('User created successfully.');
      }

      setIsModalOpen(false);
      setEditingUser(undefined);
      await loadUsers();
    } catch (error: any) {
      console.error('Failed to save user:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to save user. Please try again.';
      toast.error(errorMessage);
      throw error;
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleModalClose = () => {
    if (!isSubmitting) {
      setIsModalOpen(false);
      setEditingUser(undefined);
    }
  };

  return (
    <Layout title="User Management">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100 mb-2">
                User Management
              </h2>
              <p className="text-neutral-600 dark:text-neutral-400">
                Manage user accounts, roles, and permissions
              </p>
            </div>
            <button
              onClick={handleCreateClick}
              className="bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-md flex items-center gap-2"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4v16m8-8H4"
                />
              </svg>
              Create User
            </button>
          </div>
        </div>

        {/* User Table */}
        <UserTable
          users={users}
          onEdit={handleEditClick}
          onDelete={handleDeleteClick}
          isLoading={isLoading}
        />

        {/* Modal for Create/Edit User */}
        <Modal
          open={isModalOpen}
          onClose={handleModalClose}
          title={editingUser ? 'Edit User' : 'Create User'}
          size="md"
        >
          <UserForm
            user={editingUser}
            onSubmit={handleFormSubmit}
            onCancel={handleModalClose}
            isLoading={isSubmitting}
          />
        </Modal>
      </div>
    </Layout>
  );
}
