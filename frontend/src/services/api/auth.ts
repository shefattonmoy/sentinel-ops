// src/services/api/auth.ts
import { apiClient } from './client';
import { LoginCredentials, AuthResponse, User } from '../../types';

export const authService = {
  login: (credentials: LoginCredentials) =>
    apiClient.post<AuthResponse>('/auth/login/', credentials),

  register: (data: any) =>
    apiClient.post('/auth/register/', data),

  getProfile: () =>
    apiClient.get<User>('/auth/profile/'),

  changePassword: (data: any) =>
    apiClient.post('/auth/change-password/', data),

  refreshToken: (refresh: string) =>
    apiClient.post<{ access: string }>('/auth/token/refresh/', { refresh }),
};