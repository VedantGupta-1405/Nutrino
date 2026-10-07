import { apiClient } from './client';

export const nutritionApi = {
  getTodayNutrition: async () => {
    const response = await apiClient.get('/nutrition/today');
    return response.data;
  },

  getNutritionByDate: async (dateStr) => {
    const response = await apiClient.get('/nutrition', {
      params: { date: dateStr },
    });
    return response.data;
  },

  getNutritionHistory: async (startDate, endDate) => {
    const response = await apiClient.get('/nutrition/history', {
      params: {
        start_date: startDate,
        end_date: endDate,
      },
    });
    return response.data;
  },
};
