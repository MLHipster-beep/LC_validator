import type { LeadPayload, ValidateResponse } from "./types"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

async function parseError(res: Response): Promise<string> {
  try {
    const body = await res.json()
    return typeof body?.detail === "string" ? body.detail : `Request failed (${res.status})`
  } catch {
    return `Request failed (${res.status})`
  }
}

export async function validateDocuments(files: File[], signal?: AbortSignal): Promise<ValidateResponse> {
  const form = new FormData()
  files.forEach((f) => form.append("files", f))

  const res = await fetch(`${API_URL}/api/validate`, { method: "POST", body: form, signal })
  if (!res.ok) throw new Error(await parseError(res))

  const data = (await res.json()) as ValidateResponse
  return { documents: data.documents ?? [], report: data.report ?? null, warning: data.warning ?? null }
}

export async function submitLead(payload: LeadPayload): Promise<void> {
  const res = await fetch(`${API_URL}/api/leads`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(await parseError(res))
}
