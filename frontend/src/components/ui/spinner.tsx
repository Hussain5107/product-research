import { cn } from "@/lib/utils";
import { Skeleton } from "./skeleton";

interface SpinnerProps {
  className?: string;
  size?: "sm" | "md" | "lg";
}

const spinnerVariants = {
  sm: "h-4 w-4 border-2",
  md: "h-6 w-6 border-2",
  lg: "h-8 w-8 border-2",
};

export function Spinner({ className, size = "md" }: SpinnerProps) {
  return (
    <div
      className={cn(
        "animate-spin rounded-full border-2 border-muted-foreground/20 border-t-primary",
        spinnerVariants[size],
        className
      )}
    />
  );
}

export function LoadingCard({ className }: { className?: string }) {
  return (
    <Skeleton className={cn("h-24 rounded-xl", className)} />
  );
}
