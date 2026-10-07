import { apiClient } from './client';

export const goalsApi = {
  getGoal: async () => {
    const response = await apiClient.get('/goals');
    return response.data;
  },

  updateGoal: async (goalData) => {
    const response = await apiClient.put('/goals', goalData);
    return response.data;
  },
};
