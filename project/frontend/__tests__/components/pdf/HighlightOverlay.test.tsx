import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { HighlightOverlay, getConfidenceColor, type HighlightRegion } from '@/components/pdf/HighlightOverlay';

describe('HighlightOverlay', () => {
  const mockHighlights: HighlightRegion[] = [
    {
      page: 1,
      bbox: { x: 100, y: 100, width: 200, height: 20 },
      color: '#4CAF50',
      confidence: 95,
      fieldName: 'GAP Insurance Premium',
    },
    {
      page: 2,
      bbox: { x: 150, y: 200, width: 180, height: 18 },
      color: '#F44336',
      confidence: 65,
      fieldName: 'Cancellation Fee',
    },
  ];

  it('should render highlights for current page only', () => {
    const { container } = render(
      <HighlightOverlay
        highlights={mockHighlights}
        currentPage={1}
        scale={1.0}
        pageWidth={612}
        pageHeight={792}
      />
    );

    // Should render 1 rectangle (page 1 only)
    const rects = container.querySelectorAll('rect');
    expect(rects).toHaveLength(1);
  });

  it('should apply correct colors to highlights', () => {
    const { container } = render(
      <HighlightOverlay
        highlights={[mockHighlights[0]]}
        currentPage={1}
        scale={1.0}
        pageWidth={612}
        pageHeight={792}
      />
    );

    const rect = container.querySelector('rect');
    expect(rect).toHaveAttribute('fill', '#4CAF50');
  });

  it('should render nothing when no highlights for current page', () => {
    const { container } = render(
      <HighlightOverlay
        highlights={mockHighlights}
        currentPage={3}
        scale={1.0}
        pageWidth={612}
        pageHeight={792}
      />
    );

    expect(container.querySelector('svg')).toBeNull();
  });

  it('should include field name and confidence in title', () => {
    const { container } = render(
      <HighlightOverlay
        highlights={[mockHighlights[0]]}
        currentPage={1}
        scale={1.0}
        pageWidth={612}
        pageHeight={792}
      />
    );

    const title = container.querySelector('title');
    expect(title?.textContent).toContain('GAP Insurance Premium');
    expect(title?.textContent).toContain('95% confidence');
  });

  it('should scale coordinates with scale factor', () => {
    const { container } = render(
      <HighlightOverlay
        highlights={[mockHighlights[0]]}
        currentPage={1}
        scale={1.5}
        pageWidth={612}
        pageHeight={792}
      />
    );

    const svg = container.querySelector('svg');
    expect(svg).toHaveAttribute('width', String(612 * 1.5));
    expect(svg).toHaveAttribute('height', String(792 * 1.5));
  });
});

describe('getConfidenceColor', () => {
  it('should return green for high confidence (90-100%)', () => {
    expect(getConfidenceColor(95)).toBe('#4CAF50');
    expect(getConfidenceColor(90)).toBe('#4CAF50');
    expect(getConfidenceColor(100)).toBe('#4CAF50');
  });

  it('should return blue for medium confidence (70-89%)', () => {
    expect(getConfidenceColor(85)).toBe('#2196F3');
    expect(getConfidenceColor(70)).toBe('#2196F3');
    expect(getConfidenceColor(89)).toBe('#2196F3');
  });

  it('should return red for low confidence (0-69%)', () => {
    expect(getConfidenceColor(50)).toBe('#F44336');
    expect(getConfidenceColor(0)).toBe('#F44336');
    expect(getConfidenceColor(69)).toBe('#F44336');
  });

  it('should return gray for no confidence', () => {
    expect(getConfidenceColor(undefined)).toBe('#9E9E9E');
    expect(getConfidenceColor()).toBe('#9E9E9E');
  });
});
