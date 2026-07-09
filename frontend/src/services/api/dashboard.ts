// src/services/api/dashboard.ts
import { apiClient } from './client';
import { DashboardStats, ChartDataPoint, SeverityDistribution } from '../../types';

export const dashboardService = {
  getOverview: () =>
    apiClient.get<DashboardStats>('/dashboard/overview/'),

  getEventsChart: (hours?: number) =>
    apiClient.get<ChartDataPoint[]>('/dashboard/events-chart/', { params: { hours } }),

  getAlertStats: () =>
    apiClient.get<{ severity_distribution: SeverityDistribution[]; top_alert_types: any[] }>('/dashboard/alert-stats/'),

  getTopIps: (hours?: number, limit?: number) =>
    apiClient.get('/dashboard/top-ips/', { params: { hours, limit } }),

  getTopServers: () =>
    apiClient.get('/dashboard/top-servers/'),

  getFailedLogins: (hours?: number) =>
    apiClient.get('/dashboard/failed-logins/', { params: { hours } }),

  getAgentHealth: () =>
    apiClient.get('/dashboard/agent-health/'),
};