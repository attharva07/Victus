import { TextareaHTMLAttributes } from 'react';
import { cn } from '../../lib/utils';

export const Textarea = ({ className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) => (
  <textarea
    className={cn('w-full rounded-md border border-border bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-300', className)}
    {...props}
  />
);
