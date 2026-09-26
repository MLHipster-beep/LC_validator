import { FileText } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import type { IdentifiedDocument } from "@/lib/types"

const LABELS: Record<string, string> = {
  LC: "Letter of Credit",
  LC_DRAFT: "LC Draft",
  LC_INSTRUCTION: "LC Instruction",
  Invoice: "Commercial Invoice",
  BOL: "Bill of Lading",
  PL: "Packing List",
  Insurance: "Insurance",
  CO: "Certificate of Origin",
  Other: "Other",
}

const PRIMARY = new Set(["LC", "Invoice"])

export function DocumentList({ documents }: { documents: IdentifiedDocument[] }) {
  return (
    <ul className="divide-y">
      {documents.map((d, i) => (
        <li key={`${d.filename}-${i}`} className="flex items-center gap-3 py-2.5 first:pt-0 last:pb-0">
          <FileText className="size-4 shrink-0 text-muted-foreground" />
          <span className="min-w-0 flex-1 truncate text-sm">{d.filename}</span>
          <Badge variant={PRIMARY.has(d.doc_type) ? "default" : "secondary"}>
            {LABELS[d.doc_type] ?? d.doc_type}
          </Badge>
        </li>
      ))}
    </ul>
  )
}
