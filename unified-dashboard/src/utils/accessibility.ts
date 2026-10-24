// 可访问性工具函数

export const generateId = (prefix: string = 'id') => {
  return `${prefix}-${Math.random().toString(36).substr(2, 9)}`
}

export const announceToScreenReader = (message: string) => {
  // 创建一个临时的 aria-live 区域来向屏幕阅读器宣告消息
  const announcement = document.createElement('div')
  announcement.setAttribute('aria-live', 'polite')
  announcement.setAttribute('aria-atomic', 'true')
  announcement.className = 'sr-only'
  announcement.textContent = message

  document.body.appendChild(announcement)

  // 一段时间后移除该元素
  setTimeout(() => {
    document.body.removeChild(announcement)
  }, 1000)
}

// 键盘导航工具
export const trapFocus = (element: HTMLElement) => {
  const focusableElements = element.querySelectorAll(
    'a[href], button:not([disabled]), textarea:not([disabled]), input[type="text"]:not([disabled]), input[type="radio"]:not([disabled]), input[type="checkbox"]:not([disabled]), select:not([disabled])'
  ) as NodeListOf<HTMLElement>

  const firstFocusableElement = focusableElements[0]
  const lastFocusableElement = focusableElements[focusableElements.length - 1]

  const handleKeyDown = (event: KeyboardEvent) => {
    if (event.key === 'Tab') {
      if (event.shiftKey) {
        // Shift + Tab
        if (document.activeElement === firstFocusableElement) {
          lastFocusableElement.focus()
          event.preventDefault()
        }
      } else {
        // Tab
        if (document.activeElement === lastFocusableElement) {
          firstFocusableElement.focus()
          event.preventDefault()
        }
      }
    }
  }

  element.addEventListener('keydown', handleKeyDown)

  return () => {
    element.removeEventListener('keydown', handleKeyDown)
  }
}

// 颜色对比度检查
export const getContrastRatio = (color1: string, color2: string): number => {
  const getLuminance = (color: string): number => {
    // 移除 # 号
    const hex = color.replace('#', '')

    // 转换为 RGB
    const r = parseInt(hex.substr(0, 2), 16) / 255
    const g = parseInt(hex.substr(2, 2), 16) / 255
    const b = parseInt(hex.substr(4, 2), 16) / 255

    // 计算相对亮度
    const sRGB = [r, g, b].map(value => {
      return value <= 0.03928 ? value / 12.92 : Math.pow((value + 0.055) / 1.055, 2.4)
    })

    return 0.2126 * sRGB[0] + 0.7152 * sRGB[1] + 0.0722 * sRGB[2]
  }

  const lum1 = getLuminance(color1)
  const lum2 = getLuminance(color2)

  const brightest = Math.max(lum1, lum2)
  const darkest = Math.min(lum1, lum2)

  return (brightest + 0.05) / (darkest + 0.05)
}

export const meetsWCAGAA = (contrastRatio: number): boolean => {
  return contrastRatio >= 4.5
}

export const meetsWCAGAAA = (contrastRatio: number): boolean => {
  return contrastRatio >= 7
}

// 跳过链接
export const createSkipLink = (targetId: string, text: string = '跳到主要内容'): HTMLElement => {
  const skipLink = document.createElement('a')
  skipLink.href = `#${targetId}`
  skipLink.textContent = text
  skipLink.className = 'sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-primary-600 text-white px-4 py-2 rounded-md z-50'

  return skipLink
}

// 焦点管理
export const restoreFocus = (element: HTMLElement) => {
  element.focus()
}

export const removeFocus = () => {
  if (document.activeElement && document.activeElement instanceof HTMLElement) {
    document.activeElement.blur()
  }
}

// ARIA 属性辅助函数
export const getAriaAttributes = (options: {
  label?: string
  labelledby?: string
  describedby?: string
  expanded?: boolean
  selected?: boolean
  disabled?: boolean
  required?: boolean
  invalid?: boolean
  hidden?: boolean
}) => {
  const attributes: Record<string, string | boolean> = {}

  if (options.label) attributes['aria-label'] = options.label
  if (options.labelledby) attributes['aria-labelledby'] = options.labelledby
  if (options.describedby) attributes['aria-describedby'] = options.describedby
  if (options.expanded !== undefined) attributes['aria-expanded'] = options.expanded
  if (options.selected !== undefined) attributes['aria-selected'] = options.selected
  if (options.disabled !== undefined) attributes['aria-disabled'] = options.disabled
  if (options.required !== undefined) attributes['aria-required'] = options.required
  if (options.invalid !== undefined) attributes['aria-invalid'] = options.invalid
  if (options.hidden !== undefined) attributes['aria-hidden'] = options.hidden

  return attributes
}