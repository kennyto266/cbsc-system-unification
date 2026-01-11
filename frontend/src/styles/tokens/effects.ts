/**
 * CBSC Design System - Effects Tokens
 * 阴影和动效系统设计令牌
 */

// Shadow definitions - 阴影定义
export const shadows = {
  none: 'none',

  // Material Design inspired shadows
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',                           // 2dp
  base: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)', // 4dp
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)', // 8dp
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)', // 12dp
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)', // 16dp
  '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',                  // 24dp

  // Inner shadows
  inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
  innerLg: 'inset 0 4px 8px 0 rgba(0, 0, 0, 0.1)',

  // Colored shadows for depth
  primary: '0 10px 25px -5px rgba(2, 132, 199, 0.25)',
  success: '0 10px 25px -5px rgba(34, 197, 94, 0.25)',
  warning: '0 10px 25px -5px rgba(245, 158, 11, 0.25)',
  error: '0 10px 25px -5px rgba(239, 68, 68, 0.25)',
  info: '0 10px 25px -5px rgba(59, 130, 246, 0.25)',

  // Glow effects - 发光效果
  glow: '0 0 20px rgba(59, 130, 246, 0.3)',
  glowPrimary: '0 0 30px rgba(2, 132, 199, 0.4)',
  glowSuccess: '0 0 30px rgba(34, 197, 94, 0.4)',
  glowWarning: '0 0 30px rgba(245, 158, 11, 0.4)',
  glowError: '0 0 30px rgba(239, 68, 68, 0.4)',
  glowInfo: '0 0 30px rgba(59, 130, 246, 0.4)',

  // Card shadows - 卡片阴影
  card: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  cardHover: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',

  // Button shadows - 按钮阴影
  button: '0 2px 4px rgba(0, 0, 0, 0.1)',
  buttonHover: '0 4px 8px rgba(0, 0, 0, 0.15)',
  buttonActive: '0 1px 2px rgba(0, 0, 0, 0.1) inset',

  // Modal/Dialog shadow - 模态框阴影
  modal: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
  dropdown: '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
}

// Animation durations - 动画持续时间
export const durations = {
  instant: '0ms',
  fast: '150ms',
  normal: '250ms',
  slow: '350ms',
  slower: '500ms',
  slowest: '750ms',
}

// Animation easing curves - 动画缓动曲线
export const easings = {
  // Standard curves
  linear: 'linear',
  ease: 'ease',
  easeIn: 'ease-in',
  easeOut: 'ease-out',
  easeInOut: 'ease-in-out',

  // Material Design curves
  standard: 'cubic-bezier(0.4, 0.0, 0.2, 1)',
  standardDecelerate: 'cubic-bezier(0.0, 0.0, 0.2, 1)',
  standardAccelerate: 'cubic-bezier(0.4, 0.0, 1, 1)',
  emphasis: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
  emphasisDecelerate: 'cubic-bezier(0.05, 0.7, 0.1, 1.0)',
  emphasisAccelerate: 'cubic-bezier(0.3, 0.0, 0.8, 0.15)',

  // Custom curves
  bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  elastic: 'cubic-bezier(0.68, -0.6, 0.32, 1.6)',
}

// Animation keyframes - 动画关键帧
export const keyframes = {
  // Fade animations - 淡入淡出
  fadeIn: {
    from: { opacity: 0 },
    to: { opacity: 1 },
  },
  fadeOut: {
    from: { opacity: 1 },
    to: { opacity: 0 },
  },
  fadeUp: {
    from: { opacity: 0, transform: 'translateY(20px)' },
    to: { opacity: 1, transform: 'translateY(0)' },
  },
  fadeDown: {
    from: { opacity: 0, transform: 'translateY(-20px)' },
    to: { opacity: 1, transform: 'translateY(0)' },
  },
  fadeLeft: {
    from: { opacity: 0, transform: 'translateX(20px)' },
    to: { opacity: 1, transform: 'translateX(0)' },
  },
  fadeRight: {
    from: { opacity: 0, transform: 'translateX(-20px)' },
    to: { opacity: 1, transform: 'translateX(0)' },
  },

  // Scale animations - 缩放动画
  scaleIn: {
    from: { opacity: 0, transform: 'scale(0.9)' },
    to: { opacity: 1, transform: 'scale(1)' },
  },
  scaleOut: {
    from: { opacity: 1, transform: 'scale(1)' },
    to: { opacity: 0, transform: 'scale(0.9)' },
  },
  scaleUp: {
    from: { transform: 'scale(1)' },
    to: { transform: 'scale(1.05)' },
  },
  scaleDown: {
    from: { transform: 'scale(1)' },
    to: { transform: 'scale(0.95)' },
  },

  // Slide animations - 滑动动画
  slideUp: {
    from: { transform: 'translateY(100%)' },
    to: { transform: 'translateY(0)' },
  },
  slideDown: {
    from: { transform: 'translateY(-100%)' },
    to: { transform: 'translateY(0)' },
  },
  slideLeft: {
    from: { transform: 'translateX(100%)' },
    to: { transform: 'translateX(0)' },
  },
  slideRight: {
    from: { transform: 'translateX(-100%)' },
    to: { transform: 'translateX(0)' },
  },

  // Rotation animations - 旋转动画
  spin: {
    from: { transform: 'rotate(0deg)' },
    to: { transform: 'rotate(360deg)' },
  },
  bounce: {
    '0%, 100%': { transform: 'translateY(0)' },
    '50%': { transform: 'translateY(-25%)' },
  },
  pulse: {
    '0%, 100%': { opacity: 1 },
    '50%': { opacity: 0.5 },
  },
  ping: {
    '0%': { transform: 'scale(1)', opacity: 1 },
    '75%, 100%': { transform: 'scale(2)', opacity: 0 },
  },

  // Special animations - 特殊动画
  shake: {
    '0%, 100%': { transform: 'translateX(0)' },
    '10%, 30%, 50%, 70%, 90%': { transform: 'translateX(-10px)' },
    '20%, 40%, 60%, 80%': { transform: 'translateX(10px)' },
  },
  wiggle: {
    '0%, 100%': { transform: 'rotate(-3deg)' },
    '50%': { transform: 'rotate(3deg)' },
  },
  heartbeat: {
    '0%': { transform: 'scale(1)' },
    '14%': { transform: 'scale(1.3)' },
    '28%': { transform: 'scale(1)' },
    '42%': { transform: 'scale(1.3)' },
    '70%': { transform: 'scale(1)' },
  },

  // Loading animations - 加载动画
  loading: {
    '0%': { transform: 'rotate(0deg)' },
    '100%': { transform: 'rotate(360deg)' },
  },
  loadingDots: {
    '0%, 80%, 100%': { transform: 'scale(0)' },
    '40%': { transform: 'scale(1)' },
  },
  shimmer: {
    '0%': { transform: 'translateX(-100%)' },
    '100%': { transform: 'translateX(100%)' },
  },
}

