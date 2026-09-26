"use client"

import { CheckCircle2, Download, EyeOff, RotateCcw, XCircle } from "lucide-react"
import { useMemo, useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ScoreRing } from "@/components/score-ring"
import { SeverityBadge } from "@/components/severity-badge"
import { PASS_THRESHOLD, scoreDiscrepancies, SEVERITY_ORDER } from "@/lib/scoring"
import type { Discrepancy, ValidationReport } from "@/lib/types"
import { cn } from "@/lib/utils"

function exportCsv(rows: Discrepancy[], ignored: Set<number>) {
  const esc = (s: string) => `"${s.replace(/"/g, '""')}"`
  const lines = [
    "field,severity,message,ignored",
    ...rows.map((d, i) => [esc(d.field), d.severity, esc(d.message), ignored.has(i)].join(",")),
  ]
  const blob = new Blob([lines.join("\n")], { type: "text/csv" })
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = "lc-discrepancy-report.csv"
  a.click()
  URL.revokeObjectURL(url)
}

export function DiscrepancyReport({ report }: { report: ValidationReport }) {
  const [ignored, setIgnored] = useState<Set<number>>(new Set())

  // Sort by severity once; keep original index as a stable id for the ignore set.
  const rows = useMemo(
    () =>
      report.discrepancies
        .map((d, i) => ({ ...d, id: i }))
        .sort((a, b) => SEVERITY_ORDER.indexOf(a.severity) - SEVERITY_ORDER.indexOf(b.severity)),
    [report.discrepancies],
  )

  const active = rows.filter((r) => !ignored.has(r.id))
  const { score, status } = scoreDiscrepancies(active)
  const pass = status === "PASS"

  const counts = SEVERITY_ORDER.map((s) => ({ s, n: active.filter((d) => d.severity === s).length }))

  const toggle = (id: number) =>
    setIgnored((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })

  return (
    <div className="space-y-4">
      {/* Summary */}
      <Card>
        <CardContent className="flex flex-col gap-6 sm:flex-row sm:items-center">
          <ScoreRing score={score} pass={pass} />
          <div className="flex-1 space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              {pass ? (
                <CheckCircle2 className="size-5 text-emerald-500" />
              ) : (
                <XCircle className="size-5 text-red-500" />
              )}
              <h2 className="text-lg font-semibold tracking-tight">
                {pass ? "Likely to be accepted" : "Likely to be rejected by the bank"}
              </h2>
              <Badge
                className={cn(
                  "ml-1",
                  pass
                    ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400"
                    : "bg-red-500/10 text-red-700 dark:text-red-400",
                )}
              >
                {status}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground">
              {active.length === 0
                ? "No active discrepancies between the LC and the invoice."
                : `${active.length} active discrepanc${active.length === 1 ? "y" : "ies"} found. A score of ${PASS_THRESHOLD}+ is required to pass.`}
              {ignored.size > 0 && ` ${ignored.size} ignored.`}
            </p>
            <div className="flex flex-wrap gap-2">
              {counts.map(({ s, n }) => (
                <span key={s} className="inline-flex items-center gap-2 rounded-md border px-2 py-1 text-xs">
                  <SeverityBadge severity={s} />
                  <span className="tabular-nums font-medium">{n}</span>
                </span>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      {rows.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Discrepancies</CardTitle>
            <CardDescription>
              Tick a row to ignore it (e.g. if the bank has agreed to waive it). The score updates instantly.
            </CardDescription>
            <CardAction className="flex gap-2">
              {ignored.size > 0 && (
                <Button variant="ghost" size="sm" onClick={() => setIgnored(new Set())}>
                  <RotateCcw /> Reset
                </Button>
              )}
              <Button variant="outline" size="sm" onClick={() => exportCsv(report.discrepancies, ignored)}>
                <Download /> Export CSV
              </Button>
            </CardAction>
          </CardHeader>
          <CardContent className="px-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12 pl-4">
                    <EyeOff className="size-3.5" aria-label="Ignore" />
                  </TableHead>
                  <TableHead className="w-44">Field</TableHead>
                  <TableHead className="w-28">Severity</TableHead>
                  <TableHead>Details</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((d) => {
                  const isIgnored = ignored.has(d.id)
                  return (
                    <TableRow
                      key={d.id}
                      data-state={isIgnored ? "selected" : undefined}
                      className={cn("cursor-pointer", isIgnored && "opacity-50")}
                      onClick={() => toggle(d.id)}
                    >
                      <TableCell className="pl-4" onClick={(e) => e.stopPropagation()}>
                        <Checkbox
                          checked={isIgnored}
                          onCheckedChange={() => toggle(d.id)}
                          aria-label={`Ignore ${d.field}`}
                        />
                      </TableCell>
                      <TableCell className={cn("font-medium", isIgnored && "line-through")}>{d.field}</TableCell>
                      <TableCell>
                        <SeverityBadge severity={d.severity} />
                      </TableCell>
                      <TableCell className="whitespace-normal text-muted-foreground">{d.message}</TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
