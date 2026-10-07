import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { LoadingState } from '../components/common/LoadingState';
import { EmptyState } from '../components/common/EmptyState';
import { ErrorState } from '../components/common/ErrorState';
import { Modal } from '../components/common/Modal';

describe('Common UI Components', () => {
  it('renders Button variants and handles onClick', () => {
    const handleClick = vi.fn();
    render(<Button variant="primary" onClick={handleClick}>Click Me</Button>);

    const button = screen.getByRole('button', { name: /click me/i });
    expect(button).toBeInTheDocument();
    fireEvent.click(button);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('renders LoadingState with message', () => {
    render(<LoadingState message="Processing request..." />);
    expect(screen.getByText('Processing request...')).toBeInTheDocument();
  });

  it('renders EmptyState with action button', () => {
    const onAction = vi.fn();
    render(
      <EmptyState
        title="No meals found"
        description="Log your first meal to start tracking."
        action={<Button onClick={onAction}>Log Meal</Button>}
      />
    );
    expect(screen.getByText('No meals found')).toBeInTheDocument();
    expect(screen.getByText('Log your first meal to start tracking.')).toBeInTheDocument();
    const btn = screen.getByRole('button', { name: /log meal/i });
    fireEvent.click(btn);
    expect(onAction).toHaveBeenCalledTimes(1);
  });

  it('renders ErrorState with retry handler', () => {
    const onRetry = vi.fn();
    render(
      <ErrorState
        title="Failed to load"
        message="Network timeout"
        onRetry={onRetry}
      />
    );
    expect(screen.getByText('Failed to load')).toBeInTheDocument();
    expect(screen.getByText('Network timeout')).toBeInTheDocument();
    const retryBtn = screen.getByRole('button', { name: /retry request/i });
    fireEvent.click(retryBtn);
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('renders Badge with custom variant', () => {
    render(<Badge variant="success">Completed</Badge>);
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });

  it('renders Modal when isOpen is true and calls onClose', () => {
    const onClose = vi.fn();
    render(
      <Modal isOpen={true} onClose={onClose} title="Test Modal">
        <p>Modal body content</p>
      </Modal>
    );
    expect(screen.getByText('Test Modal')).toBeInTheDocument();
    expect(screen.getByText('Modal body content')).toBeInTheDocument();

    const closeBtn = screen.getByRole('button', { name: /close modal/i });
    fireEvent.click(closeBtn);
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
