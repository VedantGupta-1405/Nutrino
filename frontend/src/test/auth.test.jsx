import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { AppRoutes } from '../routes/AppRoutes';
import { renderWithProviders } from './test-utils';
import { authApi } from '../api/auth';
import { nutritionApi } from '../api/nutrition';
import { mealsApi } from '../api/meals';
import { recommendationsApi } from '../api/recommendations';

vi.mock('../api/auth', () => ({
  authApi: {
    getSession: vi.fn(),
    getCurrentUser: vi.fn(),
  },
}));

vi.mock('../api/nutrition', () => ({
  nutritionApi: {
    getTodayNutrition: vi.fn().mockResolvedValue({
      date: '2026-10-08',
      consumed: { calories: 1500, protein: 90, carbohydrates: 160, fat: 50 },
      target: { calories: 2000, protein: 120, carbohydrates: 200, fat: 65 },
      remaining: { calories: 500, protein: 30, carbohydrates: 40, fat: 15 },
      meals_count: 2,
    }),
    getNutritionHistory: vi.fn().mockResolvedValue({ days: [] }),
  },
}));

vi.mock('../api/meals', () => ({
  mealsApi: {
    getTodayMeals: vi.fn().mockResolvedValue([]),
    listMeals: vi.fn().mockResolvedValue([]),
  },
}));

vi.mock('../api/recommendations', () => ({
  recommendationsApi: {
    getMealRecommendation: vi.fn().mockResolvedValue({
      recommendation: {
        meal_name: 'Grilled Tofu Bowl',
        foods: [{ name: 'Tofu', quantity: 150, unit: 'g' }],
        nutritional_summary: { calories: 350, protein: 28, carbohydrates: 12, fat: 18 },
        explanation: 'Rich in protein',
      },
    }),
  },
}));

describe('Single-User Mode & Personal Application Routes', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('automatically initializes single-user session and lands directly on Dashboard', async () => {
    authApi.getSession.mockResolvedValueOnce({
      access_token: 'personal-jwt-token',
      token_type: 'bearer',
      user: { id: 1, name: 'Alex Nutrition', email: 'alex.nutrition@example.com' },
    });

    renderWithProviders(<AppRoutes />, { initialEntries: ['/'], skipDefaultSession: true });

    await waitFor(() => {
      expect(authApi.getSession).toHaveBeenCalled();
      expect(localStorage.getItem('nutrino_token')).toBe('personal-jwt-token');
      expect(screen.getByText(/energy intake/i)).toBeInTheDocument();
    });

    // Verify no login or register screens appear
    expect(screen.queryByText(/sign in to nutrino/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/create account/i)).not.toBeInTheDocument();
  });

  it('restores existing user session on direct /dashboard access', async () => {
    localStorage.setItem('nutrino_token', 'valid-stored-token');
    authApi.getCurrentUser.mockResolvedValueOnce({
      id: 1,
      name: 'Alex Nutrition',
      email: 'alex.nutrition@example.com',
    });

    renderWithProviders(<AppRoutes />, { initialEntries: ['/dashboard'] });

    await waitFor(() => {
      expect(authApi.getCurrentUser).toHaveBeenCalled();
      expect(screen.getByText(/energy intake/i)).toBeInTheDocument();
    });
  });

  it('verifies /login route does not exist and falls through to 404 page', async () => {
    localStorage.setItem('nutrino_token', 'valid-stored-token');
    authApi.getCurrentUser.mockResolvedValueOnce({
      id: 1,
      name: 'Alex Nutrition',
      email: 'alex.nutrition@example.com',
    });

    renderWithProviders(<AppRoutes />, { initialEntries: ['/login'] });

    await waitFor(() => {
      expect(screen.getByText(/404 — Page Not Found/i)).toBeInTheDocument();
    });
    expect(screen.queryByLabelText(/password/i)).not.toBeInTheDocument();
  });

  it('verifies /register route does not exist and falls through to 404 page', async () => {
    localStorage.setItem('nutrino_token', 'valid-stored-token');
    authApi.getCurrentUser.mockResolvedValueOnce({
      id: 1,
      name: 'Alex Nutrition',
      email: 'alex.nutrition@example.com',
    });

    renderWithProviders(<AppRoutes />, { initialEntries: ['/register'] });

    await waitFor(() => {
      expect(screen.getByText(/404 — Page Not Found/i)).toBeInTheDocument();
    });
    expect(screen.queryByRole('button', { name: /create account/i })).not.toBeInTheDocument();
  });

  it('sidebar navigation renders personal app links and contains no login/signup buttons', async () => {
    localStorage.setItem('nutrino_token', 'valid-stored-token');
    authApi.getCurrentUser.mockResolvedValueOnce({
      id: 1,
      name: 'Alex Nutrition',
      email: 'alex.nutrition@example.com',
    });

    renderWithProviders(<AppRoutes />, { initialEntries: ['/dashboard'] });

    await waitFor(() => {
      expect(screen.getAllByText('Dashboard').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('Meals').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('Nutrition').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('AI Assistant').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('Recommendations').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('Goals').length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText('Profile').length).toBeGreaterThanOrEqual(1);
    });

    expect(screen.queryByText(/sign in/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/log in/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/get started/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/sign out/i)).not.toBeInTheDocument();
  });
});
