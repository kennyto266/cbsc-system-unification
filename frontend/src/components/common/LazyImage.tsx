import React, { useState, useRef, useEffect } from 'react';
import { useIntersectionObserver } from '../../hooks/useIntersectionObserver';
import { clsx } from 'clsx';

interface LazyImageProps {
  src: string;
  alt: string;
  className?: string;
  placeholderSrc?: string;
  blurDataURL?: string;
  width?: number | string;
  height?: number | string;
  objectFit?: 'cover' | 'contain' | 'fill' | 'none' | 'scale-down';
  loading?: 'lazy' | 'eager';
  onLoad?: () => void;
  onError?: () => void;
  style?: React.CSSProperties;
}

/**
 * LazyImage component with blur-up effect and intersection observer
 */
const LazyImage: React.FC<LazyImageProps> = ({
  src,
  alt,
  className,
  placeholderSrc,
  blurDataURL,
  width,
  height,
  objectFit = 'cover',
  loading = 'lazy',
  onLoad,
  onError,
  style,
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [currentSrc, setCurrentSrc] = useState(placeholderSrc || blurDataURL);
  const imgRef = useRef<HTMLImageElement>(null);

  const { ref: intersectionRef, isIntersecting } = useIntersectionObserver({
    threshold: 0.1,
    rootMargin: '50px',
  });

  // Combine refs
  const setRefs = (node: HTMLImageElement) => {
    imgRef.current = node;
    (intersectionRef as React.RefObject<HTMLImageElement>).current = node;
  };

  useEffect(() => {
    if (isIntersecting && currentSrc !== src && !isLoaded && !hasError) {
      const img = new Image();

      img.onload = () => {
        setCurrentSrc(src);
        setIsLoaded(true);
        onLoad?.();
      };

      img.onerror = () => {
        setHasError(true);
        onError?.();
      };

      img.src = src;
    }
  }, [isIntersecting, src, currentSrc, isLoaded, hasError, onLoad, onError]);

  const containerStyle: React.CSSProperties = {
    width,
    height,
    position: 'relative',
    overflow: 'hidden',
    ...style,
  };

  const imageStyle: React.CSSProperties = {
    width: '100%',
    height: '100%',
    objectFit,
    transition: 'opacity 0.3s ease-in-out, filter 0.3s ease-in-out',
    opacity: isLoaded ? 1 : 0,
    filter: isLoaded ? 'none' : 'blur(10px)',
  };

  const placeholderStyle: React.CSSProperties = {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    objectFit,
    opacity: isLoaded ? 0 : 1,
    filter: blurDataURL ? 'blur(10px)' : 'none',
    transition: 'opacity 0.3s ease-in-out',
    backgroundColor: '#f3f4f6',
  };

  return (
    <div style={containerStyle} className={clsx('lazy-image-container', className)}>
      {/* Placeholder or blur image */}
      {placeholderSrc || blurDataURL ? (
        <img
          src={placeholderSrc || blurDataURL}
          alt=""
          aria-hidden="true"
          style={placeholderStyle}
        />
      ) : (
        <div
          style={{
            ...placeholderStyle,
            background: 'linear-gradient(to bottom, #f3f4f6, #e5e7eb)',
          }}
        />
      )}

      {/* Main image */}
      <img
        ref={setRefs}
        src={currentSrc}
        alt={alt}
        style={imageStyle}
        loading={loading}
      />

      {/* Error state */}
      {hasError && (
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            backgroundColor: '#f3f4f6',
            color: '#6b7280',
          }}
        >
          <svg
            className="w-12 h-12"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
        </div>
      )}

      {/* Loading indicator */}
      {!isLoaded && !hasError && (
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
          }}
        >
          <div
            style={{
              width: '40px',
              height: '40px',
              border: '3px solid #f3f4f6',
              borderTop: '3px solid #3b82f6',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
            }}
          />
        </div>
      )}
    </div>
  );
};

export default LazyImage;

// Add spin animation
const styleSheet = document.createElement('style');
styleSheet.textContent = `
  @keyframes spin {
    0% { transform: translate(-50%, -50%) rotate(0deg); }
    100% { transform: translate(-50%, -50%) rotate(360deg); }
  }
`;
document.head.appendChild(styleSheet);