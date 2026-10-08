import { apiClient } from './client';

export const authApi = {
  getSession: async () => {
    const response = await apiClient.post('/auth/session');
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },
};
