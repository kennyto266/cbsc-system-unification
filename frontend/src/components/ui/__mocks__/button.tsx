/**
 * Button Component Mock
 * 按钮组件 Mock
 */
import React from 'react';

export const Button = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
    size?: 'default' | 'sm' | 'lg' | 'icon';
  }
>(({ children, className, ...props }, ref) => (
  <button
    ref={ref}
    className={className || ''}
    {...props}
  >
    {children}
  </button>
));

Button.displayName = 'Button';

export default Button;
