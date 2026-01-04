import React, { useState, useEffect, useRef } from 'react';
import styled, { keyframes, css } from 'styled-components';

// 主題配置
export const theme = {
  colors: {
    primary: {
      dark: '#0a0e27',
      secondary: '#151932',
      tertiary: '#1a1f3a',
    },
    neon: {
      cyan: '#00d4ff',
      purple: '#8b5cf6',
      pink: '#ec4899',
      green: '#10b981',
      orange: '#f59e0b',
    },
    gray: {
      900: '#111827',
      800: '#1f2937',
      700: '#374151',
      600: '#4b5563',
      500: '#6b7280',
      400: '#9ca3af',
      300: '#d1d5db',
      200: '#e5e7eb',
      100: '#f3f4f6',
    },
    status: {
      success: '#10b981',
      warning: '#f59e0b',
      error: '#ef4444',
      info: '#3b82f6',
    }
  },
  fonts: {
    display: "'Orbitron', monospace",
    body: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    '2xl': '3rem',
    '3xl': '4rem',
  },
  borderRadius: {
    sm: '0.25rem',
    md: '0.5rem',
    lg: '0.75rem',
    xl: '1rem',
  },
  shadows: {
    neon: '0 0 20px rgba(0, 212, 255, 0.3)',
    card: '0 8px 32px rgba(0, 0, 0, 0.1)',
    cardHover: '0 20px 40px rgba(0, 0, 0, 0.3), 0 0 30px rgba(0, 212, 255, 0.1)',
  },
  transitions: {
    fast: '0.15s ease',
    normal: '0.3s ease',
    slow: '0.5s ease',
  },
};

// 動畫
const fadeIn = keyframes`
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

const glow = keyframes`
  from {
    filter: brightness(1) contrast(1);
  }
  to {
    filter: brightness(1.1) contrast(1.1);
  }
`;

const pulse = keyframes`
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
`;

const slideUp = keyframes`
  from {
    transform: translateY(100%);
  }
  to {
    transform: translateY(0);
  }
`;

// 粒子背景組件
export const ParticleBackground = () => {
  const containerRef = useRef(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const particleCount = 50;
    const particles = [];

    for (let i = 0; i < particleCount; i++) {
      const particle = document.createElement('div');
      particle.style.position = 'absolute';
      particle.style.width = '2px';
      particle.style.height = '2px';
      particle.style.background = theme.colors.neon.cyan;
      particle.style.borderRadius = '50%';
      particle.style.opacity = '0.3';
      particle.style.left = `${Math.random() * 100}%`;
      particle.style.animation = `float ${15 + Math.random() * 10}s linear infinite`;
      particle.style.animationDelay = `${Math.random() * 20}s`;

      container.appendChild(particle);
      particles.push(particle);
    }

    return () => {
      particles.forEach(p => p.remove());
    };
  }, []);

  return (
    <ParticleContainer ref={containerRef}>
      <GradientOverlay />
    </ParticleContainer>
  );
};

const ParticleContainer = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
  overflow: hidden;
`;

const GradientOverlay = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background:
    radial-gradient(ellipse at top left, rgba(139, 92, 246, 0.1) 0%, transparent 50%),
    radial-gradient(ellipse at bottom right, rgba(0, 212, 255, 0.1) 0%, transparent 50%),
    radial-gradient(ellipse at center, rgba(236, 72, 153, 0.05) 0%, transparent 50%);
`;

// 卡片組件
export const Card = ({
  children,
  icon,
  iconColor = 'cyan',
  title,
  status,
  animated = true,
  hoverable = true,
  ...props
}) => {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <CardContainer
      animated={animated}
      hoverable={hoverable}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      {...props}
    >
      <GlowLine isVisible={isHovered} />
      {(title || icon) && (
        <CardHeader>
          {title && (
            <CardTitle>
              {icon && <CardIcon color={iconColor}>{icon}</CardIcon>}
              {title}
            </CardTitle>
          )}
          {status && <StatusIndicator {...status} />}
        </CardHeader>
      )}
      <CardContent>{children}</CardContent>
    </CardContainer>
  );
};

const CardContainer = styled.div`
  background: rgba(${theme.colors.primary.secondary}, 0.6);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(${theme.colors.neon.cyan}, 0.1);
  border-radius: ${theme.borderRadius.xl};
  padding: ${theme.spacing.xl};
  position: relative;
  overflow: hidden;
  transition: all ${theme.transitions.normal};
  animation: ${animated => animated ? fadeIn : 'none'} 0.6s ease forwards;

  ${hoverable => hoverable && css`
    &:hover {
      transform: translateY(-5px);
      border-color: rgba(${theme.colors.neon.cyan}, 0.3);
      box-shadow: ${theme.shadows.cardHover};
    }
  `}
