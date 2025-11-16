import { InputHTMLAttributes, forwardRef, useId } from 'react';

export interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size'> {
  label?: string;
  helperText?: string;
  error?: string;
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      helperText,
      error,
      size = 'md',
      fullWidth = false,
      required = false,
      disabled = false,
      className = '',
      id,
      type = 'text',
      ...props
    },
    ref
  ) => {
    // Use React's useId() for stable IDs across server/client renders
    const generatedId = useId();
    const inputId = id || generatedId;
    const errorId = `${inputId}-error`;
    const helperTextId = `${inputId}-helper`;

    const baseStyles = 'block border rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1';

    const sizeStyles = {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2 text-base',
      lg: 'px-5 py-3 text-lg',
    };

    const stateStyles = error
      ? 'border-danger-500 focus:ring-danger-500 focus:border-danger-500'
      : 'border-neutral-300 focus:ring-primary-500 focus:border-primary-500';

    const disabledStyles = disabled
      ? 'bg-neutral-100 cursor-not-allowed opacity-60'
      : 'bg-white';

    const inputClasses = `${baseStyles} ${sizeStyles[size]} ${stateStyles} ${disabledStyles} ${className}`.trim();

    const containerClasses = fullWidth ? 'w-full' : '';

    return (
      <div className={containerClasses}>
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-neutral-700 mb-1"
          >
            {label}
            {required && <span className="text-danger-500 ml-1">*</span>}
          </label>
        )}

        <input
          ref={ref}
          id={inputId}
          type={type}
          disabled={disabled}
          required={required}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={
            error ? errorId : helperText ? helperTextId : undefined
          }
          className={inputClasses}
          {...props}
        />

        {error && (
          <p id={errorId} className="mt-1 text-sm text-danger-500" role="alert">
            {error}
          </p>
        )}

        {helperText && !error && (
          <p id={helperTextId} className="mt-1 text-sm text-neutral-500">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
