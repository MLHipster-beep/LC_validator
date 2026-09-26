import { cn } from "@/lib/utils"

/** Circular score gauge, 0–100. */
export function ScoreRing({ score, pass }: { score: number; pass: boolean }) {
  const r = 42
  const c = 2 * Math.PI * r
  const offset = c - (score / 100) * c

  return (
    <div className="relative size-28 shrink-0">
      <svg viewBox="0 0 100 100" className="size-full -rotate-90">
        <circle cx="50" cy="50" r={r} fill="none" strokeWidth="8" className="stroke-muted" />
        <circle
          cx="50"
          cy="50"
          r={r}
          fill="none"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
          className={cn(
            "transition-[stroke-dashoffset] duration-700 ease-out",
            pass ? "stroke-emerald-500" : "stroke-red-500",
          )}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-semibold tabular-nums tracking-tight">{score}</span>
        <span className="text-[11px] text-muted-foreground">/ 100</span>
      </div>
    </div>
  )
}
