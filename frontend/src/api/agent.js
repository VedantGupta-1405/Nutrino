import { apiClient } from './client';

export const agentApi = {
  chatWithAgent: async (message) => {
    const response = await apiClient.post('/agent/chat', { message });
    return response.data;
  },
};
