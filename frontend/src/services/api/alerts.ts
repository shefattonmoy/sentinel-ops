// src/services/api/alerts.ts
import { apiClient } from './client';
import { Alert, AlertStatus, PaginatedResponse } from '../../types';

export const alertService = {
  list: (params?: any) =>
    apiClient.get<PaginatedResponse<Alert>>('/alerts/', { params }),

  get: (id: string) =>
    apiClient.get<Alert>(`/alerts/${id}/`),

  updateStatus: (id: string, status: AlertStatus, note?: string) =>
    apiClient.post(`/alerts/${id}/update_status/`, { status, note }),

  addComment: (id: string, comment: string) =>
    apiClient.post(`/alerts/${id}/add_comment/`, { comment }),

  getComments: (id: string) =>
    apiClient.get(`/alerts/${id}/comments/`),

  getHistory: (id: string) =>
    apiClient.get(`/alerts/${id}/history/`),

  getStats: () =>
    apiClient.get('/alerts/stats/'),

  getRecent: (limit?: number) =>
    apiClient.get('/alerts/recent/', { params: { limit } }),
};