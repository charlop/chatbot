import React from 'react';
import { render, screen } from '@testing-library/react';
import StateIndicator from '@/components/contract/StateIndicator';

describe('StateIndicator', () => {
  it('renders primary state code', () => {
    render(<StateIndicator state="CA" />);

    expect(screen.getByText('CA')).toBeInTheDocument();
    expect(screen.getByLabelText('State: California')).toBeInTheDocument();
  });

  it('shows additional states for multi-state contracts', () => {
    render(
      <StateIndicator
        state="CA"
        applicableStates={['NY', 'TX', 'FL']}
      />
    );

    expect(screen.getByText('CA')).toBeInTheDocument();
    expect(screen.getByText('Also: NY, TX, FL')).toBeInTheDocument();
  });

  it('applies correct size classes', () => {
    const { rerender } = render(<StateIndicator state="CA" size="sm" />);
    expect(screen.getByText('CA')).toHaveClass('text-xs');

    rerender(<StateIndicator state="CA" size="md" />);
    expect(screen.getByText('CA')).toHaveClass('text-sm');
  });

  it('displays tooltip with full state name', () => {
    render(<StateIndicator state="NY" showTooltip={true} />);
    const badge = screen.getByText('NY');
    expect(badge).toHaveAttribute('title', 'New York');
  });

  it('hides tooltip when showTooltip is false', () => {
    render(<StateIndicator state="TX" showTooltip={false} />);
    const badge = screen.getByText('TX');
    expect(badge).not.toHaveAttribute('title');
  });

  it('handles unknown state codes gracefully', () => {
    render(<StateIndicator state="XX" />);
    expect(screen.getByText('XX')).toBeInTheDocument();
    expect(screen.getByLabelText('State: XX')).toBeInTheDocument();
  });
});
