import { apiClient } from './client';
import { Agent, AgentRegistration, AgentHeartbeat, PaginatedResponse } from '../../types';

export const agentService = {
  list: async (params?: any): Promise<PaginatedResponse<Agent>> => {
    return apiClient.get('/agents/manage/', { params });
  },

  get: async (id: string): Promise<Agent> => {
    return apiClient.get(`/agents/manage/${id}/`);
  },

  register: async (data: AgentRegistration): Promise<{ agent_id: string; token: string }> => {
    return apiClient.post('/agents/register/', data);
  },

  delete: async (id: string): Promise<void> => {
    return apiClient.delete(`/agents/manage/${id}/`);
  },

  getHeartbeats: async (agentId: string): Promise<AgentHeartbeat[]> => {
    return apiClient.get(`/agents/manage/${agentId}/heartbeats/`);
  },

  getOnlineCount: async (): Promise<{ online: number; total: number }> => {
    return apiClient.get('/agents/stats/');
  }
};