`;

const GlowLine = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, ${theme.colors.neon.cyan}, transparent);
  opacity: ${props => props.isVisible ? 1 : 0};
  transition: opacity ${theme.transitions.normal};
`;

const CardHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: ${theme.spacing.lg};
`;

const CardTitle = styled.h3`
  font-family: ${theme.fonts.display};
  font-size: 1.125rem;
  font-weight: 600;
  color: ${theme.colors.gray[100]};
  display: flex;
  align-items: center;
  gap: ${theme.spacing.sm};
`;

const CardIcon = styled.div`
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: ${theme.borderRadius.lg};
  font-size: 1.25rem;
  background: rgba(${props => theme.colors.neon[props.color]}, 0.1);
  color: ${props => theme.colors.neon[props.color]};
`;

const CardContent = styled.div``;

// 狀態指示器
export const StatusIndicator = ({ status, text, animated = true }) => {
  return (
    <StatusContainer status={status}>
      <StatusDot animated={animated} />
      <StatusText>{text || status}</StatusText>
    </StatusContainer>
  );
};

const StatusContainer = styled.div`
  display: inline-flex;
  align-items: center;
  gap: ${theme.spacing.sm};
  padding: ${theme.spacing.xs} ${theme.spacing.sm};
  border-radius: ${theme.borderRadius.lg};
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;

  background: rgba(${props => theme.colors.status[props.status]}, 0.1);
  color: ${props => theme.colors.status[props.status]};
  border: 1px solid rgba(${props => theme.colors.status[props.status]}, 0.3);
`;

const StatusDot = styled.span`
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
  animation: ${props => props.animated ? pulse : 'none'} 2s ease-in-out infinite;
`;

const StatusText = styled.span`
  font-family: ${theme.fonts.body};
`;

// 統計數據組件
export const StatItem = ({ label, value, color, trend, icon }) => {
  return (
    <StatContainer>
      <StatLabel>{label}</StatLabel>
      <StatValue color={color}>
        {icon && <StatIcon>{icon}</StatIcon>}
        {value}
        {trend && <StatTrend trend={trend}>{trend > 0 ? '+' : ''}{trend}%</StatTrend>}
      </StatValue>
    </StatContainer>
  );
};

const StatContainer = styled.div`
  display: flex;
  flex-direction: column;
  padding: ${theme.spacing.md};
  background: rgba(${theme.colors.primary.tertiary}, 0.5);
  border-radius: ${theme.borderRadius.lg};
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: all ${theme.transitions.normal};

  &:hover {
    background: rgba(${theme.colors.primary.tertiary}, 0.8);
    border-color: rgba(${theme.colors.neon.cyan}, 0.2);
  }
`;

const StatLabel = styled.span`
  font-size: 0.875rem;
  color: ${theme.colors.gray[500]};
  margin-bottom: ${theme.spacing.xs};
  font-weight: 500;
`;

const StatValue = styled.div`
  font-family: ${theme.fonts.display};
  font-size: 1.5rem;
  font-weight: 700;
  color: ${props => props.color || theme.colors.gray[100]};
  display: flex;
  align-items: center;
  gap: ${theme.spacing.xs};
`;

const StatIcon = styled.span`
  font-size: 1rem;
`;

const StatTrend = styled.span`
  font-size: 0.875rem;
  color: ${props => props.trend > 0 ? theme.colors.status.success : theme.colors.status.error};
