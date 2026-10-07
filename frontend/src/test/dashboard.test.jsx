import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import { DashboardPage } from '../pages/DashboardPage';
import { renderWithProviders } from './test-utils';
import { nutritionApi } from '../api/nutrition';
import { mealsApi } from '../api/meals';
import { recommendationsApi } from '../api/recommendations';

vi.mock('../api/nutrition', () => ({
  nutritionApi: {
    getTodayNutrition: vi.fn(),
  },
}));

vi.mock('../api/meals', () => ({
  mealsApi: {
    getTodayMeals: vi.fn(),
  },
}));

vi.mock('../api/recommendations', () => ({
  recommendationsApi: {
    getMealRecommendation: vi.fn(),
  },
}));

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem('nutrino_token', 'test-token');
    localStorage.setItem('nutrino_user', JSON.stringify({ id: 1, name: 'Alex Morgan' }));
  });

  it('renders greeting, today nutrition calories, and macro progress', async () => {
    nutritionApi.getTodayNutrition.mockResolvedValueOnce({
      date: '2026-10-08',
      meals_count: 2,
      consumed: {
        calories: 1650,
        protein: 95,
        carbohydrates: 210,
        fat: 48,
        fiber: 22,
      },
      target: {
        calories: 2000,
        protein: 110,
        carbohydrates: 240,
        fat: 60,
      },
      remaining: {
        calories: 350,
        protein: 15,
        carbohydrates: 30,
        fat: 12,
      },
    });

    mealsApi.getTodayMeals.mockResolvedValueOnce([
      {
        id: 10,
        meal_type: 'BREAKFAST',
        consumed_at: '2026-10-08T08:30:00Z',
        items: [{ id: 1, food_name: 'Idli', quantity: 2, unit: 'piece' }],
        total_calories: 116,
        total_protein: 3.2,
        total_carbohydrates: 24,
        total_fat: 0.4,
      },
    ]);

    recommendationsApi.getMealRecommendation.mockResolvedValueOnce({
      recommendation_summary: 'Toor Dal and Steamed Rice',
      meal_type: 'DINNER',
      total_calories: 380,
      total_protein: 14,
      total_carbohydrates: 65,
      total_fat: 4,
      explanation: 'Balanced option fitting remaining calories and macros.',
      limitations: [],
    });

    renderWithProviders(<DashboardPage />, { route: '/dashboard' });

    expect(await screen.findByText(/Alex Morgan/i)).toBeInTheDocument();
    expect(await screen.findByText('1650')).toBeInTheDocument();
    expect(screen.getByText(/2000 kcal/i)).toBeInTheDocument();
    expect(screen.getByText('95g')).toBeInTheDocument();
    expect(screen.getByText('210g')).toBeInTheDocument();
    expect(screen.getByText('48g')).toBeInTheDocument();
    expect(screen.getByText(/Toor Dal and Steamed Rice/i)).toBeInTheDocument();
    expect(screen.getByText('Idli')).toBeInTheDocument();
  });
});
