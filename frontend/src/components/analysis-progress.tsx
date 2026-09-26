"use client"

import { Check, Loader2 } from "lucide-react"
import { useEffect, useState } from "react"
import { cn } from "@/lib/utils"

const STEPS = [
  "Reading documents",
  "Classifying LC, invoice and supporting docs",
  "Extracting fields with Gemini Vision",
  "Checking against UCP 600 rules",
]

/** Visual progress while the single /api/validate request runs (~20–40s). */
export function AnalysisProgress() {
  const [active, setActive] = useState(0)

  useEffect(() => {
    const id = setInterval(() => setActive((s) => Math.min(s + 1, STEPS.length - 1)), 7000)
    return () => clearInterval(id)
  }, [])

  return (
    <ol className="space-y-3" aria-live="polite">
      {STEPS.map((step, i) => {
        const done = i < active
        const current = i === active
        return (
          <li key={step} className="flex items-center gap-3 text-sm">
            <span
              className={cn(
                "flex size-5 shrink-0 items-center justify-center rounded-full border transition-colors",
                done && "border-foreground bg-foreground text-background",
                current && "border-foreground/50",
              )}
            >
              {done ? (
                <Check className="size-3" />
              ) : current ? (
                <Loader2 className="size-3 animate-spin" />
              ) : null}
            </span>
            <span className={cn("transition-colors", done || current ? "text-foreground" : "text-muted-foreground")}>
              {step}
            </span>
          </li>
        )
      })}
    </ol>
  )
}
