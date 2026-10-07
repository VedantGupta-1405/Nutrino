import { apiClient } from './client';

export const mealsApi = {
  listMeals: async (limit = 50, offset = 0) => {
    const response = await apiClient.get('/meals', {
      params: { limit, offset },
    });
    return response.data;
  },

  getTodayMeals: async () => {
    const response = await apiClient.get('/meals/today');
    return response.data;
  },

  getMealById: async (mealId) => {
    const response = await apiClient.get(`/meals/${mealId}`);
    return response.data;
  },

  createMeal: async (mealData) => {
    const response = await apiClient.post('/meals', mealData);
    return response.data;
  },

  deleteMeal: async (mealId) => {
    await apiClient.delete(`/meals/${mealId}`);
    return true;
  },
};
