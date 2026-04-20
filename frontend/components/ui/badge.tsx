import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground",
        secondary: "border-transparent bg-secondary text-secondary-foreground",
        destructive: "border-transparent bg-destructive text-destructive-foreground",
        outline: "border-border text-foreground",
        gold: "border-transparent bg-lymo-gold-500/15 text-lymo-gold-400 border-lymo-gold-500/40",
        vermilion: "border-transparent bg-lymo-vermilion-500/15 text-lymo-vermilion-300 border-lymo-vermilion-500/40",
        stellar: "border-transparent bg-lymo-stellar-500/15 text-lymo-stellar-400 border-lymo-stellar-500/40",
        jade: "border-transparent bg-lymo-jade-500/15 text-lymo-jade-400 border-lymo-jade-500/40",
        ghost: "border-border bg-transparent text-muted-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
