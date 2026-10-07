import { apiClient } from './client';

export const foodsApi = {
  searchFoods: async (query, category = null, limit = 20, offset = 0) => {
    const params = { q: query, limit, offset };
    if (category) params.category = category;
    const response = await apiClient.get('/foods/search', { params });
    return response.data;
  },

  getFoodById: async (foodId) => {
    const response = await apiClient.get(`/foods/${foodId}`);
    return response.data;
  },
};
