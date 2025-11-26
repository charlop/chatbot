import { describe, it, expect, vi } from 'vitest';
import { render, fireEvent, screen } from '@testing-library/react';
import { PDFControls } from '@/components/pdf/PDFControls';

describe('PDFControls', () => {
  const defaultProps = {
    currentPage: 1,
    numPages: 10,
    scale: 1.0,
    onZoomIn: vi.fn(),
    onZoomOut: vi.fn(),
    onPageChange: vi.fn(),
    fileName: 'Test.pdf',
  };

  it('should render file name', () => {
    render(<PDFControls {...defaultProps} />);
    expect(screen.getByText('Test.pdf')).toBeInTheDocument();
  });

  it('should display current page and total pages', () => {
    render(<PDFControls {...defaultProps} />);
    expect(screen.getByDisplayValue('1')).toBeInTheDocument();
    expect(screen.getByText('/ 10')).toBeInTheDocument();
  });

  it('should display zoom percentage', () => {
    render(<PDFControls {...defaultProps} scale={1.5} />);
    expect(screen.getByText('150%')).toBeInTheDocument();
  });

  it('should call onZoomIn when zoom in button clicked', () => {
    const onZoomIn = vi.fn();
    render(<PDFControls {...defaultProps} onZoomIn={onZoomIn} />);

    const zoomInButton = screen.getByLabelText('Zoom in');
    fireEvent.click(zoomInButton);

    expect(onZoomIn).toHaveBeenCalledTimes(1);
  });

  it('should call onZoomOut when zoom out button clicked', () => {
    const onZoomOut = vi.fn();
    render(<PDFControls {...defaultProps} onZoomOut={onZoomOut} />);

    const zoomOutButton = screen.getByLabelText('Zoom out');
    fireEvent.click(zoomOutButton);

    expect(onZoomOut).toHaveBeenCalledTimes(1);
  });

  it('should disable zoom in button at max scale', () => {
    render(<PDFControls {...defaultProps} scale={2.0} />);

    const zoomInButton = screen.getByLabelText('Zoom in');
    expect(zoomInButton).toBeDisabled();
  });

  it('should disable zoom out button at min scale', () => {
    render(<PDFControls {...defaultProps} scale={0.5} />);

    const zoomOutButton = screen.getByLabelText('Zoom out');
    expect(zoomOutButton).toBeDisabled();
  });

  it('should call onPageChange when previous page clicked', () => {
    const onPageChange = vi.fn();
    render(<PDFControls {...defaultProps} currentPage={5} onPageChange={onPageChange} />);

    const prevButton = screen.getByLabelText('Previous page');
    fireEvent.click(prevButton);

    expect(onPageChange).toHaveBeenCalledWith(4);
  });

  it('should call onPageChange when next page clicked', () => {
    const onPageChange = vi.fn();
    render(<PDFControls {...defaultProps} currentPage={5} onPageChange={onPageChange} />);

    const nextButton = screen.getByLabelText('Next page');
    fireEvent.click(nextButton);

    expect(onPageChange).toHaveBeenCalledWith(6);
  });

  it('should disable previous page button on first page', () => {
    render(<PDFControls {...defaultProps} currentPage={1} />);

    const prevButton = screen.getByLabelText('Previous page');
    expect(prevButton).toBeDisabled();
  });

  it('should disable next page button on last page', () => {
    render(<PDFControls {...defaultProps} currentPage={10} />);

    const nextButton = screen.getByLabelText('Next page');
    expect(nextButton).toBeDisabled();
  });

  it('should call onPageChange when page input changes', () => {
    const onPageChange = vi.fn();
    render(<PDFControls {...defaultProps} onPageChange={onPageChange} />);

    const pageInput = screen.getByDisplayValue('1') as HTMLInputElement;
    fireEvent.change(pageInput, { target: { value: '5' } });

    expect(onPageChange).toHaveBeenCalledWith(5);
  });

  it('should render download button when onDownload provided', () => {
    const onDownload = vi.fn();
    render(<PDFControls {...defaultProps} onDownload={onDownload} />);

    const downloadButton = screen.getByLabelText('Download PDF');
    expect(downloadButton).toBeInTheDocument();

    fireEvent.click(downloadButton);
    expect(onDownload).toHaveBeenCalledTimes(1);
  });

  it('should render print button when onPrint provided', () => {
    const onPrint = vi.fn();
    render(<PDFControls {...defaultProps} onPrint={onPrint} />);

    const printButton = screen.getByLabelText('Print PDF');
    expect(printButton).toBeInTheDocument();

    fireEvent.click(printButton);
    expect(onPrint).toHaveBeenCalledTimes(1);
  });

  it('should not render download button when onDownload not provided', () => {
    render(<PDFControls {...defaultProps} />);

    const downloadButton = screen.queryByLabelText('Download PDF');
    expect(downloadButton).not.toBeInTheDocument();
  });
});
