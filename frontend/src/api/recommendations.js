import { apiClient } from './client';

export const recommendationsApi = {
  getMealRecommendation: async (params = {}) => {
    const response = await apiClient.post('/recommendations', params);
    return response.data;
  },
};
