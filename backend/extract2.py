from pydantic import BaseModel, ValidationError, field_validator, Field
from typing import List, Optional, Literal, Union
import re
from compare import compare_lc_and_invoice, compare_lc_bol
from helper_function import get_structured_data, get_structured_data_text
from datetime import date
from prompt import prompt_BiBiNi, prompt_bol, Prompt_additional_condition, Prompt_invoice, Prompt_LC

class DocumentRequirements(BaseModel):
    must_have_lc_number: bool = False
    must_have_lc_date: bool = False
    must_have_hs_code: bool = False
    must_have_issuing_bank_name: bool = False
    must_have_applicant_pan: bool = False
    must_have_exim_code: bool = False
    must_be_signed_stamped: bool = True  # Standard requirement
    language_requirement: str = "ENGLISH"


class DocClassify(BaseModel):
    document_type : str


class LCData(BaseModel):
    """
ROLE: Senior Trade Finance Auditor specializing in SWIFT MT700 LC documents.
TASK: Extract structured data from this Letter of Credit document.

### SECTION 1: PARTY NAME EXTRACTION (CRITICAL)
For ALL party fields (applicant, beneficiary, issuing_bank, advising_bank):
- Extract ONLY the legal company/entity name
- DO NOT include address, city, country, floor, building, road, or any location details
- Stop extracting when you encounter address keywords like: Complex, Road, Marg, Chowk, Street, Building, Floor, Block, Plot, Near, Opposite, P.O. Box, or any city/country name after the company name
- Examples:
  * "YETI BREWERY LTD. ATAL COMPLEX, UTTAR DHOKA, LAZIMPAT-2, KATHMANDU, NEPAL" → "YETI BREWERY LTD"
  * "BARMALT MALTING (INDIA) PVT. LTD. FOR DETAILS SEE SECTION 47A (6)" → "BARMALT MALTING (INDIA) PVT LTD"
  * "RASTRIYA BANIJYA BANK LTD, DHARMAPATH, KATHMANDU" → "RASTRIYA BANIJYA BANK LTD"
  * "KOTAK MAHINDRA BANK, MUMBAI BRANCH" → "KOTAK MAHINDRA BANK"

### SECTION 2: PORT/PLACE NORMALIZATION (CRITICAL)
For place_of_loading and final_destination:
- Extract ONLY the place name and country
- REMOVE customs office names, route info, via points, and border crossing details
- Always append country if not present. Format: "[PLACE], [COUNTRY]"
- Special LC terms: Keep "ANY PLACE IN INDIA" or "ANY PORT IN INDIA" exactly as written
- Examples:
  * "CHITWAN, NEPAL VIA KRISHNANAGAR CUSTOM OFFICE NEPAL" → "CHITWAN, NEPAL"
  * "NHAVA SHEVA (JNPT), INDIA" → "NHAVA SHEVA, INDIA"
  * "ANY PLACE IN INDIA" → "ANY PLACE IN INDIA" (keep exactly as is)
  * "BIRGUNJ" → "BIRGUNJ, NEPAL"
  * "INDIA" → "INDIA"

PORT/PLACE EXTRACTION

For place_of_loading and final_destination:
- Extract the full text as written
- ALSO extract just the country name separately

Examples:
- "ANY PLACE IN INDIA" → 
  * place_of_loading: "ANY PLACE IN INDIA"
  * place_of_loading_country: "INDIA"
  
- "CHITWAN, NEPAL VIA KRISHNANAGAR" →
  * final_destination: "CHITWAN, NEPAL"
  * final_destination_country: "NEPAL"
  
- "NHAVA SHEVA, INDIA" →
  * place_of_loading: "NHAVA SHEVA, INDIA"
  * place_of_loading_country: "INDIA"


### SECTION 3: OCR NOISE FILTERING
- NUMERIC RECOVERY: Interpret 'O/o' as '0', 'I/l' as '1', 'S' as '5' in numeric fields
  * "42000O.0O" → 420000.00
  * "5O KG" → "50 KG"
- SPACING: Fix run-together words only: "inHDPE" → "in HDPE"
- CASING: DO NOT change casing of letters. If description is uppercase, keep uppercase. If mixed, keep mixed.
- PUNCTUATION: DO NOT add or remove hyphens in product names. "6-ROW" stays "6-ROW". "6 ROW" stays "6 ROW"

### SECTION 4: GOODS DESCRIPTION
- 'raw_field_45a': Copy the COMPLETE text from Field 45A exactly as written
- 'clean_goods_description': Extract ONLY product name and packaging detail
  * Example: "6-ROW MALT PACKED IN HDPE BAGS EACH CONTAINING 50 KG (NET)"
  * Remove quantity amounts, unit prices, HS codes from this field
  * Keep: product name, packaging type, size/weight per unit

### SECTION 5: DATE FORMATTING
- Convert ALL dates to YYYY-MM-DD format regardless of input format
  * "260216" → "2026-02-16"
  * "08.12.2025" → "2025-12-08"
  * "16 FEB 2026" → "2026-02-16"

### SECTION 6: TOLERANCE (Field 39A)
- Format is "PLUS/MINUS" → extract as two separate floats
  * "5/5" → tolerance_plus_percentage: 5.0, tolerance_minus_percentage: 5.0
  * "0/0" → tolerance_plus_percentage: 0.0, tolerance_minus_percentage: 0.0
  * "10/5" → tolerance_plus_percentage: 10.0, tolerance_minus_percentage: 5.0

### SECTION 7: SPECIAL CHARACTERS
- "(AT)" → "@" for email addresses
- "L/C" → "LC" in text fields

Return ONLY valid JSON matching the schema. No explanations.
"""

    doc_type: Literal["LC"] = "LC" 
    # Header Information
    lc_number: str                  # Field 20: L25187000041
    issue_date: str                 # Field 31C: 251209

    # The full raw text from Field 45A for record-keeping
    # raw_field_45a: str 
    
    # A cleaner version for the Triple-Match comparison
    # AI Prompt instruction: "Extract only the product name and packaging detail"
    clean_goods_description: str  # e.g., "6-ROW MALT PACKED IN HDPE BAGS EACH CONTAINING 5O KG (NET)"
    
    # Parties
    issuing_bank: str               # Field 51D: RASTRIYA BANIJYA BANK LTD
    applicant: str                  # Field 50: YETI BREWERY LTD
    beneficiary: str                # Field 59: BARMALT MALTING (INDIA) PVT. LTD.
    advising_bank: Optional[str]    # Field 57D: KOTAK MAHINDRA BANK
    
    # Financials
    currency: str                   # Field 32B: INR
    amount: float                   # Field 32B: 17808000.00
    tolerance: str                  # Field 39A: 0/0
    draft_terms: str                # Field 42C: 30 DAYS FROM DATE OF INVOICE
    
    # Logistics
    latest_shipment_date: str        # Field 44C: 260216
    shipment_date_object: date       #Extract all dates in YYYY-MM-DD format. If a date is in a different format (like 08.12.2025 or 260216), convert it to YYYY-MM-DD before returning the JSON.
 
    expiry_date_place: str          # Field 31D: 260309, INDIA
    place_of_loading: str           # Field 44A: ANY PLACE IN INDIA and AI INSTRUCTION: Normalize to "[PLACE], [COUNTRY]" format # "ANY PLACE IN INDIA" → keep as is (it's a special LC term)  # "CHITWAN, NEPAL" → "CHITWAN, NEPAL"     # "INDIA" → "INDIA" (country only is valid).
    place_of_loading_country: str   #just the countryplace_of_loading: "ANY PLACE IN INDIA" place_of_loading_country: "INDIA"


    final_destination: str          # Field 44B: CHITWAN, NEPAL and AI INSTRUCTION: Normalize to "[PLACE], [COUNTRY]" format.
    final_destination_country: str  #"CHITWAN, NEPAL VIA KRISHNANAGAR" → final_destination: "CHITWAN, NEPAL" final_destination_country: "NEPAL"

    partial_shipments: str          # Field 43P: ALLOWED
    transhipment: str               # Field 43T: ALLOWED
    
    # Goods (Extracted from 45A)
    quantity: str                   # 420000.00 KGS
    unit_price: str                 # INR 42.40/KG
    hs_code: str                    # 11071000
    
    # Legal & Requirements
    documents_required: List[str]    # Field 46A: 1.DRAFT, 2.ROAD CONSIGNMENT ...
    additional_conditions: List[str] # Field 47A: 1.DISCREPANCY FEE...
    presentation_period: str         # Field 48: 21 DAYS

    applicant_Exim_code: str
    applicant_Pan: str

    tolerance_plus_percentage: float  # Field 39A The before digit of / like for 1/2 the minus tolerance percentage is 1 
    tolerance_minus_percentage: float # Field 39A the after digit of / like for 1/2 the minus tolerance percentage is 2 


