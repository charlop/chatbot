import React, { useState, useRef, useEffect } from 'react';
import { ConfidenceBadge } from './ConfidenceBadge';

export interface DataCardProps {
  /**
   * Field label (e.g., "GAP Insurance Premium")
   */
  label: string;

  /**
   * Field value
   */
  value: string;

  /**
   * Confidence score (0-100)
   */
  confidence?: number;

  /**
   * Source location in document
   */
  source?: string;

  /**
   * Whether the field has been edited
   */
  isEdited?: boolean;

  /**
   * Whether editing is disabled
   */
  disabled?: boolean;

  /**
   * Callback when value changes
   */
  onChange?: (newValue: string) => void;

  /**
   * Callback when "View in document" is clicked
   */
  onViewInDocument?: () => void;

  /**
   * Optional CSS class
   */
  className?: string;
}

/**
 * Card component for displaying an extracted data field with inline editing
 */
export const DataCard: React.FC<DataCardProps> = ({
  label,
  value,
  confidence,
  source,
  isEdited = false,
  disabled = false,
  onChange,
  onViewInDocument,
  className = '',
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value);
  const inputRef = useRef<HTMLInputElement>(null);

  // Update edit value when prop changes
  useEffect(() => {
    setEditValue(value);
  }, [value]);

  // Focus input when entering edit mode
  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const handleStartEdit = () => {
    if (!disabled) {
      setIsEditing(true);
      setEditValue(value);
    }
  };

  const handleSave = () => {
    if (editValue !== value && onChange) {
      onChange(editValue);
    }
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditValue(value);
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSave();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleCancel();
    }
  };

  const handleValueClick = () => {
    handleStartEdit();
  };

  const handleValueKeyDown = (e: React.KeyboardEvent<HTMLSpanElement>) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleStartEdit();
    }
  };

  const displayValue = value || 'No value';
  const isEmpty = !value;

  return (
    <div className={`bg-white border border-neutral-200 rounded-lg p-4 ${className}`}>
      {/* Label and Confidence */}
      <div className="flex items-start justify-between mb-2">
        <h3 className="text-sm font-semibold text-neutral-900">{label}</h3>
        <ConfidenceBadge confidence={confidence} />
      </div>

      {/* Value - Editable */}
      <div className="mb-3">
        {isEditing ? (
          <input
            ref={inputRef}
            type="text"
            role="textbox"
            value={editValue}
            onChange={(e) => setEditValue(e.target.value)}
            onBlur={handleSave}
            onKeyDown={handleKeyDown}
            className="w-full px-3 py-2 text-base font-medium text-neutral-900 border border-primary-500 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        ) : (
          <span
            role="button"
            tabIndex={0}
            onClick={handleValueClick}
            onKeyDown={handleValueKeyDown}
            aria-label={`Click to edit ${label}: ${displayValue}`}
            className={`block w-full px-3 py-2 text-base font-medium rounded-md cursor-pointer transition-colors ${
              disabled
                ? 'text-neutral-400 cursor-not-allowed'
                : isEmpty
                ? 'text-neutral-400 hover:bg-neutral-50'
                : 'text-neutral-900 hover:bg-neutral-50'
            } ${!disabled ? 'focus:outline-none focus:ring-2 focus:ring-primary-300' : ''}`}
          >
            {displayValue}
          </span>
        )}
      </div>

      {/* Edited Indicator */}
      {isEdited && (
        <div className="flex items-center gap-1 mb-3">
          <svg
            className="w-4 h-4 text-primary"
            fill="currentColor"
            viewBox="0 0 20 20"
            aria-hidden="true"
          >
            <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
          </svg>
          <span className="text-xs font-medium text-primary">Edited</span>
        </div>
      )}

      {/* Source and Actions */}
      <div className="flex items-center justify-between">
        {source ? (
          <p className="text-xs text-neutral-600">
            <span className="font-medium">Source:</span> {source}
          </p>
        ) : (
          <span className="text-xs text-neutral-400">No source location</span>
        )}

        {onViewInDocument && (
          <button
            onClick={onViewInDocument}
            className="text-xs font-medium text-primary hover:text-primary-dark transition-colors focus:outline-none focus:underline"
            aria-label="View in document"
          >
            View in document →
          </button>
        )}
      </div>
    </div>
  );
};
