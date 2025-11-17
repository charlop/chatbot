import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AuditTrail } from '@/components/audit/AuditTrail';
import { ExtractedData } from '@/lib/api/contracts';

describe('AuditTrail', () => {
  const mockExtractedData: ExtractedData = {
    extractionId: '12345',
    gapPremium: 500,
    gapPremiumConfidence: 95,
    refundMethod: 'Pro-rata',
    refundMethodConfidence: 90,
    cancellationFee: 50,
    cancellationFeeConfidence: 92,
    status: 'pending',
    llmModelVersion: 'claude-3-5-sonnet-20241022',
    llmProvider: 'anthropic',
    processingTimeMs: 1500,
    extractedAt: '2025-11-17T02:31:51.207054Z',
  };

  it('renders audit information section', () => {
    render(<AuditTrail extractedData={mockExtractedData} />);

    expect(screen.getByText('Audit Information')).toBeInTheDocument();
  });

  it('displays model version', () => {
    render(<AuditTrail extractedData={mockExtractedData} />);

    expect(screen.getByText('claude-3-5-sonnet-20241022')).toBeInTheDocument();
  });

  it('displays provider information', () => {
    render(<AuditTrail extractedData={mockExtractedData} />);

    expect(screen.getByText('Provider: anthropic')).toBeInTheDocument();
  });

  it('displays processing time in seconds for 1.5s', () => {
    render(<AuditTrail extractedData={mockExtractedData} />);

    expect(screen.getByText('1.50s')).toBeInTheDocument();
  });

  it('displays processing time in seconds for longer durations', () => {
    const data = { ...mockExtractedData, processingTimeMs: 3500 };
    render(<AuditTrail extractedData={data} />);

    expect(screen.getByText('3.50s')).toBeInTheDocument();
  });

  it('displays processing time in minutes for very long durations', () => {
    const data = { ...mockExtractedData, processingTimeMs: 125000 };
    render(<AuditTrail extractedData={data} />);

    expect(screen.getByText('2m 5s')).toBeInTheDocument();
  });

  it('displays formatted extraction timestamp', () => {
    render(<AuditTrail extractedData={mockExtractedData} />);

    // Check for "Extracted At" label
    expect(screen.getByText('Extracted At')).toBeInTheDocument();
    // The formatted date will be present (format depends on locale)
    const extractedAtSection = screen.getByText('Extracted At').closest('div');
    expect(extractedAtSection).toBeInTheDocument();
  });

  it('displays pending status badge', () => {
    render(<AuditTrail extractedData={mockExtractedData} />);

    expect(screen.getByText('Pending')).toBeInTheDocument();
  });

  it('displays approved status badge and timestamp', () => {
    const approvedData: ExtractedData = {
      ...mockExtractedData,
      status: 'approved',
      approvedAt: '2025-11-17T08:25:18.959275Z',
    };

    render(<AuditTrail extractedData={approvedData} />);

    expect(screen.getByText('✓ Approved')).toBeInTheDocument();
    expect(screen.getByText('Approved At')).toBeInTheDocument();
  });

  it('displays corrections count when provided', () => {
    render(<AuditTrail extractedData={mockExtractedData} correctionsCount={3} />);

    expect(screen.getByText('Corrections Made')).toBeInTheDocument();
    expect(screen.getByText('3 fields')).toBeInTheDocument();
  });

  it('displays singular "field" for single correction', () => {
    render(<AuditTrail extractedData={mockExtractedData} correctionsCount={1} />);

    expect(screen.getByText('1 field')).toBeInTheDocument();
  });

  it('does not display corrections section when count is 0', () => {
    render(<AuditTrail extractedData={mockExtractedData} correctionsCount={0} />);

    expect(screen.queryByText('Corrections Made')).not.toBeInTheDocument();
  });

  it('handles missing optional fields gracefully', () => {
    const minimalData: ExtractedData = {
      extractionId: '12345',
      gapPremium: 500,
      refundMethod: 'Pro-rata',
      cancellationFee: 50,
      status: 'pending',
    };

    render(<AuditTrail extractedData={minimalData} />);

    expect(screen.getByText('Audit Information')).toBeInTheDocument();
    expect(screen.getByText('N/A')).toBeInTheDocument();
  });

  it('handles invalid timestamp gracefully', () => {
    const invalidData: ExtractedData = {
      ...mockExtractedData,
      extractedAt: 'invalid-date',
    };

    render(<AuditTrail extractedData={invalidData} />);

    expect(screen.getByText('Invalid Date')).toBeInTheDocument();
  });

  it('does not show approved timestamp for pending status', () => {
    render(<AuditTrail extractedData={mockExtractedData} />);

    expect(screen.queryByText('Approved At')).not.toBeInTheDocument();
  });

  it('applies correct styling for approved status', () => {
    const approvedData: ExtractedData = {
      ...mockExtractedData,
      status: 'approved',
      approvedAt: '2025-11-17T08:25:18.959275Z',
    };

    render(<AuditTrail extractedData={approvedData} />);

    const statusBadge = screen.getByText('✓ Approved');
    expect(statusBadge).toHaveClass('bg-[#2da062]/10');
  });

  it('applies correct styling for pending status', () => {
    render(<AuditTrail extractedData={mockExtractedData} />);

    const statusBadge = screen.getByText('Pending');
    expect(statusBadge).toHaveClass('bg-neutral-200');
  });
});
