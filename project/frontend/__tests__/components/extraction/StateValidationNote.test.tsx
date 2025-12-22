import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import StateValidationNote from '@/components/extraction/StateValidationNote';

describe('StateValidationNote', () => {
  it('renders with jurisdiction and message', () => {
    render(
      <StateValidationNote
        jurisdiction="US-CA"
        message="Validated against California GAP insurance requirements"
      />
    );

    expect(
      screen.getByText('Validated against California GAP insurance requirements')
    ).toBeInTheDocument();
  });

  it('returns null when no data provided', () => {
    const { container } = render(<StateValidationNote />);
    expect(container.firstChild).toBeNull();
  });

  it('displays multi-state conflicts when provided', () => {
    const conflicts = [
      {
        jurisdiction: 'US-NY',
        field: 'refund_calculation_method',
        conflict: 'NY prohibits Rule of 78s method',
      },
      {
        jurisdiction: 'US-TX',
        field: 'cancellation_fee',
        conflict: 'TX requires fee under $75',
      },
    ];

    render(<StateValidationNote jurisdiction="US-CA" conflicts={conflicts} />);

    // Conflicts should be collapsed initially
    expect(screen.getByText('Multi-State Conflicts (2)')).toBeInTheDocument();
    expect(
      screen.queryByText('NY prohibits Rule of 78s method')
    ).not.toBeInTheDocument();
  });

  it('expands and collapses conflicts on click', () => {
    const conflicts = [
      {
        jurisdiction: 'US-NY',
        field: 'refund_calculation_method',
        conflict: 'NY prohibits Rule of 78s method',
      },
    ];

    render(<StateValidationNote conflicts={conflicts} />);

    const button = screen.getByText('Multi-State Conflicts (1)');

    // Initially collapsed
    expect(
      screen.queryByText('NY prohibits Rule of 78s method')
    ).not.toBeInTheDocument();

    // Expand
    fireEvent.click(button);
    expect(
      screen.getByText('NY prohibits Rule of 78s method')
    ).toBeInTheDocument();

    // Collapse
    fireEvent.click(button);
    expect(
      screen.queryByText('NY prohibits Rule of 78s method')
    ).not.toBeInTheDocument();
  });

  it('renders message without conflicts', () => {
    render(
      <StateValidationNote
        jurisdiction="US-CA"
        message="Premium validated against CA limits"
      />
    );

    expect(screen.getByText('Premium validated against CA limits')).toBeInTheDocument();
    expect(screen.queryByText('Multi-State Conflicts')).not.toBeInTheDocument();
  });
});
