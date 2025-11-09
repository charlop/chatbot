import { describe, it, expect } from 'vitest';
import { render, screen } from '../utils/test-utils';
import Home from '@/app/page';

describe('Home Page', () => {
  it('should render the main heading', () => {
    render(<Home />);

    const heading = screen.getByRole('heading', {
      name: /Contract Refund Eligibility System/i,
    });

    expect(heading).toBeInTheDocument();
  });

  it('should display tagline', () => {
    render(<Home />);

    const message = screen.getByText(/AI-powered contract review and refund eligibility determination/i);

    expect(message).toBeInTheDocument();
  });

  it('should have proper styling classes', () => {
    render(<Home />);

    const main = screen.getByRole('main');

    expect(main).toHaveClass('flex', 'min-h-screen');
  });
});
