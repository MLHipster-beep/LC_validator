import { cn } from "@/lib/utils"
import type { Severity } from "@/lib/types"

const STYLES: Record<Severity, string> = {
  CRITICAL: "bg-red-500/10 text-red-700 ring-red-500/20 dark:text-red-400",
  HIGH: "bg-amber-500/10 text-amber-700 ring-amber-500/20 dark:text-amber-400",
  LOW: "bg-sky-500/10 text-sky-700 ring-sky-500/20 dark:text-sky-400",
}

const DOT: Record<Severity, string> = {
  CRITICAL: "bg-red-500",
  HIGH: "bg-amber-500",
  LOW: "bg-sky-500",
}

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-medium tracking-wide ring-1 ring-inset",
        STYLES[severity],
      )}
    >
      <span className={cn("size-1.5 rounded-full", DOT[severity])} />
      {severity}
    </span>
  )
}