class InvoiceData(BaseModel):
    """
ROLE: Pedantic Trade Finance Auditor.
TASK: Extract Invoice data with character-level accuracy for LC discrepancy checking.

### SECTION 1: PARTY NAME EXTRACTION
For exporter_name and consignee_name:
- Extract ONLY the legal company name
- DO NOT include address, city, country, or location details
- Examples:
  * "BARMALT MALTING (INDIA) PVT. LTD., PUNE, MAHARASHTRA" → "BARMALT MALTING (INDIA) PVT LTD"
  * "YETI BREWERY LTD., ATAL COMPLEX, KATHMANDU" → "YETI BREWERY LTD"

### SECTION 2: DESCRIPTION OF GOODS (MOST CRITICAL FIELD)
- Extract EXACTLY as printed on the invoice. Character-level accuracy required.
- DO NOT fix typos in product names (if it says "MALTINGG", keep "MALTINGG")
- DO NOT change casing (lowercase stays lowercase, uppercase stays uppercase)
- DO NOT add or remove hyphens
- DO fix OCR number errors in numeric parts only: "5O KG" → "50 KG"
- DO fix spacing errors: "Packed inHDPE" → "Packed in HDPE"
- Extract ONLY product name and packaging detail (not quantities or prices)
- Example: "6 Row malt Packed in HDPE bags each containing 50 Kg (net)"

### SECTION 3: NUMERIC PRECISION
- Extract totals as clean floats. Remove currency symbols and commas.
  * "INR 17,808,000.00" → 17808000.0
  * "42000O" → 420000.0
- unit_price: Extract per-unit price as float
  * "INR 42.40/KG" → 42.40

### SECTION 4: IDENTIFICATION NUMBERS
- applicant_Pan: 9-digit PAN number of buyer
- exporter_Pan: PAN number of seller/exporter
- applicant_Exim_Code: EXIM registration code (usually starts with numbers + NP)

### SECTION 5: VISUAL VERIFICATION
- is_signed: True ONLY if actual handwritten signature visible (not printed name)
- is_stamped: True ONLY if physical rubber stamp visible (blue/purple ink, circular or rectangular)

### SECTION 6: SPECIAL HANDLING
- "(AT)" → "@" for email addresses
- full_text_raw: Dump the COMPLETE raw text of the document here

Return ONLY valid JSON. No explanations.
"""

    doc_type: Literal["Invoice"] = "Invoice" 
    invoice_no: str              # 2025-26/055
    invoice_date: str            # 24.11.2025
    exporter_name: str           # Barmalt Malting (India) Pvt. Ltd.
    consignee_name: str          # YETI BREWERY LTD.
    currency: str                # INRS
    total_amount: float          # 17808000.00
    description_of_goods: str    # 6 Row malt Packed in HDPE bags...
    total_quantity: float        # 420000.00
    unit_of_measure: str         # KG
    unit_price: float            # 42.40
    hs_code: str                 # 11071000
    origin_country: str          # INDIA
    destination_country: str     # NEPAL
    delivery_terms: str          # Ex-Works, India
    payment_terms: str           # 30 Days from date of invoice under L/C
    # full_text_raw: str           # Dump complete text here to check if it contains some special number
    applicant_Pan: str
    exporter_Pan: str
    applicant_Exim_Code: str
    is_signed: bool              
    is_stamped: bool             
    #applicant_lc_number : str     when we have commercial invoice
    #Lc_issusing_bank_name: str    when we have commercial invoice
    #lc_issue_date: str            when we have commerical invoice

    @field_validator('unit_price', 'total_amount')
    @classmethod
    def clean_structure(cls, v):
        if isinstance(v, str):
            cleaned = re.sub(r'[^\d.]', '', v)
            return float(cleaned) if cleaned else 0.0
        return v
    


