"use client"

import { AlertTriangle, ArrowRight, Loader2, RotateCcw } from "lucide-react"
import { useRef, useState } from "react"
import { toast } from "sonner"
import { AnalysisProgress } from "@/components/analysis-progress"
import { DiscrepancyReport } from "@/components/discrepancy-report"
import { DocumentList } from "@/components/document-list"
import { Dropzone } from "@/components/dropzone"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { validateDocuments } from "@/lib/api"
import type { ValidateResponse } from "@/lib/types"

type Status = "idle" | "loading" | "done" | "error"

export function Validator() {
  const [files, setFiles] = useState<File[]>([])
  const [status, setStatus] = useState<Status>("idle")
  const [result, setResult] = useState<ValidateResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  async function run() {
    if (files.length === 0) return
    abortRef.current?.abort()
    const ctrl = new AbortController()
    abortRef.current = ctrl

    setStatus("loading")
    setError(null)
    setResult(null)
    try {
      const data = await validateDocuments(files, ctrl.signal)
      setResult(data)
      setStatus("done")
    } catch (err) {
      if (ctrl.signal.aborted) return
      const msg = err instanceof Error ? err.message : "Something went wrong."
      setError(msg)
      setStatus("error")
      toast.error(msg)
    }
  }

  function reset() {
    abortRef.current?.abort()
    setFiles([])
    setResult(null)
    setError(null)
    setStatus("idle")
  }

  const loading = status === "loading"

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Upload documents</CardTitle>
          <CardDescription>
            Include at least the issued <span className="font-medium text-foreground">Letter of Credit</span> and the{" "}
            <span className="font-medium text-foreground">Commercial Invoice</span>.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {loading ? (
            <div className="rounded-xl border bg-muted/30 p-6">
              <AnalysisProgress />
            </div>
          ) : (
            <Dropzone files={files} onChange={setFiles} onReject={(r) => toast.error(r)} disabled={loading} />
          )}
          <div className="flex items-center justify-end gap-2">
            {(files.length > 0 || result) && (
              <Button variant="ghost" onClick={reset}>
                <RotateCcw /> Start over
              </Button>
            )}
            <Button size="lg" onClick={run} disabled={files.length === 0 || loading}>
              {loading ? <Loader2 className="animate-spin" /> : null}
              {loading ? "Analyzing…" : result ? "Re-run check" : "Validate documents"}
              {!loading && <ArrowRight />}
            </Button>
          </div>
        </CardContent>
      </Card>

      {status === "error" && error && (
        <div className="flex items-start gap-3 rounded-xl border border-red-500/30 bg-red-500/5 p-4 text-sm">
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-red-500" />
          <div>
            <p className="font-medium">Validation failed</p>
            <p className="text-muted-foreground">{error}</p>
          </div>
        </div>
      )}

      {result && (
        <div className="animate-in fade-in slide-in-from-bottom-2 space-y-4 duration-500">
          {result.documents.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Identified documents</CardTitle>
                <CardDescription>Classified automatically from the uploaded files.</CardDescription>
              </CardHeader>
              <CardContent>
                <DocumentList documents={result.documents} />
              </CardContent>
            </Card>
          )}

          {result.warning && (
            <div className="flex items-start gap-3 rounded-xl border border-amber-500/30 bg-amber-500/5 p-4 text-sm">
              <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-500" />
              <p>{result.warning}</p>
            </div>
          )}

          {result.report && <DiscrepancyReport key={result.report.score + result.report.discrepancies.length} report={result.report} />}
        </div>
      )}
    </div>
  )
}
