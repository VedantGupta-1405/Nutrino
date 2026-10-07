import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { renderWithProviders } from './test-utils';
import { NutritionPage } from '../pages/NutritionPage';
import { nutritionApi } from '../api/nutrition';

vi.mock('../api/nutrition', () => ({
  nutritionApi: {
    getTodayNutrition: vi.fn(),
    getNutritionHistory: vi.fn(),
  },
}));

// Mock recharts to prevent SVG layout issues in happy-dom
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }) => <div data-testid="chart-container">{children}</div>,
  PieChart: ({ children }) => <div data-testid="pie-chart">{children}</div>,
  Pie: ({ children }) => <div>{children}</div>,
  Cell: () => <div />,
  Tooltip: () => <div />,
  Legend: () => <div />,
  BarChart: ({ children }) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div />,
  LineChart: ({ children }) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div />,
  XAxis: () => <div />,
  YAxis: () => <div />,
  CartesianGrid: () => <div />,
}));

describe('NutritionPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders today nutrition analytics and macro breakdown', async () => {
    nutritionApi.getTodayNutrition.mockResolvedValueOnce({
      date: '2026-10-08',
      consumed: {
        calories: 1450,
        protein: 85,
        carbohydrates: 160,
        fat: 45,
        fiber: 22,
      },
      target: {
        calories: 2000,
        protein: 120,
        carbohydrates: 220,
        fat: 60,
      },
      remaining: {
        calories: 550,
        protein: 35,
        carbohydrates: 60,
        fat: 15,
      },
      meals_count: 3,
    });

    nutritionApi.getNutritionHistory.mockResolvedValueOnce({
      days: [
        {
          date: '2026-10-07',
          consumed: {
            calories: 1600,
            protein: 95,
            carbohydrates: 180,
            fat: 50,
          },
          target: {
            calories: 2000,
            protein: 120,
            carbohydrates: 220,
            fat: 60,
          },
        },
        {
          date: '2026-10-08',
          consumed: {
            calories: 1450,
            protein: 85,
            carbohydrates: 160,
            fat: 45,
          },
          target: {
            calories: 2000,
            protein: 120,
            carbohydrates: 220,
            fat: 60,
          },
        },
      ],
    });

    renderWithProviders(<NutritionPage />);

    expect(screen.getByText('Nutrition Analytics')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('1450')).toBeInTheDocument();
      expect(screen.getByText('85')).toBeInTheDocument();
      expect(screen.getByText('160')).toBeInTheDocument();
      expect(screen.getByText('45')).toBeInTheDocument();
      expect(screen.getByText('22')).toBeInTheDocument();
    });

    expect(screen.getByText("Today's Macro Calorie Split")).toBeInTheDocument();
    expect(screen.getByText('Recent 7-Day Calorie Intake')).toBeInTheDocument();
  });

  it('handles error state when nutrition fetching fails', async () => {
    nutritionApi.getTodayNutrition.mockRejectedValueOnce(new Error('Failed to load nutrition'));
    nutritionApi.getNutritionHistory.mockRejectedValueOnce(new Error('Failed to load history'));

    renderWithProviders(<NutritionPage />);

    await waitFor(() => {
      expect(screen.getByText('Could not load nutrition metrics')).toBeInTheDocument();
    });
  });
});
