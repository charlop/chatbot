import { describe, it, expect, vi, beforeEach } from 'vitest';
import { adminApi } from '@/lib/api/admin';
import { apiClient } from '@/lib/api/client';

vi.mock('@/lib/api/client');

describe('adminApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getUsers', () => {
    it('calls correct endpoint with no params', async () => {
      const mockResponse = {
        data: {
          users: [],
          total: 0,
          offset: 0,
          limit: 100,
        },
      };
      vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

      await adminApi.getUsers();

      expect(apiClient.get).toHaveBeenCalledWith('/admin/users', { params: undefined });
    });

    it('calls correct endpoint with limit param', async () => {
      const mockResponse = {
        data: {
          users: [],
          total: 0,
          offset: 0,
          limit: 10,
        },
      };
      vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

      await adminApi.getUsers({ limit: 10 });

      expect(apiClient.get).toHaveBeenCalledWith('/admin/users', {
        params: { limit: 10 },
      });
    });

    it('calls correct endpoint with all params', async () => {
      const mockResponse = {
        data: {
          users: [],
          total: 0,
          offset: 5,
          limit: 20,
        },
      };
      vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

      await adminApi.getUsers({
        offset: 5,
        limit: 20,
        role: 'admin',
        activeOnly: true,
      });

      expect(apiClient.get).toHaveBeenCalledWith('/admin/users', {
        params: {
          offset: 5,
          limit: 20,
          role: 'admin',
          activeOnly: true,
        },
      });
    });

    it('returns user list response', async () => {
      const mockUsers = [
        {
          userId: '1',
          authProvider: 'auth0',
          authProviderUserId: 'auth0|user1',
          email: 'test@example.com',
          username: null,
          firstName: 'Test',
          lastName: 'User',
          role: 'user',
          isActive: true,
          createdAt: '2024-01-01T00:00:00Z',
          updatedAt: '2024-01-01T00:00:00Z',
        },
      ];
      const mockResponse = {
        data: {
          users: mockUsers,
          total: 1,
          offset: 0,
          limit: 100,
        },
      };
      vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

      const result = await adminApi.getUsers();

      expect(result).toEqual(mockResponse.data);
      expect(result.users).toHaveLength(1);
      expect(result.total).toBe(1);
    });
  });

  describe('getUser', () => {
    it('calls correct endpoint with userId', async () => {
      const mockUser = {
        userId: '123',
        authProvider: 'auth0',
        authProviderUserId: 'auth0|user1',
        email: 'test@example.com',
        username: null,
        firstName: 'Test',
        lastName: 'User',
        role: 'user',
        isActive: true,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z',
      };
      const mockResponse = { data: mockUser };
      vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

      await adminApi.getUser('123');

      expect(apiClient.get).toHaveBeenCalledWith('/admin/users/123');
    });

    it('returns single user', async () => {
      const mockUser = {
        userId: '123',
        authProvider: 'auth0',
        authProviderUserId: 'auth0|user1',
        email: 'test@example.com',
        username: null,
        firstName: 'Test',
        lastName: 'User',
        role: 'user',
        isActive: true,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z',
      };
      const mockResponse = { data: mockUser };
      vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

      const result = await adminApi.getUser('123');

      expect(result).toEqual(mockUser);
      expect(result.userId).toBe('123');
    });
  });

  describe('createUser', () => {
    it('posts to correct endpoint with user data', async () => {
      const userData = {
        authProvider: 'auth0',
        authProviderUserId: 'auth0|newuser',
        email: 'new@example.com',
        firstName: 'New',
        lastName: 'User',
        role: 'user' as const,
      };
      const mockCreatedUser = {
        userId: 'new-id',
        ...userData,
        username: null,
        isActive: true,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z',
      };
      const mockResponse = { data: mockCreatedUser };
      vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

      await adminApi.createUser(userData);

      expect(apiClient.post).toHaveBeenCalledWith('/admin/users', userData);
    });

    it('returns created user', async () => {
      const userData = {
        authProvider: 'auth0',
        authProviderUserId: 'auth0|newuser',
        email: 'new@example.com',
        role: 'admin' as const,
      };
      const mockCreatedUser = {
        userId: 'new-id',
        ...userData,
        username: null,
        firstName: null,
        lastName: null,
        isActive: true,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-01T00:00:00Z',
      };
      const mockResponse = { data: mockCreatedUser };
      vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

      const result = await adminApi.createUser(userData);

      expect(result).toEqual(mockCreatedUser);
      expect(result.userId).toBe('new-id');
      expect(result.email).toBe('new@example.com');
    });
  });

  describe('updateUser', () => {
    it('puts to correct endpoint with user data', async () => {
      const updateData = {
        email: 'updated@example.com',
        firstName: 'Updated',
        role: 'admin' as const,
      };
      const mockUpdatedUser = {
        userId: '123',
        authProvider: 'auth0',
        authProviderUserId: 'auth0|user1',
        email: 'updated@example.com',
        username: null,
        firstName: 'Updated',
        lastName: 'User',
        role: 'admin' as const,
        isActive: true,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-02T00:00:00Z',
      };
      const mockResponse = { data: mockUpdatedUser };
      vi.mocked(apiClient.put).mockResolvedValue(mockResponse);

      await adminApi.updateUser('123', updateData);

      expect(apiClient.put).toHaveBeenCalledWith('/admin/users/123', updateData);
    });

    it('returns updated user', async () => {
      const updateData = {
        isActive: false,
      };
      const mockUpdatedUser = {
        userId: '123',
        authProvider: 'auth0',
        authProviderUserId: 'auth0|user1',
        email: 'test@example.com',
        username: null,
        firstName: 'Test',
        lastName: 'User',
        role: 'user' as const,
        isActive: false,
        createdAt: '2024-01-01T00:00:00Z',
        updatedAt: '2024-01-02T00:00:00Z',
      };
      const mockResponse = { data: mockUpdatedUser };
      vi.mocked(apiClient.put).mockResolvedValue(mockResponse);

      const result = await adminApi.updateUser('123', updateData);

      expect(result).toEqual(mockUpdatedUser);
      expect(result.isActive).toBe(false);
    });
  });

  describe('deleteUser', () => {
    it('deletes correct endpoint', async () => {
      vi.mocked(apiClient.delete).mockResolvedValue({ data: undefined });

      await adminApi.deleteUser('123');

      expect(apiClient.delete).toHaveBeenCalledWith('/admin/users/123');
    });

    it('does not return data', async () => {
      vi.mocked(apiClient.delete).mockResolvedValue({ data: undefined });

      const result = await adminApi.deleteUser('123');

      expect(result).toBeUndefined();
    });
  });

  describe('error handling', () => {
    it('handles API errors correctly', async () => {
      const mockError = new Error('API Error');
      vi.mocked(apiClient.get).mockRejectedValue(mockError);

      await expect(adminApi.getUsers()).rejects.toThrow('API Error');
    });

    it('handles network errors', async () => {
      const mockError = new Error('Network Error');
      vi.mocked(apiClient.post).mockRejectedValue(mockError);

      await expect(
        adminApi.createUser({
          authProvider: 'auth0',
          authProviderUserId: 'auth0|test',
          email: 'test@example.com',
          role: 'user',
        })
      ).rejects.toThrow('Network Error');
    });
  });
});