`;

// 按鈕組件
export const Button = ({
  children,
  variant = 'primary',
  size = 'medium',
  icon,
  loading = false,
  animated = true,
  onClick,
  ...props
}) => {
  return (
    <StyledButton
      variant={variant}
      size={size}
      animated={animated}
      onClick={onClick}
      disabled={loading}
      {...props}
    >
      {loading ? <ButtonLoader /> : icon && <ButtonIcon>{icon}</ButtonIcon>}
      {children}
      {animated && <ButtonRipple />}
    </StyledButton>
  );
};

const StyledButton = styled.button`
  display: inline-flex;
  align-items: center;
  gap: ${theme.spacing.sm};
  padding: ${props => {
    switch (props.size) {
      case 'small': return `${theme.spacing.sm} ${theme.spacing.md}`;
      case 'large': return `${theme.spacing.lg} ${theme.spacing.xl}`;
      default: return `${theme.spacing.md} ${theme.spacing.lg}`;
    }
  }};
  border: none;
  border-radius: ${theme.borderRadius.md};
  font-family: ${theme.fonts.body};
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: all ${theme.transitions.normal};
  position: relative;
  overflow: hidden;

  ${props => {
    switch (props.variant) {
      case 'primary':
        return css`
          background: linear-gradient(135deg, ${theme.colors.neon.cyan}, ${theme.colors.neon.purple});
          color: white;
          box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3);

          &:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 212, 255, 0.4);
          }
        `;
      case 'secondary':
        return css`
          background: rgba(${theme.colors.primary.tertiary}, 0.8);
          color: ${theme.colors.neon.cyan};
          border: 1px solid rgba(${theme.colors.neon.cyan}, 0.3);

          &:hover:not(:disabled) {
            background: rgba(${theme.colors.neon.cyan}, 0.1);
            border-color: ${theme.colors.neon.cyan};
            box-shadow: 0 4px 15px rgba(0, 212, 255, 0.2);
          }
        `;
      case 'ghost':
        return css`
          background: transparent;
          color: ${theme.colors.gray[300]};

          &:hover:not(:disabled) {
            background: rgba(${theme.colors.neon.cyan}, 0.1);
            color: ${theme.colors.neon.cyan};
          }
        `;
      default:
        return '';
    }
  }}

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const ButtonIcon = styled.span`
  font-size: 1rem;
`;

const ButtonLoader = styled.div`
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top: 2px solid currentColor;
  border-radius: 50%;
  animation: spin 1s linear infinite;

  @keyframes spin {
    to { transform: rotate(360deg); }
  }
`;

const ButtonRipple = styled.span`
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s;
`;

// 圖表容器組件
export const ChartContainer = ({
  title,
  subtitle,
  actions,
  height = 300,
  children
}) => {
  return (
    <ChartWrapper>
      {(title || subtitle || actions) && (
        <ChartHeader>
          <ChartTitleSection>
            {title && <ChartTitle>{title}</ChartTitle>}
            {subtitle && <ChartSubtitle>{subtitle}</ChartSubtitle>}
          </ChartTitleSection>
          {actions && <ChartActions>{actions}</ChartActions>}
        </ChartHeader>
      )}
      <ChartContent height={height}>{children}</ChartContent>
    </ChartWrapper>
  );
};

const ChartWrapper = styled.div`
  background: rgba(${theme.colors.primary.tertiary}, 0.3);
  border-radius: ${theme.borderRadius.lg};
  padding: ${theme.spacing.lg};
  position: relative;
  overflow: hidden;
`;

const ChartHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: ${theme.spacing.lg};
`;

const ChartTitleSection = styled.div``;

const ChartTitle = styled.h3`
  font-family: ${theme.fonts.display};
  font-size: 1.125rem;
  font-weight: 600;
  color: ${theme.colors.gray[100]};
  margin-bottom: ${theme.spacing.xs};
`;

const ChartSubtitle = styled.p`
  color: ${theme.colors.gray[500]};
  font-size: 0.875rem;
`;

const ChartActions = styled.div`
  display: flex;
  gap: ${theme.spacing.sm};
`;

const ChartContent = styled.div`
  height: ${props => props.height}px;
  position: relative;
