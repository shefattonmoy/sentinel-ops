// src/services/api/events.ts
import { apiClient } from './client';
import { Event, PaginatedResponse } from '../../types';

export const eventService = {
  list: (params?: any) =>
    apiClient.get<PaginatedResponse<Event>>('/events/', { params }),

  get: (id: string) =>
    apiClient.get<Event>(`/events/${id}/`),

  getStats: (params?: any) =>
    apiClient.get('/events/stats/', { params }),

  getTopIps: (params?: any) =>
    apiClient.get('/events/top_ips/', { params }),

  getTimeline: (params?: any) =>
    apiClient.get('/events/timeline/', { params }),
};