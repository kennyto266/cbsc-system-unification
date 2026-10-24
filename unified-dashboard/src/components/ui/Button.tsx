import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary-600 text-white hover:bg-primary-700",
        destructive:
          "bg-error-600 text-white hover:bg-error-700",
        outline:
          "border border-gray-300 bg-background hover:bg-accent hover:text-accent-foreground",
        secondary:
          "bg-gray-100 text-gray-900 hover:bg-gray-200",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary-600 underline-offset-4 hover:underline",
        // CBSC specific variants
        cbsc: "bg-gradient-to-r from-primary-500 to-cbsc-cyan text-white hover:from-primary-600 hover:to-cbsc-cyan/90 shadow-lg",
        cbscOutline: "border-2 border-primary-500 text-primary-500 hover:bg-primary-500 hover:text-white",
        success: "bg-green-600 text-white hover:bg-green-700",
        danger: "bg-red-600 text-white hover:bg-red-700",
        warning: "bg-yellow-600 text-white hover:bg-yellow-700",
        info: "bg-blue-600 text-white hover:bg-blue-700",

        // Financial trading variants
        bullish: "bg-green-500 text-white hover:bg-green-600 border border-green-600",
        bearish: "bg-red-500 text-white hover:bg-red-600 border border-red-600",
        neutral: "bg-gray-500 text-white hover:bg-gray-600 border border-gray-600",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
        xs: "h-8 rounded px-2 text-xs",
        xl: "h-12 rounded-lg px-10 text-base",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
  loading?: boolean
  icon?: React.ReactNode
  iconPosition?: 'left' | 'right'
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, loading = false, icon, iconPosition = 'left', children, disabled, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"

    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={disabled || loading}
        {...props}
      >
        {loading && (
          <svg
            className="animate-spin -ml-1 mr-3 h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            ></circle>
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
        )}

        {!loading && icon && iconPosition === 'left' && (
          <span className="mr-2">{icon}</span>
        )}

        <span>{children}</span>

        {!loading && icon && iconPosition === 'right' && (
          <span className="ml-2">{icon}</span>
        )}
      </Comp>
    )
  }
)
Button.displayName = "Button"

// CBSC-specific button presets
export const TradingButton = {
  Buy: (props: Omit<ButtonProps, 'variant' | 'children'>) => (
    <Button variant="bullish" {...props}>
      買入 {props.icon && <span className="ml-1">{props.icon}</span>}
    </Button>
  ),

  Sell: (props: Omit<ButtonProps, 'variant' | 'children'>) => (
    <Button variant="bearish" {...props}>
      賣出 {props.icon && <span className="ml-1">{props.icon}</span>}
    </Button>
  ),

  Hold: (props: Omit<ButtonProps, 'variant' | 'children'>) => (
    <Button variant="neutral" {...props}>
      持有 {props.icon && <span className="ml-1">{props.icon}</span>}
    </Button>
  ),
}

export const ActionButton = {
  Create: (props: Omit<ButtonProps, 'variant' | 'children'>) => (
    <Button variant="success" {...props}>
      創建
    </Button>
  ),

  Delete: (props: Omit<ButtonProps, 'variant' | 'children'>) => (
    <Button variant="danger" {...props}>
      刪除
    </Button>
  ),

  Edit: (props: Omit<ButtonProps, 'variant' | 'children'>) => (
    <Button variant="warning" {...props}>
      編輯
    </Button>
  ),

  View: (props: Omit<ButtonProps, 'variant' | 'children'>) => (
    <Button variant="info" {...props}>
      查看
    </Button>
  ),
}

export { Button, buttonVariants }