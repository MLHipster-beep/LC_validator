"use client"

import { FileText, ImageIcon, UploadCloud, X } from "lucide-react"
import { useCallback, useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const ACCEPT = ["application/pdf", "image/png", "image/jpeg", "image/webp"]
const MAX_MB = 15

function formatSize(bytes: number) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

interface DropzoneProps {
  files: File[]
  onChange: (files: File[]) => void
  onReject: (reason: string) => void
  disabled?: boolean
}

export function Dropzone({ files, onChange, onReject, disabled }: DropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)

  const addFiles = useCallback(
    (incoming: FileList | null) => {
      if (!incoming) return
      const next = [...files]
      for (const f of Array.from(incoming)) {
        if (!ACCEPT.includes(f.type)) {
          onReject(`${f.name}: only PDF, PNG, JPG or WEBP files are supported.`)
          continue
        }
        if (f.size > MAX_MB * 1024 * 1024) {
          onReject(`${f.name} is larger than ${MAX_MB} MB.`)
          continue
        }
        if (next.some((x) => x.name === f.name && x.size === f.size)) continue
        next.push(f)
      }
      onChange(next)
    },
    [files, onChange, onReject],
  )

  return (
    <div className="space-y-3">
      <button
        type="button"
        disabled={disabled}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault()
          if (!disabled) setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragging(false)
          if (!disabled) addFiles(e.dataTransfer.files)
        }}
        className={cn(
          "group relative flex w-full flex-col items-center justify-center gap-3 rounded-xl border border-dashed px-6 py-12 text-center transition-colors",
          "hover:border-foreground/30 hover:bg-muted/40 focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none",
          "disabled:pointer-events-none disabled:opacity-60",
          dragging && "border-foreground/40 bg-muted/60",
        )}
      >
        <div className="flex size-11 items-center justify-center rounded-full border bg-background shadow-xs transition-transform group-hover:-translate-y-0.5">
          <UploadCloud className="size-5 text-muted-foreground" />
        </div>
        <div className="space-y-1">
          <p className="text-sm font-medium">
            Drop trade documents here, or <span className="underline underline-offset-4">browse</span>
          </p>
          <p className="text-xs text-muted-foreground">
            LC, Commercial Invoice, BOL, Packing List, Bi.Bi.Ni. · PDF or image · up to {MAX_MB} MB each
          </p>
        </div>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPT.join(",")}
          className="sr-only"
          onChange={(e) => {
            addFiles(e.target.files)
            e.target.value = ""
          }}
        />
      </button>

      {files.length > 0 && (
        <ul className="divide-y rounded-xl border">
          {files.map((f, i) => {
            const Icon = f.type === "application/pdf" ? FileText : ImageIcon
            return (
              <li key={`${f.name}-${i}`} className="flex items-center gap-3 px-3 py-2.5">
                <div className="flex size-8 shrink-0 items-center justify-center rounded-md bg-muted">
                  <Icon className="size-4 text-muted-foreground" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{f.name}</p>
                  <p className="text-xs text-muted-foreground">{formatSize(f.size)}</p>
                </div>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  aria-label={`Remove ${f.name}`}
                  disabled={disabled}
                  onClick={() => onChange(files.filter((_, idx) => idx !== i))}
                >
                  <X />
                </Button>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
