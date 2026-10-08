import React from 'react';
import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '../context/AuthContext';

export function renderWithProviders(
  ui,
  { route = '/', initialEntries = [route], queryClient, skipDefaultSession = false } = {}
) {
  if (!skipDefaultSession && !localStorage.getItem('nutrino_token')) {
    localStorage.setItem('nutrino_token', 'test-token');
    localStorage.setItem(
      'nutrino_user',
      JSON.stringify({ id: 1, name: 'Alex Nutrition', email: 'alex.nutrition@example.com' })
    );
  }

  const client =
    queryClient ||
    new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });

  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={initialEntries}>
        <AuthProvider>{ui}</AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
}
