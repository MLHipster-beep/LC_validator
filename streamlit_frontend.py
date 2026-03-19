import streamlit as st
import base64
from helper_function import get_structured_data, get_structured_data_text
from prompt import Prompt_LC, Prompt_invoice, prompt_BiBiNi, Prompt_additional_condition, prompt_bol
from extract2 import LCData, InvoiceData, DocClassify, DocumentRequirements, bol_manual, BillOfLadingData
from SendingPdf import classify_doc
import json
from compare import compare_lc_and_invoice, df_result
import pandas as pd

st.write("# TradingDocs Validator")

# --- INITIALIZE SESSION STATE ---
# This acts as the "brain" so the app doesn't forget your results
if "result" not in st.session_state:
    st.session_state.result = None
if "doc_map" not in st.session_state:
    st.session_state.doc_map = None

def label_documents(file_object):
    prompt = """You are a Nepal trade finance document classification expert.

You are given multiple trade documents from a single export transaction. 
Analyze each document and classify it into EXACTLY ONE of these categories:

CATEGORIES:

1. "LC" - Final issued Letter of Credit that has been 
   TRANSMITTED through SWIFT. 

   MUST have AT LEAST ONE of these SWIFT transmission markers:
   - "Instance Type and Transmission" header
   - "Network Delivery Status" 
   - "Message Input Reference"
   - "Swift Input : FIN 700"
   - "Message Header" / "Message Text" / "Message Trailer" sections
   - Sender/Receiver BIC codes in SWIFT format (e.g., RBBANPKAXXX)
   - PKI Signature or MAC-Equivalent

   MUST NOT be classified as LC if it contains ANY of these:
   - "PLEASE SEND THE FOLLOWING MT 700" or similar instruction language
   - "PREPARED BY" / "CHECKED BY" / "SUBMITTED BY" / "APPROVED BY" 
     (indicates internal bank processing form)
   - "PLEASE SEND THROUGH SWIFT" or any instruction to transmit
   - Draft stamps or "PROPOSED" labels

   If a document contains all LC fields (40A, 20, 31D, etc.) 
   BUT has instruction language like "PLEASE SEND" or 
   has "PREPARED BY / CHECKED BY" sections, classify it as:
   "LC_DRAFT" — this is an internal bank instruction to 
   issue an LC, NOT the final transmitted LC itself.

2. "Invoice" - Commercial Invoice or Proforma Invoice from the exporter/beneficiary. Must contain:
   - Seller/exporter details
   - Buyer/importer details  
   - Description of goods with quantities and prices
   - Total amount
   - Invoice number

3. "BOL" - Bill of Lading. Must contain:
   - Shipper and consignee details
   - Port of loading and port of discharge
   - Description of goods/packages
   - Vessel name or flight details
   - BL number

4. "PL" - Packing List. Must contain:
   - Itemized list of goods with quantities
   - Package numbers, weights, dimensions
   - Usually NO prices (that differentiates it from invoice)

5. "Insurance" - Bima Bipatra / Insurance Certificate or Policy. Must contain:
   - Insurance company details
   - Coverage amount and type
   - Goods/shipment being insured
   - Policy or certificate number

6. "CO" - Certificate of Origin. Must contain:
   - Origin of goods certification
   - Usually issued by Chamber of Commerce or trade body
   - Exporter and importer details

7. "Other" - Any document that does not clearly fit categories 1-6.
   This includes:
   - Bank cover letters or transmittal notes
   - Internal bank communications
   - Draft documents
   - LC amendments
   - Beneficiary certificates
   - Any supporting correspondence

8. "LC_INSTRUCTION" - Internal bank document requesting 
   SWIFT transmission of an LC. Contains LC field data 
   but is NOT the final transmitted credit.
   
   Identified by:
   - "PLEASE SEND THE FOLLOWING MT 700" or similar
   - "PREPARED BY / CHECKED BY / APPROVED BY" at bottom
   - Contains LC fields but lacks SWIFT transmission headers
   - No Message Trailer or PKI Signature
   
   This document should NOT be used for discrepancy checking 
   as it is a pre-transmission draft.

CRITICAL RULES:
- Each category can be assigned to AT MOST ONE document
- If two documents could both be "LC", classify the one with 
  actual MT 700 / FIN 700 SWIFT format as "LC" and the other as "Other"
- If no document clearly matches a category, do not force-assign it
- When uncertain between two categories, prefer "Other" over wrong classification
- Nepali language documents: read carefully, many Nepali trade forms 
  mix Nepali and English text

Return ONLY a JSON object mapping each filename to its classification:
{
"document_type": "TYPE_NAME"
}"""
    try:
        raw_json = classify_doc(prompt=prompt, streamlit_file=file_object)
        if isinstance(raw_json, str):
            return json.loads(raw_json).get("document_type", "Other")
        return raw_json.get("document_type", "Other")
    except Exception as e:
        st.error(f"Error identifying {file_object.name}: {e}")
        return "Unknown"
    
