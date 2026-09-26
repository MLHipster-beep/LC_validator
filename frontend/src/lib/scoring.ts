import type { Discrepancy, Severity } from "./types"

/** Mirrors backend/compare.py `result()` so re-scoring after "ignore" is instant. */
export const SEVERITY_PENALTY: Record<Severity, number> = {
  CRITICAL: 100,
  HIGH: 40,
  LOW: 5,
}

export const PASS_THRESHOLD = 85

export function scoreDiscrepancies(items: Discrepancy[]) {
  const penalty = items.reduce((sum, d) => sum + (SEVERITY_PENALTY[d.severity] ?? 0), 0)
  const score = Math.max(0, 100 - penalty)
  return { score, status: score >= PASS_THRESHOLD ? ("PASS" as const) : ("FAIL" as const) }
}

export const SEVERITY_ORDER: Severity[] = ["CRITICAL", "HIGH", "LOW"]