// Animation presets - 动画预设
export const animations = {
  // Entrance animations - 入场动画
  entrance: {
    fadeIn: `${durations.normal} ${easings.standard} ${keyframes.fadeIn}`,
    fadeUp: `${durations.slow} ${easings.emphasisDecelerate} ${keyframes.fadeUp}`,
    scaleIn: `${durations.normal} ${easings.emphasis} ${keyframes.scaleIn}`,
    slideUp: `${durations.slow} ${easings.emphasisDecelerate} ${keyframes.slideUp}`,
    slideDown: `${durations.slow} ${easings.emphasisDecelerate} ${keyframes.slideDown}`,
  },

  // Exit animations - 退场动画
  exit: {
    fadeOut: `${durations.fast} ${easings.standardAccelerate} ${keyframes.fadeOut}`,
    scaleOut: `${durations.fast} ${easings.standard} ${keyframes.scaleOut}`,
  },

  // Attention animations - 注意力动画
  attention: {
    bounce: `${durations.slow} ${easings.bounce} ${keyframes.bounce}`,
    pulse: `${durations.slow} ${easings.standard} ${keyframes.pulse}`,
    shake: `${durations.slow} ${easings.standard} ${keyframes.shake}`,
    wiggle: `${durations.normal} ${easings.bounce} ${keyframes.wiggle}`,
    glow: `${durations.normal} ${easings.standard} both`,
  },

  // Loading animations - 加载动画
  loading: {
    spin: `${durations.slower} ${easings.linear} infinite ${keyframes.spin}`,
    pulse: `${durations.slow} ${easings.standard} infinite ${keyframes.pulse}`,
    bounce: `${durations.slow} ${easings.bounce} infinite ${keyframes.bounce}`,
    dots: `${durations.slow} ${easings.standard} infinite`,
    shimmer: `${durations.slow} ${easings.standard} infinite`,
  },

  // Transition presets - 过渡预设
  transition: {
    // Basic transitions
    fast: `${durations.fast} ${easings.standard}`,
    normal: `${durations.normal} ${easings.standard}`,
    slow: `${durations.slow} ${easings.standard}`,

    // Specific property transitions
    colors: `color ${durations.normal} ${easings.standard}, background-color ${durations.normal} ${easings.standard}, border-color ${durations.normal} ${easings.standard}`,
    opacity: `opacity ${durations.normal} ${easings.standard}`,
    transform: `transform ${durations.normal} ${easings.emphasis}`,
    all: `all ${durations.normal} ${easings.standard}`,

    // Interactive transitions
    button: `all ${durations.fast} ${easings.standard}`,
    hover: `all ${durations.fast} ${easings.standard}`,
    focus: `all ${durations.normal} ${easings.emphasis}`,
    active: `all ${durations.instant} ${easings.standard}`,

    // Component transitions
    modal: `all ${durations.slow} ${easings.emphasisDecelerate}`,
    dropdown: `all ${durations.fast} ${easings.standard}`,
    tooltip: `all ${durations.fast} ${easings.emphasis}`,
    toast: `all ${durations.slow} ${easings.emphasisDecelerate}`,
  },
}

// Blur effects - 模糊效果
export const blurs = {
  none: 'blur(0)',
  sm: 'blur(4px)',
  base: 'blur(8px)',
  md: 'blur(12px)',
  lg: 'blur(16px)',
  xl: 'blur(24px)',
  '2xl': 'blur(40px)',
  '3xl': 'blur(64px)',
}

// Filter effects - 滤镜效果
export const filters = {
  brightness: {
    dim: 'brightness(0.5)',
    normal: 'brightness(1)',
    bright: 'brightness(1.2)',
    brights: 'brightness(1.5)',
  },
  contrast: {
    low: 'contrast(0.5)',
    normal: 'contrast(1)',
    high: 'contrast(1.2)',
    higher: 'contrast(1.5)',
  },
  saturate: {
    desaturated: 'saturate(0)',
    normal: 'saturate(1)',
    saturated: 'saturate(1.5)',
    vivid: 'saturate(2)',
  },
  grayscale: {
    normal: 'grayscale(0)',
    grayscale: 'grayscale(1)',
  },
  sepia: {
    normal: 'sepia(0)',
    sepia: 'sepia(1)',
  },
}

// Export all effect tokens
export const effects = {
  shadows,
  durations,
  easings,
  keyframes,
  animations,
  blurs,
  filters,
}