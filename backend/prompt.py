prompt_BiBiNi = """
ROLE: Senior Trade Finance Auditor specializing in Nepal Banking Regulations.
TASK: Extract structured data from Bi.Bi.Ni. Form No. 3 for LC compliance.

### SECTION 1: ENTITY RESOLUTION (Nepali Document OCR Correction)
These forms are often handwritten. Use context to normalize:
- IMPORTER NAME: 
  * "SVETI BREWERY", "VETI BREWERY", "YETI BREWARY" → "YETI BREWERY LTD"
  * Always expand to full legal name
- SELLER/EXPORTER NAME:
  * "Pot.ltd", "Put.ltd", "Pvt.ltd" → "PVT LTD"
  * "Barmalt", "Barrmalt" → "BARMALT MALTING (INDIA) PVT LTD"
- BANK NAME:
  * "RBB" → "RASTRIYA BANIJYA BANK LTD"
  * Always use full official bank name

### SECTION 2: DATA PRESERVATION (DO NOT NORMALIZE THESE)
- goods_description_raw: Extract EXACTLY as handwritten in "सामानको नाम" box
  * Keep ALL typos and variations (e.g., "6-Raw malt" stays "6-Raw malt")
  * This field is used for discrepancy detection - accuracy is critical
- bibini_number: Exact "सि.नं." value
- quantity: Extract exactly as written including unit

### SECTION 3: NUMERIC FIELDS
- importer_pan: 9-digit "Aayakar Darta Number" (e.g., 601095685)
- amount: Clean float, no currency symbols (e.g., 17808000.0)
- OCR RECOVERY: "INK" → "INR", 'O' → '0' in numeric fields

### SECTION 4: DATE FORMATTING  
- registration_date: Convert to YYYY-MM-DD format
  * "08.12.2025" → "2025-12-08"
  * "०८/१२/२०२५" (Nepali numerals) → "2025-12-08"

### SECTION 5: VISUAL VERIFICATION
- is_signed: True if handwritten signature visible in "निवेदकको दस्तखत" or bank authorization area
- is_stamped: True if circular or rectangular bank stamp visible (usually blue/purple ink)

### SECTION 6: FIELD MAPPINGS
- bibini_number → "सि.नं." value
- registration_date → "मिति" field
- customs_entry_point → "भन्सार प्रवेश विन्दु" field (e.g., "Krishnanagar customs")
- bank_branch → branch name of issuing bank (e.g., "Dubarmarg")

Return ONLY valid JSON matching the schema. No explanations.
"""


Prompt_LC = """
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


Prompt_invoice = """
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

