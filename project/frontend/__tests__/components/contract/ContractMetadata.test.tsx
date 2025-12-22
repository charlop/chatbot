import React from 'react';
import { render, screen } from '@testing-library/react';
import ContractMetadata from '@/components/contract/ContractMetadata';

describe('ContractMetadata', () => {
  it('renders all metadata fields', () => {
    render(
      <ContractMetadata
        contractId="GAP-2024-001"
        accountNumber="123456789012"
        state="CA"
        contractType="GAP Insurance"
        templateVersion="1.0"
      />
    );

    expect(screen.getByText('GAP-2024-001')).toBeInTheDocument();
    expect(screen.getByText('123456789012')).toBeInTheDocument();
    expect(screen.getByText('CA')).toBeInTheDocument();
    expect(screen.getByText('GAP Insurance')).toBeInTheDocument();
    expect(screen.getByText('1.0')).toBeInTheDocument();
  });

  it('handles optional fields gracefully', () => {
    render(<ContractMetadata contractId="GAP-2024-001" />);

    expect(screen.getByText('GAP-2024-001')).toBeInTheDocument();
    expect(screen.queryByText('Account Number')).not.toBeInTheDocument();
  });

  it('displays contract details header', () => {
    render(<ContractMetadata contractId="GAP-2024-001" />);
    expect(screen.getByText('Contract Details')).toBeInTheDocument();
  });

  it('renders multi-state contracts with applicable states', () => {
    render(
      <ContractMetadata
        contractId="GAP-2024-001"
        state="CA"
        applicableStates={['CA', 'NY', 'TX']}
      />
    );

    expect(screen.getByText('CA')).toBeInTheDocument();
    // StateIndicator should show additional states excluding primary
    expect(screen.getByText('Also: NY, TX')).toBeInTheDocument();
  });

  it('renders without state information', () => {
    render(
      <ContractMetadata
        contractId="GAP-2024-001"
        contractType="GAP Insurance"
      />
    );

    expect(screen.getByText('GAP-2024-001')).toBeInTheDocument();
    expect(screen.getByText('GAP Insurance')).toBeInTheDocument();
    expect(screen.queryByText('State')).not.toBeInTheDocument();
  });
});
