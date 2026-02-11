import { ButtonHTMLAttributes } from 'react';
import { cn } from '../../lib/utils';

export const Button = ({ className, ...props }: ButtonHTMLAttributes<HTMLButtonElement>) => (
  <button
    className={cn(
      'inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition disabled:opacity-50',
      'bg-slate-900 text-white hover:bg-slate-800',
      className,
    )}
    {...props}
  />
);