`;

// 導航欄組件
export const Navbar = ({ brand, links, transparent = false }) => {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 100);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <NavbarContainer scrolled={scrolled} transparent={transparent}>
      <NavbarContent>
        <Brand href="/">
          <BrandIcon>🚀</BrandIcon>
          <BrandText>{brand}</BrandText>
        </Brand>
        <NavLinks>
          {links?.map((link, index) => (
            <NavLink key={index} href={link.href} active={link.active}>
              {link.text}
            </NavLink>
          ))}
        </NavLinks>
      </NavbarContent>
    </NavbarContainer>
  );
};

const NavbarContainer = styled.nav`
  position: fixed;
  width: 100%;
  top: 0;
  z-index: 1000;
  transition: all ${theme.transitions.normal};
  padding: ${theme.spacing.md} 0;
  border-bottom: 1px solid rgba(${theme.colors.neon.cyan}, 0.2);

  background: ${props =>
    props.scrolled
      ? `rgba(${theme.colors.primary.dark}, 0.95)`
      : props.transparent
        ? 'transparent'
        : `rgba(${theme.colors.primary.secondary}, 0.8)`
  };
  backdrop-filter: blur(${props => props.scrolled ? '30px' : '20px'});
`;

const NavbarContent = styled.div`
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 ${theme.spacing.lg};
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const Brand = styled.a`
  font-family: ${theme.fonts.display};
  font-size: 1.5rem;
  font-weight: 700;
  color: ${theme.colors.neon.cyan};
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: ${theme.spacing.sm};
  text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
  transition: transform ${theme.transitions.normal};

  &:hover {
    transform: scale(1.05);
  }
`;

const BrandIcon = styled.span`
  font-size: 1.5rem;
`;

const BrandText = styled.span``;

const NavLinks = styled.ul`
  display: flex;
  gap: ${theme.spacing.xl};
  list-style: none;

  @media (max-width: 768px) {
    display: none;
  }
`;

const NavLink = styled.a`
  color: ${props => props.active ? theme.colors.neon.cyan : theme.colors.gray[400]};
  text-decoration: none;
  font-weight: 500;
  transition: all ${theme.transitions.normal};
  position: relative;
  padding: ${theme.spacing.sm} ${theme.spacing.md};

  &:hover,
  &.active {
    color: ${theme.colors.neon.cyan};
    text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
  }

  &::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: ${props => props.active ? '80%' : '0'};
    height: 2px;
    background: ${theme.colors.neon.cyan};
    transition: width ${theme.transitions.normal};
  }

  &:hover::after {
    width: 80%;
  }
`;

// Hero 區域組件
export const Hero = ({
  title,
  subtitle,
  backgroundImage,
  actions,
  animated = true
}) => {
  return (
    <HeroSection animated={animated}>
      <HeroContent>
        <HeroTitle>{title}</HeroTitle>
        <HeroSubtitle>{subtitle}</HeroSubtitle>
        {actions && <HeroActions>{actions}</HeroActions>}
      </HeroContent>
    </HeroSection>
  );
};

const HeroSection = styled.section`
  padding: ${theme.spacing['3xl']} 0;
  text-align: center;
  position: relative;
  overflow: hidden;
  animation: ${props => props.animated ? fadeIn : 'none'} 0.8s ease;
`;

const HeroContent = styled.div`
  max-width: 800px;
  margin: 0 auto;
  padding: 0 ${theme.spacing.lg};
`;

const HeroTitle = styled.h1`
  font-family: ${theme.fonts.display};
  font-size: clamp(2.5rem, 8vw, 5rem);
  font-weight: 900;
  background: linear-gradient(135deg, ${theme.colors.neon.cyan}, ${theme.colors.neon.purple}, ${theme.colors.neon.pink});
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: ${theme.spacing.lg};
  text-shadow: 0 0 40px rgba(0, 212, 255, 0.3);
  animation: ${glow} 3s ease-in-out infinite alternate;
`;

const HeroSubtitle = styled.p`
  font-size: 1.25rem;
  color: ${theme.colors.gray[400]};
  max-width: 600px;
  margin: 0 auto ${theme.spacing['2xl']};
  line-height: 1.8;
`;

const HeroActions = styled.div`
  display: flex;
  gap: ${theme.spacing.md};
  justify-content: center;
  flex-wrap: wrap;
`;

// 儀表板網格組件
export const DashboardGrid = ({ children, columns = 'auto-fit' }) => {
  return <DashboardGridContainer columns={columns}>{children}</DashboardGridContainer>;
};

const DashboardGridContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(${props => props.columns}, minmax(320px, 1fr));
  gap: ${theme.spacing.xl};
  padding: 0 ${theme.spacing.lg};
  max-width: 1400px;
  margin: 0 auto;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    padding: 0 ${theme.spacing.md};
  }
