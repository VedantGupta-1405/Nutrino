import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { ProfilePage } from '../pages/ProfilePage';
import { GoalsPage } from '../pages/GoalsPage';
import { renderWithProviders } from './test-utils';
import { profileApi } from '../api/profile';
import { goalsApi } from '../api/goals';
import { nutritionApi } from '../api/nutrition';

vi.mock('../api/profile', () => ({
  profileApi: {
    getProfile: vi.fn(),
    updateProfile: vi.fn(),
  },
}));

vi.mock('../api/goals', () => ({
  goalsApi: {
    getGoal: vi.fn(),
    updateGoal: vi.fn(),
  },
}));

vi.mock('../api/nutrition', () => ({
  nutritionApi: {
    getTodayNutrition: vi.fn(),
  },
}));

describe('Profile & Goals Pages', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders and updates profile fields', async () => {
    profileApi.getProfile.mockResolvedValueOnce({
      age: 29,
      height: 178,
      weight: 72,
      activity_level: 'MODERATELY_ACTIVE',
      dietary_preference: 'VEGETARIAN',
      preferred_cuisine: ['Indian', 'Mediterranean'],
      allergies_or_restrictions: ['peanuts'],
      disliked_foods: ['mushrooms'],
      budget_per_day: 350,
      available_ingredients: ['rice', 'dal'],
    });

    profileApi.updateProfile.mockResolvedValueOnce({
      age: 30,
      height: 178,
      weight: 72,
      activity_level: 'MODERATELY_ACTIVE',
      dietary_preference: 'VEGETARIAN',
      preferred_cuisine: ['Indian'],
      allergies_or_restrictions: ['peanuts'],
      disliked_foods: [],
      budget_per_day: 400,
      available_ingredients: ['rice'],
    });

    renderWithProviders(<ProfilePage />, { route: '/profile' });

    expect(await screen.findByDisplayValue('29')).toBeInTheDocument();
    expect(screen.getByDisplayValue('178')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/Age \(Years\)/i), { target: { value: '30' } });
    const saveBtn = screen.getByRole('button', { name: /save profile settings/i });
    fireEvent.submit(saveBtn.closest('form'));

    await waitFor(() => {
      expect(profileApi.updateProfile).toHaveBeenCalled();
    });
  });

  it('renders and updates goals form', async () => {
    goalsApi.getGoal.mockResolvedValueOnce({
      goal_type: 'WEIGHT_MANAGEMENT',
      target_calories: 2100,
      target_protein: 120,
      target_carbohydrates: 250,
      target_fat: 65,
      is_active: true,
      notes: 'Initial test goal',
    });
    nutritionApi.getTodayNutrition.mockResolvedValueOnce({
      consumed: { calories: 1500, protein: 80, carbohydrates: 180, fat: 45 },
      target: { calories: 2100, protein: 120, carbohydrates: 250, fat: 65 },
    });
    goalsApi.updateGoal.mockResolvedValueOnce(true);

    renderWithProviders(<GoalsPage />, { route: '/goals' });

    expect(await screen.findByDisplayValue('2100')).toBeInTheDocument();
    expect(screen.getByDisplayValue('120')).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/Target Calories/i), { target: { value: '2200' } });
    const goalBtn = screen.getByRole('button', { name: /save active goal/i });
    fireEvent.submit(goalBtn.closest('form'));

    await waitFor(() => {
      expect(goalsApi.updateGoal).toHaveBeenCalled();
    });
  });
});
