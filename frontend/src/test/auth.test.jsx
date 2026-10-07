import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { LoginPage } from '../pages/LoginPage';
import { RegisterPage } from '../pages/RegisterPage';
import { AppRoutes } from '../routes/AppRoutes';
import { renderWithProviders } from './test-utils';
import { authApi } from '../api/auth';

vi.mock('../api/auth', () => ({
  authApi: {
    login: vi.fn(),
    register: vi.fn(),
    getCurrentUser: vi.fn(),
  },
}));

describe('Authentication Pages & Routing', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('renders login form with email and password fields', () => {
    renderWithProviders(<LoginPage />, { route: '/login' });
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('shows error message on empty login submission', async () => {
    renderWithProviders(<LoginPage />, { route: '/login' });
    const submitBtn = screen.getByRole('button', { name: /sign in/i });
    fireEvent.submit(submitBtn.closest('form'));

    expect(await screen.findByText(/please enter both your email address and password/i)).toBeInTheDocument();
  });

  it('submits login successfully with valid credentials', async () => {
    authApi.login.mockResolvedValueOnce({
      access_token: 'fake-jwt-token',
      token_type: 'bearer',
      user: { id: 1, name: 'Test User', email: 'test@example.com' },
    });

    renderWithProviders(<LoginPage />, { route: '/login' });
    fireEvent.change(screen.getByLabelText(/email address/i), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password123' } });
    const submitBtn = screen.getByRole('button', { name: /sign in/i });
    fireEvent.submit(submitBtn.closest('form'));

    await waitFor(() => {
      expect(authApi.login).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
      });
      expect(localStorage.getItem('nutrino_token')).toBe('fake-jwt-token');
    });
  });

  it('renders registration form and validates input', async () => {
    renderWithProviders(<RegisterPage />, { route: '/register' });
    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/full name/i), { target: { value: 'Jane Doe' } });
    fireEvent.change(screen.getByLabelText(/email address/i), { target: { value: 'jane@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'short' } });
    const createBtn = screen.getByRole('button', { name: /create account/i });
    fireEvent.submit(createBtn.closest('form'));

    const msgs = await screen.findAllByText(/must be at least 8 characters/i);
    expect(msgs.length).toBeGreaterThanOrEqual(1);
  });

  it('redirects unauthenticated user from protected route to login', async () => {
    renderWithProviders(<AppRoutes />, { initialEntries: ['/dashboard'] });
    expect(await screen.findByText(/sign in to nutrino/i)).toBeInTheDocument();
  });
});
