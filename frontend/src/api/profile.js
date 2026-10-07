import { apiClient } from './client';

export const profileApi = {
  getProfile: async () => {
    const response = await apiClient.get('/profile');
    return response.data;
  },

  updateProfile: async (profileData) => {
    const response = await apiClient.put('/profile', profileData);
    return response.data;
  },
};
