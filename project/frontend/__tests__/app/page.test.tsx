import { describe, it, expect } from 'vitest';
import { render, screen } from '../utils/test-utils';
import Home from '@/app/page';

describe('Home Page', () => {
  it('should render the welcome heading', () => {
    render(<Home />);

    const heading = screen.getByRole('heading', {
      name: /Welcome to the Contract Refund Eligibility System/i,
    });

    expect(heading).toBeInTheDocument();
  });

  it('should display search instruction text', () => {
    render(<Home />);

    const message = screen.getByText(/Search for a contract to begin the refund eligibility review process/i);

    expect(message).toBeInTheDocument();
  });

  it('should render search bar', () => {
    render(<Home />);

    const searchInput = screen.getByPlaceholderText(/Enter account number/i);

    expect(searchInput).toBeInTheDocument();
  });

  it('should render quick stats section', () => {
    render(<Home />);

    expect(screen.getByText(/Contracts Processed/i)).toBeInTheDocument();
    expect(screen.getByText(/Avg Confidence/i)).toBeInTheDocument();
    expect(screen.getByText(/Pending Reviews/i)).toBeInTheDocument();
  });

  it('should render getting started section', () => {
    render(<Home />);

    expect(screen.getByText(/Getting Started/i)).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Search for a Contract/i, level: 4 })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Review AI Extraction/i, level: 4 })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Approve or Correct/i, level: 4 })).toBeInTheDocument();
  });
});