prompt_bol = """
ROLE: Senior Maritime Logistics & Trade Finance Auditor.
TASK: Extract structured data from the Bill of Lading for LC compliance checking.

### SECTION 1: PARTY NAME EXTRACTION (CRITICAL)
For shipper and consignee fields:
- Extract ONLY the legal company/entity name
- DO NOT include address, city, country, floor, building, or location details
- Stop at address keywords: Complex, Road, Street, Building, Floor, Near, Opposite, city names
- Examples:
  * "BARMALT MALTING (INDIA) PVT LTD, PUNE - 411001, INDIA" → "BARMALT MALTING (INDIA) PVT LTD"
  * "YETI BREWERY LTD, ATAL COMPLEX, UTTAR DHOKA, KATHMANDU" → "YETI BREWERY LTD"
  * "TO ORDER OF RASTRIYA BANIJYA BANK" → "TO ORDER OF RASTRIYA BANIJYA BANK" (keep if consignee is TO ORDER)
- notify_party: Keep FULL name AND address (needed for delivery notification)

### SECTION 2: PORT NORMALIZATION (CRITICAL)
For port_of_loading and port_of_discharge:
- Extract port/city name and country ONLY
- REMOVE customs office names, route details, via points, ICD names
- Always append country if not explicitly stated. Format: "[PORT], [COUNTRY]"
- Examples:
  * "NHAVA SHEVA (JNPT)" → "NHAVA SHEVA, INDIA"
  * "BIRGUNJ VIA KRISHNANAGAR CUSTOMS" → "BIRGUNJ, NEPAL"
  * "ICD TUGHLAKABAD, NEW DELHI" → "ICD TUGHLAKABAD, INDIA"
  * "CHITWAN, NEPAL VIA RAXAUL" → "CHITWAN, NEPAL"
  * "KOLKATA PORT TRUST" → "KOLKATA, INDIA"

### SECTION 3: DATES (CRITICAL)
- shipped_date / shipped_on_board_date: Look specifically for "SHIPPED ON BOARD" stamp/notation
  * This is the MOST IMPORTANT date on the BOL
  * If multiple dates exist, use the one with "ON BOARD" or "LADEN ON BOARD" notation
  * Convert ALL dates to YYYY-MM-DD format
- issue_date: Date the BOL was issued (may differ from shipped date)

### SECTION 4: CARGO DETAILS
- description_of_goods: Extract EXACTLY as written. Keep typos. Keep original casing.
- gross_weight_unit: Normalize all weight unit variants to "KGS"
  * "Kgs", "K.G.", "KG", "KILOGRAMS" → "KGS"
  * "MT", "M.T.", "METRIC TON" → keep as "MT" (conversion handled separately)
- number_of_packages: Integer only (e.g., 8400)
- package_type: e.g., "BAGS", "CARTONS", "PALLETS"
- number_of_originals: Format as "X/X" (e.g., "3/3")
- freight_status: "Prepaid" or "Collect" only

### SECTION 5: DOCUMENT TYPE
- bl_type: Look for stamps or printed text saying "Original", "Non-Negotiable" (= Copy), or "Sea Waybill"
- endorsement_status: 
  * "BLANK" if no endorsement on back
  * "TO ORDER" if it says "To Order" without specifying bank
  * "TO ORDER OF [BANK NAME]" if bank is specified

### SECTION 6: VISUAL COMPLIANCE
- is_clean: True UNLESS document contains clauses like "damaged", "torn", "wet", "leaking", "in dispute"
- has_carrier_signature: True ONLY if signature/stamp present in carrier or agent box (usually bottom right)

### SECTION 7: OCR RECOVERY
- In numeric fields: 'O' → '0', 'I' → '1'
- Container numbers follow format: 4 letters + 7 digits (e.g., MSKU1234567)

Return ONLY valid JSON matching the schema. No explanations.
"""

Prompt_additional_condition = """
ROLE: Senior Trade Finance Auditor (Nepal-India Compliance Expert).
TASK: Parse Field 47A (Additional Conditions) to extract document requirements checklist.

### SECTION 1: TRIGGER PHRASES (Set boolean to True if ANY of these appear)
- must_have_lc_number: 
  * Triggers: "SHOULD QUOTE", "MUST BEAR", "SHOULD INDICATE", "MUST MENTION", "SHOULD MENTION"
  * Combined with: "L/C NO", "OUR L/C NO", "LC NUMBER", "LETTER OF CREDIT NUMBER"
  
- must_have_lc_date:
  * Combined with: "LC ISSUE DATE", "DATE OF ESTABLISHMENT", "DATE OF LC", "L/C DATE"
  
- must_have_hs_code:
  * Combined with: "HS CODE", "HARMONIZED CODE", "HSN CODE", "TARIFF CODE"
  
- must_have_issuing_bank_name:
  * Combined with: "BANK'S NAME", "ISSUING BANK", "RASTRIYA BANIJYA BANK", "RBB"
  
- must_have_applicant_pan:
  * Combined with: "PAN NO", "PAN NUMBER", "PERMANENT ACCOUNT NUMBER", "VAT NO"
  
- must_have_exim_code:
  * Combined with: "EXIM CODE", "EXIM CODE NO", "EXIM REGISTRATION"

### SECTION 2: SCOPE RULE
- Requirements in Field 47A apply to ALL submitted documents unless specifically limited
  * "ALL DOCUMENTS SHOULD QUOTE LC NO" → must_have_lc_number: True for all docs
  * "INVOICE SHOULD BEAR PAN NO" → must_have_applicant_pan: True

### SECTION 3: DEFAULT VALUES
- must_be_signed_stamped: Default True unless explicitly stated otherwise
- language_requirement: Default "ENGLISH" unless another language mentioned

### SECTION 4: OCR RECOVERY
- 'O' → '0' and 'I' → '1' when reading identification numbers
- "EXIM CQDE" → "EXIM CODE" (common OCR error)
- "PAN NQ" → "PAN NO"

Return ONLY valid JSON. No explanations. No markdown.
"""

