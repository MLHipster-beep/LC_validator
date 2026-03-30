from google import genai
from google.genai import types

import os 
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def send_pdf(prompt, file_name, schema ):

    file_bytes = file_name.read()

    file_name.seek(0)

    file_part = types.Part.from_bytes(
        data=file_bytes,
        mime_type=file_name.type  
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[file_part, prompt],
        config=types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json",
                response_schema=schema, 
            ),
    )
    
    print(f"Extraction Completed!!")

    return response.text



def send_text(prompt, text, schema):

    print(f"Sending Text to the server...")


    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"{prompt}\n\n TEXT:\n{text}",
        config=types.GenerateContentConfig(
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=schema, 
        ),
    )

    print(f"Response Recieved!!")

    return response.text


def classify_doc(prompt, streamlit_file):
    file_bytes = streamlit_file.read()
    
    streamlit_file.seek(0)
    
    file_part = types.Part.from_bytes(
        data=file_bytes,
        mime_type=streamlit_file.type  
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[file_part, prompt],
        config=types.GenerateContentConfig(
            temperature=0.0,
            response_mime_type="application/json"
        ),
    )

    return response.text
from google.genai import types 

def process_all_document(files, schema):
    # check for images and other types 
    parts = []
    
    for f in files:
        f.seek(0)
        file_bytes = f.read()
        
        # 1. Keep the text label (this is fine)
        parts.append(f"DOCUMENT NAME: {f.name}") 
        
        # 2. FIXED: Use types.Part.from_bytes instead of a raw dictionary
        file_part = types.Part.from_bytes(
            data=file_bytes,
            mime_type=f.type
        )
        parts.append(file_part)
    
    # ... rest of your prompt and config ...
    parts.append("""Identify and extract all data per the BatchResponse schema.

For Document Identification use this

You are a Nepal trade finance document classification expert.

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
}""")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=parts,
        config=types.GenerateContentConfig( # Also use types for config
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=schema,
        ),
    )
    return schema.model_validate_json(response.text)