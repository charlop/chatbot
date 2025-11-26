'use client';

export interface HighlightRegion {
  page: number;
  bbox: { x: number; y: number; width: number; height: number };
  color: string;
  confidence?: number;
  fieldName?: string;
}

interface HighlightOverlayProps {
  highlights: HighlightRegion[];
  currentPage: number;
  scale: number;
  pageWidth: number;
  pageHeight: number;
  className?: string;
}

export const HighlightOverlay = ({
  highlights,
  currentPage,
  scale,
  pageWidth,
  pageHeight,
  className = '',
}: HighlightOverlayProps) => {
  // Filter to current page only
  const pageHighlights = highlights.filter(h => h.page === currentPage);

  if (pageHighlights.length === 0) {
    return null;
  }

  return (
    <svg
      className={`absolute inset-0 pointer-events-none z-10 ${className}`}
      width={pageWidth * scale}
      height={pageHeight * scale}
      viewBox={`0 0 ${pageWidth} ${pageHeight}`}
      preserveAspectRatio="xMidYMid meet"
    >
      {pageHighlights.map((highlight, idx) => (
        <g key={idx}>
          <rect
            x={highlight.bbox.x}
            y={highlight.bbox.y}
            width={highlight.bbox.width}
            height={highlight.bbox.height}
            fill={highlight.color}
            fillOpacity={0.3}
            stroke={highlight.color}
            strokeWidth={2 / scale}
            rx={2}
            className="pointer-events-auto transition-all hover:fill-opacity-50 cursor-pointer"
          >
            <title>
              {highlight.fieldName && `${highlight.fieldName}`}
              {highlight.confidence && ` (${highlight.confidence}% confidence)`}
            </title>
          </rect>
        </g>
      ))}
    </svg>
  );
};

/**
 * Helper function to get confidence-based color
 * 90-100%: Green (high confidence)
 * 70-89%: Blue (medium confidence)
 * 0-69%: Red (low confidence - needs review)
 * No confidence: Gray
 */
export function getConfidenceColor(confidence?: number): string {
  if (confidence === undefined || confidence === null) return '#9E9E9E'; // Gray
  if (confidence >= 90) return '#4CAF50';  // Green
  if (confidence >= 70) return '#2196F3';  // Blue
  return '#F44336';  // Red
}
