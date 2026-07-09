// src/services/api/rules.ts
import { apiClient } from './client';
import { DetectionRule, PaginatedResponse } from '../../types';

export const ruleService = {
  list: (params?: any) =>
    apiClient.get<PaginatedResponse<DetectionRule>>('/rules/', { params }),

  get: (id: string) =>
    apiClient.get<DetectionRule>(`/rules/${id}/`),

  create: (data: Partial<DetectionRule>) =>
    apiClient.post<DetectionRule>('/rules/', data),

  update: (id: string, data: Partial<DetectionRule>) =>
    apiClient.put<DetectionRule>(`/rules/${id}/`, data),

  delete: (id: string) =>
    apiClient.delete(`/rules/${id}/`),

  test: (id: string) =>
    apiClient.post(`/rules/${id}/test/`),

  execute: (id: string) =>
    apiClient.post(`/rules/${id}/execute/`),

  executeAll: () =>
    apiClient.post('/rules/execute_all/'),

  getStats: () =>
    apiClient.get('/rules/stats/'),
};