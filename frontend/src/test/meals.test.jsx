import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { MealsPage } from '../pages/MealsPage';
import { renderWithProviders } from './test-utils';
import { mealsApi } from '../api/meals';

vi.mock('../api/meals', () => ({
  mealsApi: {
    listMeals: vi.fn(),
    deleteMeal: vi.fn(),
  },
}));

describe('MealsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders meal list and opens details modal on click', async () => {
    mealsApi.listMeals.mockResolvedValueOnce([
      {
        id: 42,
        meal_type: 'LUNCH',
        consumed_at: '2026-10-08T13:00:00Z',
        items: [
          {
            id: 1,
            food_name: 'Cooked Toor Dal',
            quantity: 1,
            unit: 'cup',
            calculated_calories: 220,
            calculated_protein: 14,
            calculated_carbohydrates: 36,
            calculated_fat: 4,
          },
        ],
        total_calories: 220,
        total_protein: 14,
        total_carbohydrates: 36,
        total_fat: 4,
      },
    ]);

    renderWithProviders(<MealsPage />, { route: '/meals' });

    expect(await screen.findByText('Cooked Toor Dal')).toBeInTheDocument();
    expect(screen.getByText('220')).toBeInTheDocument();

    // Click meal card to open detail modal
    fireEvent.click(screen.getByText('Cooked Toor Dal'));

    expect(await screen.findByText(/LUNCH Details/i)).toBeInTheDocument();
    expect(screen.getByText(/Itemized Breakdown/i)).toBeInTheDocument();
  });

  it('confirms and calls deleteMeal when delete button is pressed', async () => {
    mealsApi.listMeals.mockResolvedValueOnce([
      {
        id: 99,
        meal_type: 'DINNER',
        consumed_at: '2026-10-08T20:00:00Z',
        items: [{ id: 1, food_name: 'Plain Dosa', quantity: 1, unit: 'piece' }],
        total_calories: 133,
        total_protein: 2.7,
        total_carbohydrates: 18.8,
        total_fat: 5.2,
      },
    ]);
    mealsApi.deleteMeal.mockResolvedValueOnce(true);

    renderWithProviders(<MealsPage />, { route: '/meals' });

    const deleteBtn = await screen.findByTitle(/delete meal record/i);
    fireEvent.click(deleteBtn);

    expect(await screen.findByText(/Confirm Meal Deletion/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /delete record/i }));

    await waitFor(() => {
      expect(mealsApi.deleteMeal).toHaveBeenCalledWith(99);
    });
  });
});