class BillOfLadingData(BaseModel):
    doc_type: Literal["BOL"] = "BOL"
    # Document identification
    bl_number: str
    bl_type: str  # "Original", "Copy", "Sea Waybill"
    issue_date: str
    
    # Carrier & transport
    carrier_name: str
    vessel_name: Optional[str]  # Not always present (could be TBD)
    voyage_number: Optional[str]
    
    # Critical dates
    shipped_on_board_date: str  # CRITICAL for LC compliance
    shipped_date: date  #Extract all dates in YYYY-MM-DD format. If a date is in a different format (like 08.12.2025 or 260216), convert it to YYYY-MM-DD before returning the JSON.
    
    # Parties
    shipper: str
    consignee: str  # CRITICAL
    notify_party: str
    endorsement_status: str  # "BLANK", "TO_ORDER", etc.
    
    # Ports (CRITICAL)
    port_of_loading: str # Ports (CRITICAL) # AI INSTRUCTION: Always append country name if not present.  # Examples:  # "NHAVA SHEVA" → "NHAVA SHEVA, INDIA"     # "MUMBAI" → "MUMBAI, INDIA"       # "CHITWAN" → "CHITWAN, NEPAL"     # "KOLKATA PORT" → "KOLKATA, INDIA"     # Format: "[PORT NAME], [COUNTRY]"
    port_of_loading_country: str  #"NHAVA SHEVA, INDIA" → place_of_loading: "NHAVA SHEVA, INDIA" place_of_loading_country: "INDIA"

    port_of_discharge: str # AI INSTRUCTION: Same as above - always include country.     # "BIRGUNJ" → "BIRGUNJ, NEPAL"
    port_of_discharge_country: str #"CHITWAN, NEPAL VIA KRISHNANAGAR" → final_destination: "BIRGUNJ, NEPAL" final_destination_country: "NEPAL"


    place_of_receipt: Optional[str]
    place_of_delivery: Optional[str]
    
    # Cargo description
    description_of_goods: str
    marks_and_numbers: Optional[str]  # Container/seal numbers
    
    # Quantities (CRITICAL)
    number_of_containers: Optional[str]
    number_of_packages: int
    package_type: str  # "BAGS", "CARTONS", etc.
    gross_weight_value: float
    gross_weight_unit: str  # "KGS", "MT", "LBS"
    
    # BOL specific
    freight_status: str  # "Prepaid" or "Collect"
    number_of_originals: str  # "3/3" for full set
    is_clean: bool  # Must be True (no clauses)
    
    # Signatures (validation only)
    has_carrier_signature: bool

    

