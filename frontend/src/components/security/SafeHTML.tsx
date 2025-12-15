/**
 * SafeHTML Component
 * Safely renders HTML content with XSS protection
 */

import React from 'react';
import { sanitizeHTML, containsDangerousPatterns } from '../../utils/security';

interface SafeHTMLProps {
  html: string;
  className?: string;
  tag?: 'div' | 'span' | 'p' | 'article' | 'section';
  onClick?: (event: React.MouseEvent) => void;
  children?: React.ReactNode;
  onViolation?: (violation: { html: string; patterns: string[] }) => void;
}

export const SafeHTML: React.FC<SafeHTMLProps> = ({
  html,
  className,
  tag = 'div',
  onClick,
  children,
  onViolation
}) => {
  // Check for dangerous patterns
  const hasDangerousPatterns = containsDangerousPatterns(html);

  // Log violations if detected
  if (hasDangerousPatterns && onViolation) {
    const patterns = ['script', 'iframe', 'object', 'embed', 'javascript:', 'on\\w+'];
    onViolation({ html, patterns });
  }

  // Sanitize HTML
  const sanitizedHTML = sanitizeHTML(html);

  // Create the appropriate element
  const Tag = tag;

  // Handle dangerouslySetInnerHTML safely
  const createMarkup = () => {
    return { __html: sanitizedHTML };
  };

  return (
    <Tag
      className={className}
      onClick={onClick}
      dangerouslySetInnerHTML={createMarkup()}
    >
      {children}
    </Tag>
  );
};

// Higher-order component for safe HTML rendering
export const withSafeHTML = <P extends object>(
  WrappedComponent: React.ComponentType<P>,
  htmlProp: keyof P = 'html' as keyof P
) => {
  const SafeComponent = (props: P) => {
    const htmlContent = props[htmlProp] as string;

    // Only render if HTML is provided
    if (htmlContent) {
      return (
        <SafeHTML html={htmlContent}>
          <WrappedComponent {...props} />
        </SafeHTML>
      );
    }

    return <WrappedComponent {...props} />;
  };

  SafeComponent.displayName = `withSafeHTML(${WrappedComponent.displayName || WrappedComponent.name})`;

  return SafeComponent;
};

// Hook for safe HTML rendering
export const useSafeHTML = (html: string, options?: {
  sanitize?: boolean;
  validate?: boolean;
}) => {
  const [safeHTML, setSafeHTML] = React.useState('');
  const [isSafe, setIsSafe] = React.useState(true);
  const [violation, setViolation] = React.useState<string[] | null>(null);

  React.useEffect(() => {
    try {
      // Validate HTML if requested
      if (options?.validate !== false) {
        const hasViolation = containsDangerousPatterns(html);
        setIsSafe(!hasViolation);

        if (hasViolation) {
          setViolation(['Dangerous patterns detected']);
        }
      }

      // Sanitize HTML if requested
      if (options?.sanitize !== false) {
        const sanitized = sanitizeHTML(html);
        setSafeHTML(sanitized);
      } else {
        setSafeHTML(html);
      }
    } catch (error) {
      console.error('SafeHTML error:', error);
      setIsSafe(false);
      setViolation(['Processing error']);
      setSafeHTML('');
    }
  }, [html, options]);

  return {
    safeHTML,
    isSafe,
    violation,
    createMarkup: () => ({ __html: safeHTML })
  };
};

export default SafeHTML;