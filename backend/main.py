"""
FastAPI server for LC Validator.

Wraps the existing extraction (Gemini) + comparison logic so the
Next.js frontend can call it over HTTP.

Run locally:
    uvicorn main:app --reload --port 8000
"""

import io
import os
from typing import List, Optional

import requests
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from compare import compare_lc_and_invoice
from extract2 import BatchResponse, DocumentRequirements
from helper_function import get_structured_data_text
from prompt import Prompt_additional_condition
from SendingPdf import process_all_document

GOOGLE_SHEET_URL = os.getenv(
    "LEADS_WEBHOOK_URL",
    "https://script.google.com/macros/s/AKfycbwfm-whN6cgV1SA5ahOaVAlj7bHSkDEtMhIVzCnLtfJfvY3qkUcY0Oz7-IFYqEa4Hkq/exec",
)

ALLOWED_TYPES = {"application/pdf", "image/png", "image/jpeg", "image/webp"}
MAX_FILE_MB = 15

app = FastAPI(title="LC Validator API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


class InMemoryFile(io.BytesIO):
    """Mimics the Streamlit UploadedFile interface (.name, .type, .read, .seek)
    so the existing process_all_document() works unchanged."""

    def __init__(self, data: bytes, name: str, mime_type: str):
        super().__init__(data)
        self.name = name
        self.type = mime_type


# ---------- Response models ----------

class Discrepancy(BaseModel):
    field: str
    severity: str
    message: str


class IdentifiedDocument(BaseModel):
    filename: str
    doc_type: str


class ValidationReport(BaseModel):
    status: str
    score: int
    discrepancies: List[Discrepancy]


class ValidateResponse(BaseModel):
    documents: List[IdentifiedDocument]
    report: Optional[ValidationReport] = None
    warning: Optional[str] = None


class Lead(BaseModel):
    name: str
    phone: str
    message: str = ""


# ---------- Routes ----------

@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/validate", response_model=ValidateResponse)
async def validate(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(400, "Upload at least one document.")

    wrapped: List[InMemoryFile] = []
    for f in files:
        if f.content_type not in ALLOWED_TYPES:
            raise HTTPException(400, f"Unsupported file type for {f.filename}. Use PDF, PNG, JPG or WEBP.")
        data = await f.read()
        if len(data) > MAX_FILE_MB * 1024 * 1024:
            raise HTTPException(400, f"{f.filename} is larger than {MAX_FILE_MB} MB.")
        wrapped.append(InMemoryFile(data, f.filename or "document", f.content_type))

    try:
        batch: BatchResponse = process_all_document(wrapped, BatchResponse)
    except Exception as e:  # Gemini / parsing failure
        raise HTTPException(502, f"Document extraction failed: {e}")

    documents = [IdentifiedDocument(filename=d.filename, doc_type=d.doc_type) for d in batch.documents]

    lc_data = next((d.lc_data for d in batch.documents if d.doc_type == "LC" and d.lc_data), None)
    invoice_data = next((d.invoice_data for d in batch.documents if d.doc_type == "Invoice" and d.invoice_data), None)

    if not (lc_data and invoice_data):
        return ValidateResponse(
            documents=documents,
            warning="An issued LC and a commercial invoice are both required to run the discrepancy check.",
        )

    conditions = get_structured_data_text(
        prompt=Prompt_additional_condition,
        text=lc_data.additional_conditions,
        schema=DocumentRequirements,
    ) or DocumentRequirements()

    result = compare_lc_and_invoice(lc_data, invoice_data, conditions)

    return ValidateResponse(
        documents=documents,
        report=ValidationReport(
            status=result["Status"].strip(),
            score=result["Score"],
            discrepancies=[Discrepancy(**d) for d in result["Discrepancy"]],
        ),
    )


@app.post("/api/leads")
def create_lead(lead: Lead):
    if not lead.phone.strip():
        raise HTTPException(400, "Phone number is required.")
    try:
        requests.post(GOOGLE_SHEET_URL, json=lead.model_dump(), timeout=10)
    except Exception as e:
        raise HTTPException(502, f"Could not save your request: {e}")
    return {"ok": True}
