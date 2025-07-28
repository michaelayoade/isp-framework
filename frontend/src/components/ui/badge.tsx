import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/utils/cn"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive:
          "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
        outline: "text-foreground",
        // Brand-specific status variants
        success:
          "border-transparent bg-success-600 text-white hover:bg-success-700",
        online:
          "border-transparent bg-brand-500 text-white hover:bg-brand-600",
        active:
          "border-transparent bg-brand-600 text-white hover:bg-brand-700",
        connected:
          "border-transparent bg-brand-400 text-brand-900 hover:bg-brand-500",
        available:
          "border-transparent bg-brand-100 text-brand-800 hover:bg-brand-200",
        'success-outline':
          "border-success-200 bg-success-50 text-success-800 hover:bg-success-100",
        'brand-outline':
          "border-brand-200 bg-brand-50 text-brand-800 hover:bg-brand-100",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
