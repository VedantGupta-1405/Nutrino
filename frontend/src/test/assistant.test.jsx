import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { AssistantPage } from '../pages/AssistantPage';
import { renderWithProviders } from './test-utils';
import { agentApi } from '../api/agent';

vi.mock('../api/agent', () => ({
  agentApi: {
    chatWithAgent: vi.fn(),
  },
}));

describe('AssistantPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders initial welcome message and sends user query', async () => {
    agentApi.chatWithAgent.mockResolvedValueOnce({
      response: 'You have consumed 1,200 calories today out of your 2,000 kcal target.',
      tools_used: ['get_today_nutrition'],
    });

    renderWithProviders(<AssistantPage />, { route: '/assistant' });

    expect(screen.getByText(/Hello! I am your Nutrino nutrition assistant/i)).toBeInTheDocument();

    const input = screen.getByPlaceholderText(/Ask a nutrition question/i);
    fireEvent.change(input, { target: { value: 'How many calories have I eaten today?' } });
    fireEvent.click(screen.getByRole('button', { name: /send/i }));

    expect(await screen.findByText(/You have consumed 1,200 calories today/i)).toBeInTheDocument();
    expect(screen.getByText('get_today_nutrition')).toBeInTheDocument();
  });
});