st.title('Upload your Documents')
uploaded_files = st.file_uploader("Upload Important trade documents [LC, Invoice, BOL, PL, Bi. Bi. Ni]" , accept_multiple_files=True)

# --- ACTION BUTTON ---
if st.button("Categorize Document"):
    doc_map = {}
    with st.spinner("Gemini is identifying documents.. "):
        for file in uploaded_files:
            label = label_documents(file)
            doc_map[file.name] = label


    
    # Save the map to memory
    st.session_state.doc_map = doc_map

    lc_file = next((f for f in uploaded_files if doc_map[f.name] == 'LC'), None)
    invoice_file = next((f for f in uploaded_files if doc_map[f.name] == 'Invoice'), None)
    # bol_file = get_structured_data_text(prompt=prompt_bol,text= bol_manual, schema= BillOfLadingData)

    if invoice_file and lc_file:
        with st.spinner("Extracting data from documents..."):
            lc_data = get_structured_data(prompt=Prompt_LC, file_name=lc_file, schema=LCData)
            invoice_data = get_structured_data(prompt=Prompt_invoice, file_name=invoice_file, schema=InvoiceData)

        if lc_data and invoice_data:
            add_condition = get_structured_data_text(
                prompt=Prompt_additional_condition, 
                text=lc_data.additional_conditions, 
                schema=DocumentRequirements
            )
            # Save the final result to memory
            st.session_state.result = compare_lc_and_invoice(lc_data, invoice_data, add_condition)
        else:
            st.error("Gemini failed to extract structured data. Check document quality.")

st.write("---")

if st.session_state.doc_map:
    st.write("### Identified Documents:")
    col3, col4 = st.columns(2)

    col3.header('Filename')
    col4.header('Document Type')

    for i in st.session_state.doc_map:
        col3.text(i)
        col4.text(st.session_state.doc_map[i])

if st.session_state.result:
    result = st.session_state.result
    st.write("---")
    st.write("### Discrepancy Report")

    if result.get("Discrepancy"):
        df = pd.DataFrame(result["Discrepancy"])
        # Insert at index 0 so it's the first thing users see
        if 'Ignore' not in df.columns:
            df.insert(len(df.columns), 'Ignore', False)

        # Using a unique key ensures the state is tracked correctly
        edited_df = st.data_editor(
            df,
            column_config={
                "Ignore": st.column_config.CheckboxColumn("Ignore?", default=False),
                "severity": st.column_config.TextColumn("Severity Level"),
            },
            disabled=["field", "severity", "message"],
            hide_index=True,
            key="discrepancy_table" 
        )

        # Calculate Ignored Logic
        ignored_count = edited_df[edited_df["Ignore"] == True].shape[0]
        if ignored_count > 0:
            st.info(f" You have ignored {ignored_count} discrepancy(ies).")

            active_discrepancies = edited_df[edited_df["Ignore"] == False]

            st.write('### Active Discrepancies')
            st.write(active_discrepancies)

            scor = df_result(active_discrepancies)
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Re-calculated Score", f"{scor['Score']}/100")
            with col2:
                status_color = "green" if scor['Status'].strip() == "PASS" else "red"

                st.markdown(f"**Status:** :{status_color}[{scor['Status']}]")
                
        else:
            # Final Summary Card
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Raw Score", f"{result['Score']}/100")
            with col2:
                status_color = "green" if result['Status'].strip() == "PASS" else "red"
                st.markdown(f"**Status:** :{status_color}[{result['Status']}]")

    else:
        st.success("No discrepancies found! Documents match perfectly.")