export type Severity = "CRITICAL" | "HIGH" | "LOW"

export type DocType =
  | "LC"
  | "LC_DRAFT"
  | "LC_INSTRUCTION"
  | "Invoice"
  | "BOL"
  | "PL"
  | "Insurance"
  | "CO"
  | "Other"

export interface Discrepancy {
  field: string
  severity: Severity
  message: string
}

export interface IdentifiedDocument {
  filename: string
  doc_type: DocType | string
}

export interface ValidationReport {
  status: "PASS" | "FAIL"
  score: number
  discrepancies: Discrepancy[]
}

export interface ValidateResponse {
  documents: IdentifiedDocument[]
  report: ValidationReport | null
  warning: string | null
}

export interface LeadPayload {
  name: string
  phone: string
  message: string
}