`;

// 工具提示組件
export const Tooltip = ({ children, text, position = 'top' }) => {
  const [visible, setVisible] = useState(false);

  return (
    <TooltipContainer
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
    >
      {children}
      <TooltipContent visible={visible} position={position}>
        {text}
      </TooltipContent>
    </TooltipContainer>
  );
};

const TooltipContainer = styled.div`
  position: relative;
  display: inline-block;
  cursor: help;
`;

const TooltipContent = styled.div`
  position: absolute;
  ${props => {
    switch (props.position) {
      case 'top':
        return `
          bottom: 100%;
          left: 50%;
          transform: translateX(-50%);
          margin-bottom: 8px;
        `;
      case 'bottom':
        return `
          top: 100%;
          left: 50%;
          transform: translateX(-50%);
          margin-top: 8px;
        `;
      case 'left':
        return `
          right: 100%;
          top: 50%;
          transform: translateY(-50%);
          margin-right: 8px;
        `;
      case 'right':
        return `
          left: 100%;
          top: 50%;
          transform: translateY(-50%);
          margin-left: 8px;
        `;
      default:
        return '';
    }
  }}
  background: ${theme.colors.gray[900]};
  color: ${theme.colors.gray[100]};
  padding: ${theme.spacing.sm};
  border-radius: ${theme.borderRadius.sm};
  font-size: 0.75rem;
  white-space: nowrap;
  opacity: ${props => props.visible ? 1 : 0};
  pointer-events: none;
  transition: opacity ${theme.transitions.normal};
  z-index: 1000;
`;

// 骨架屏組件
export const Skeleton = ({
  width = '100%',
  height = '1rem',
  animated = true,
  borderRadius = theme.borderRadius.md
}) => {
  return <SkeletonContainer width={width} height={height} animated={animated} borderRadius={borderRadius} />;
};

const SkeletonContainer = styled.div`
  width: ${props => props.width};
  height: ${props => props.height};
  border-radius: ${props => props.borderRadius};
  background: linear-gradient(90deg,
    rgba(${theme.colors.primary.tertiary}, 0.5),
    rgba(${theme.colors.primary.tertiary}, 0.8),
    rgba(${theme.colors.primary.tertiary}, 0.5)
  );
  background-size: 200% 100%;
  animation: ${props => props.animated ? 'skeleton-loading 1.5s ease-in-out infinite' : 'none'};

  @keyframes skeleton-loading {
    0% {
      background-position: 200% 0;
    }
    100% {
      background-position: -200% 0;
    }
  }
`;

// 自定義Hook
export const useScrollEffect = (callback, threshold = 100) => {
  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > threshold) {
        callback(true);
      } else {
        callback(false);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [callback, threshold]);
};

export const useWindowSize = () => {
  const [windowSize, setWindowSize] = useState({
    width: window.innerWidth,
    height: window.innerHeight,
  });

  useEffect(() => {
    const handleResize = () => {
      setWindowSize({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return windowSize;
};

export const useIntersectionObserver = (ref, options = {}) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const currentRef = ref.current;
    if (!currentRef) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsVisible(entry.isIntersecting);
      },
      { threshold: 0.1, ...options }
    );

    observer.observe(currentRef);
    return () => {
      observer.unobserve(currentRef);
    };
  }, [ref, options]);

  return isVisible;
};

// 工具函數
export const animateNumber = (start, end, duration, callback) => {
  const startTime = performance.now();
  const change = end - start;

  const animate = (currentTime) => {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);

    const value = start + (change * progress);
    callback(Math.round(value));

    if (progress < 1) {
      requestAnimationFrame(animate);
    }
  };

  requestAnimationFrame(animate);
};

export const formatCurrency = (amount, currency = 'USD') => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
};

export const formatPercentage = (value, decimals = 1) => {
  return `${value >= 0 ? '+' : ''}${value.toFixed(decimals)}%`;
};

export const getColorForValue = (value, thresholds = { positive: 0, negative: 0 }) => {
  if (value > thresholds.positive) return theme.colors.status.success;
  if (value < thresholds.negative) return theme.colors.status.error;
  return theme.colors.gray[100];
};