class PackingListData(BaseModel):
    doc_type: Literal["PL"] = "PL"
    pl_number: str                 # Packing List Reference Number
    pl_date: str                   # Date of issuance
    lc_number_ref: str             # Field 47A(2) requires quoting the LC No.
    
    exporter_name: str             # Barmalt Malting (India) Pvt. Ltd.
    consignee_name: str            # Yeti Brewery Ltd.
    
    total_bags: int                # Based on LC: Should be 8,400 bags (420k kg / 50kg)
    quantity_per_bag: float        # Based on LC: Should be 50.00
    unit_of_measure: str           # KGS
    
    total_net_weight: float        # Should match Invoice/LC: 420000.00
    total_gross_weight: float      # Net Weight + Bag Weight
    
    packaging_type: str            # Field 45A: "HDPE BAGS"
    shipping_marks: str            # Field 47A(2): "Product of India", Pan No, etc.
    
    is_signed: bool                # Field 47A(2): "Should be duly signed and stamped"
    full_text_raw: str             # For verifying HS Code and other mandatory text


class BiBiNiData(BaseModel):
    form_type: str = "Bi.Bi.Ni. Form No. 3"
    
    bibini_number: str  # The "सि.नं." (RBB)
    registration_date: str 
    
    # Entity Data
    importer_name: str
    importer_pan: str = Field(..., description="9-digit Aayakar Darta Number")
    bank_branch: str
    issuing_bank: str = Field(..., description= "Name of the bank that issued the bibini form")
    seller_name: str 
    
    # Financials
    amount: float
    currency: str = "INR"
    
    # Logistics (The "Triple Match" Fields)
    hs_code: str
    customs_entry_point: str
    goods_description_raw: str = Field(..., description="Exact handwritten text")
    quantity: str
    
    # Compliance checks
    is_signed: bool = False
    is_stamped: bool = False


class MasterDocument(BaseModel):
    filename: str  # e.g., "LC_Nepal_Bank.pdf"
    doc_type: str  # e.g., "LC"
    
    # These are the "Optional Drawers"
    lc_data: Optional[LCData] = None
    invoice_data: Optional[InvoiceData] = None
    
    #more data to be added 


class BatchResponse(BaseModel):
    # A list of documents found in the 'parts' we sent
    documents: List[MasterDocument]


