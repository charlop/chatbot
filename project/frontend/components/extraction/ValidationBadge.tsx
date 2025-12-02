import React from 'react';

interface ValidationBadgeProps {
  status?: 'pass' | 'warning' | 'fail';
  reason?: string;
}

export const ValidationBadge: React.FC<ValidationBadgeProps> = ({ status, reason }) => {
  if (!status) return null;

  const styles = {
    pass: 'bg-green-100 text-green-800 border-green-200',
    warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    fail: 'bg-red-100 text-red-800 border-red-200',
  };

  const icons = { pass: '✓', warning: '⚠', fail: '✗' };

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium border ${styles[status]}`}
      title={reason}
    >
      {icons[status]} {status}
    </span>
  );
};
