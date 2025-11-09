import { HTMLAttributes, ReactNode } from 'react';

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  header?: ReactNode;
  footer?: ReactNode;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hoverable?: boolean;
  fullWidth?: boolean;
}

export const Card = ({
  children,
  header,
  footer,
  padding = 'md',
  hoverable = false,
  fullWidth = false,
  className = '',
  ...props
}: CardProps) => {
  const baseStyles = 'bg-white border border-neutral-200 rounded-lg shadow-sm';

  const paddingStyles = {
    none: 'p-0',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  const hoverStyles = hoverable ? 'hover:shadow-md transition-shadow cursor-pointer' : '';
  const widthStyles = fullWidth ? 'w-full' : '';

  const cardClasses = `${baseStyles} ${paddingStyles[padding]} ${hoverStyles} ${widthStyles} ${className}`.trim();

  return (
    <div className={cardClasses} {...props}>
      {header && (
        <div className={padding !== 'none' ? '-mx-6 -mt-6 px-6 py-4 border-b border-neutral-200' : 'px-6 py-4 border-b border-neutral-200'}>
          {header}
        </div>
      )}

      <div className={header || footer ? (padding !== 'none' ? 'py-4' : 'p-6') : ''}>
        {children}
      </div>

      {footer && (
        <div className={padding !== 'none' ? '-mx-6 -mb-6 px-6 py-4 border-t border-neutral-200' : 'px-6 py-4 border-t border-neutral-200'}>
          {footer}
        </div>
      )}
    </div>
  );
};
