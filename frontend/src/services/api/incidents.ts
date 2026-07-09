// src/services/api/incidents.ts
import { apiClient } from './client';
import { Incident, IncidentStatus, PaginatedResponse } from '../../types';

export const incidentService = {
  list: (params?: any) =>
    apiClient.get<PaginatedResponse<Incident>>('/incidents/', { params }),

  get: (id: string) =>
    apiClient.get<Incident>(`/incidents/${id}/`),

  create: (data: Partial<Incident>) =>
    apiClient.post<Incident>('/incidents/', data),

  updateStatus: (id: string, status: IncidentStatus, note?: string) =>
    apiClient.post(`/incidents/${id}/update_status/`, { status, note }),

  addNote: (id: string, content: string, noteType?: string) =>
    apiClient.post(`/incidents/${id}/add_note/`, { content, note_type: noteType }),

  getTimeline: (id: string) =>
    apiClient.get(`/incidents/${id}/timeline/`),

  getNotes: (id: string) =>
    apiClient.get(`/incidents/${id}/notes/`),

  correlate: (data?: any) =>
    apiClient.post('/incidents/correlate/', data || {}),

  getStats: () =>
    apiClient.get('/incidents/stats/'),

  getDashboard: () =>
    apiClient.get('/incidents/dashboard/'),
};