bol_manual =  {
    # Document identification
    "bl_number": "BLMUM2026001234",
    "bl_type": "Original",
    "issue_date": "2026-01-20",
    
    # Carrier & transport
    "carrier_name": "MAERSK LINE",
    "vessel_name": "MAERSK KOLKATA",
    "voyage_number": "MK2601N",
    
    # Critical dates
    "shipped_on_board_date": "2026-01-18",
    "shipped_date": "2026-01-18",
    
    # Parties
    "shipper": "BARMALT MALTING (INDIA) PVT LTD",
    "consignee": "YETI BREWERY LTD",
    "notify_party": "YETI BREWERY LTD, ATAL COMPLEX, UTTAR DHOKA, KATHMANDU, NEPAL",
    "endorsement_status": "BLANK",
    
    # Ports
    "port_of_loading": "NHAVA SHEVA, INDIA",
    "port_of_discharge": "BIRGUNJ, NEPAL",
    "place_of_receipt": "PUNE, INDIA",
    "place_of_delivery": "CHITWAN, NEPAL",
    
    # Cargo
    "description_of_goods": "6-ROW MALT PACKED IN HDPE BAGS EACH CONTAINING 50 KG (NET)",
    "marks_and_numbers": "CONTAINER NO: MSKU1234567, SEAL NO: 987654",
    
    # Quantities
    "number_of_containers": "2 X 20FT",
    "number_of_packages": 8400,
    "package_type": "BAGS",
    "gross_weight_value": 420000.0,
    "gross_weight_unit": "KGS",
    
    # BOL specific
    "freight_status": "Prepaid",
    "number_of_originals": "3/3",
    "is_clean": True,
    
    # Signatures
    "has_carrier_signature": True
}

if __name__ == "__main__":
    lc_data = get_structured_data(prompt= Prompt_LC, file_name= '2.pdf', schema=LCData)
    invoice_data = get_structured_data(prompt=Prompt_invoice, file_name= '3.pdf', schema= InvoiceData)
    add_condition = get_structured_data_text(prompt= Prompt_additional_condition, text= lc_data.additional_conditions, schema= DocumentRequirements)
    BiBini_data = get_structured_data(prompt= prompt_BiBiNi, file_name='4.pdf', schema= BiBiNiData)
    BOL_data = get_structured_data_text(prompt=prompt_bol,text= bol_manual, schema= BillOfLadingData )

    if lc_data:
        print("\nSUCCESS: LC Extracted")
        print(f"LC Number: {lc_data.lc_number}")
        print(f"Amount in LC: {lc_data.amount}")
        print(f"Description of goods in LC : {lc_data.clean_goods_description}")
        print(f"The quantity in Lc: {lc_data.quantity}")
        print(f"Upper Tolerance: {lc_data.tolerance_plus_percentage}")
        print(f"Date time object: {lc_data.shipment_date_object}")
        print(f"Port of discharge:{lc_data.final_destination}")
        print(f"LC HS code:{lc_data.hs_code}")


    if invoice_data:
        print("\nInvoice extracted successfully")
        print(f"Invoice Number: {invoice_data.invoice_no}")
        print(f"Amount in Invoice: {invoice_data.total_amount}")
        print(f"description of good in invoice data: {invoice_data.description_of_goods}")
        print(f"The quantity in invoice: {invoice_data.total_quantity}")
        print(f"Applicant Exim code: {invoice_data.applicant_Exim_Code}")
        print(f"Invoice HS code:{invoice_data.hs_code}")

    if add_condition:
        print("\nAdditional Condition Extracted Successfully!")
        # print(add_condition)
        print(f"Must_have_lc_number: {add_condition.must_have_lc_number}")
        print(f"Must_have_issuing_bank_name: {add_condition.must_have_issuing_bank_name}")
        print(f"Must have Exim Code: {add_condition.must_have_exim_code}")


    if BiBini_data:
        print("\nBiBiNi extracted successfully")
        print(f"Issuing Bank: {BiBini_data.issuing_bank}")
        print(f"Importer Pan: {BiBini_data.importer_pan}")
        print(f"Importer Name: {BiBini_data.importer_name}")
        print(f"Issuing Bank Branch: {BiBini_data.bank_branch}")

    if BOL_data:
        print(f"port_of_discharge : {BOL_data.port_of_discharge}") 


    result = compare_lc_and_invoice(lc_data, invoice_data, add_condition)
    result = compare_lc_bol(lc_data, BOL_data)

    print(result)
