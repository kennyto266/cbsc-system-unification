import React from 'react';
import { clsx } from 'clsx';

interface SafeAreaProps {
  children: React.ReactNode;
  top?: boolean;
  bottom?: boolean;
  left?: boolean;
  right?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

/**
 * SafeArea component handles safe area insets for mobile devices
 * with notches, rounded corners, or home indicators.
 */
const SafeArea: React.FC<SafeAreaProps> = ({
  children,
  top = false,
  bottom = false,
  left = false,
  right = false,
  className,
  style,
}) => {
  const safeAreaStyle: React.CSSProperties = {
    paddingTop: top ? 'env(safe-area-inset-top)' : undefined,
    paddingBottom: bottom ? 'env(safe-area-inset-bottom)' : undefined,
    paddingLeft: left ? 'env(safe-area-inset-left)' : undefined,
    paddingRight: right ? 'env(safe-area-inset-right)' : undefined,
    ...style,
  };

  return (
    <div
      className={clsx(
        'safe-area',
        {
          'safe-area--top': top,
          'safe-area--bottom': bottom,
          'safe-area--left': left,
          'safe-area--right': right,
        },
        className
      )}
      style={safeAreaStyle}
    >
      {children}
    </div>
  );
};

export default SafeArea;

/**
 * Hook to get safe area insets as values
 */
export const useSafeAreaInsets = () => {
  const [insets, setInsets] = React.useState({
    top: 0,
    bottom: 0,
    left: 0,
    right: 0,
  });

  React.useEffect(() => {
    if (typeof window === 'undefined') return;

    const updateInsets = () => {
      const computedStyle = getComputedStyle(document.documentElement);
      setInsets({
        top: parseInt(computedStyle.getPropertyValue('--safe-area-inset-top') || '0'),
        bottom: parseInt(computedStyle.getPropertyValue('--safe-area-inset-bottom') || '0'),
        left: parseInt(computedStyle.getPropertyValue('--safe-area-inset-left') || '0'),
        right: parseInt(computedStyle.getPropertyValue('--safe-area-inset-right') || '0'),
      });
    };

    // Add CSS variables for safe area insets
    const style = document.createElement('style');
    style.textContent = `
      :root {
        --safe-area-inset-top: env(safe-area-inset-top);
        --safe-area-inset-bottom: env(safe-area-inset-bottom);
        --safe-area-inset-left: env(safe-area-inset-left);
        --safe-area-inset-right: env(safe-area-inset-right);
      }
    `;
    document.head.appendChild(style);

    updateInsets();

    // Listen for orientation changes
    const handleOrientationChange = () => {
      setTimeout(updateInsets, 100);
    };
    window.addEventListener('orientationchange', handleOrientationChange);

    return () => {
      document.head.removeChild(style);
      window.removeEventListener('orientationchange', handleOrientationChange);
    };
  }, []);

  return insets;
};