import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { RecommendationsPage } from '../pages/RecommendationsPage';
import { renderWithProviders } from './test-utils';
import { recommendationsApi } from '../api/recommendations';

vi.mock('../api/recommendations', () => ({
  recommendationsApi: {
    getMealRecommendation: vi.fn(),
  },
}));

describe('RecommendationsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders initial recommendation and allows preset selection', async () => {
    recommendationsApi.getMealRecommendation.mockResolvedValueOnce({
      recommendation_summary: 'Paneer Salad & Roti',
      meal_type: 'DINNER',
      items: [
        {
          food_id: 5,
          food_name: 'Paneer',
          quantity: 100,
          unit: 'gram',
          calories: 265,
          protein: 18,
          carbohydrates: 3,
          fat: 20,
          fiber: 0,
        },
      ],
      total_calories: 265,
      total_protein: 18,
      total_carbohydrates: 3,
      total_fat: 20,
      total_fiber: 0,
      explanation: 'Fits high-protein requirement deterministically.',
      limitations: ['Food database does not track monetary pricing.'],
    });

    renderWithProviders(<RecommendationsPage />, { route: '/recommendations' });

    expect(await screen.findByText('Paneer Salad & Roti')).toBeInTheDocument();
    expect(screen.getByText('265')).toBeInTheDocument();
    expect(screen.getByText(/Fits high-protein requirement/i)).toBeInTheDocument();
    expect(screen.getByText(/Food database does not track monetary pricing/i)).toBeInTheDocument();

    // Click preset button
    recommendationsApi.getMealRecommendation.mockResolvedValueOnce({
      recommendation_summary: 'Cooked Toor Dal & Rice',
      meal_type: 'LUNCH',
      items: [],
      total_calories: 350,
      total_protein: 12,
      total_carbohydrates: 55,
      total_fat: 3,
      total_fiber: 4,
      explanation: 'Light lunch option.',
      limitations: [],
    });

    fireEvent.click(screen.getByText('Light Lunch Option'));

    await waitFor(() => {
      expect(recommendationsApi.getMealRecommendation).toHaveBeenCalledWith({
        meal_type: 'LUNCH',
        focus: 'light',
      });
    });
  });
});
