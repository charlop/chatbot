import { apiClient } from './client';

/**
 * Type definitions for User Management API
 */
export interface User {
  userId: string;
  authProvider: string;
  authProviderUserId: string;
  email: string;
  username?: string | null;
  firstName?: string | null;
  lastName?: string | null;
  role: 'admin' | 'user';
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface UserListResponse {
  users: User[];
  total: number;
  offset: number;
  limit: number;
}

export interface CreateUserRequest {
  authProvider: string;
  authProviderUserId: string;
  email: string;
  firstName?: string;
  lastName?: string;
  role?: 'admin' | 'user';
}

export interface UpdateUserRequest {
  email?: string;
  firstName?: string;
  lastName?: string;
  role?: 'admin' | 'user';
  isActive?: boolean;
}

/**
 * Admin API client for user management operations
 */
export const adminApi = {
  /**
   * Get all users with optional filters
   */
  async getUsers(params?: {
    offset?: number;
    limit?: number;
    role?: 'admin' | 'user';
    activeOnly?: boolean;
  }): Promise<UserListResponse> {
    const response = await apiClient.get<UserListResponse>('/admin/users', { params });
    return response.data;
  },

  /**
   * Get a single user by ID
   */
  async getUser(userId: string): Promise<User> {
    const response = await apiClient.get<User>(`/admin/users/${userId}`);
    return response.data;
  },

  /**
   * Create a new user
   */
  async createUser(userData: CreateUserRequest): Promise<User> {
    const response = await apiClient.post<User>('/admin/users', userData);
    return response.data;
  },

  /**
   * Update an existing user
   */
  async updateUser(userId: string, userData: UpdateUserRequest): Promise<User> {
    const response = await apiClient.put<User>(`/admin/users/${userId}`, userData);
    return response.data;
  },

  /**
   * Soft delete a user (sets isActive to false)
   */
  async deleteUser(userId: string): Promise<void> {
    await apiClient.delete(`/admin/users/${userId}`);
  },
};
