import React from 'react';
import { render } from '@testing-library/react';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '../context/AuthContext';

export function renderWithProviders(ui, { route = '/', initialEntries = [route], queryClient } = {}) {
  const client = queryClient || new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={initialEntries}>
        <AuthProvider>
          {ui}
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
}
