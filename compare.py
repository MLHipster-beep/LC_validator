from difflib import SequenceMatcher
from typing import List, Dict
import re


def fix_ocr(text:str):
    corrections = {
        'O': '0',  # Oscar to Zero
        'o': '0',  # lowercase o to Zero
        'I': '1',  # Capital i to One
        'l': '1',  # Lowercase L to One
        'S': '5',  # S to Five (Common in 50 KG)
        'B': '8',  # B to Eight
    }
    for char, val in corrections.items():
        text = text.replace(char, val)
    
    return text

def smart_ocr_fix(text: str) -> str:
    """
    Only replaces 'O' or 'o' with '0' if they are 
    part of a number (e.g., '5O' -> '50', '42000O' -> '420000').
    It will NOT touch 'ROW' or 'ORDER'.
    """
    if not text:
        return ""
    
    # Regex logic: 
    # (?<=\d)O  -> Find 'O' preceded by a digit
    # O(?=\d)   -> Find 'O' followed by a digit
    # [Oo]      -> Match both cases
    
    # This pattern catches: 5O, O5, 420O0, etc.
    fixed = re.sub(r'(?<=\d)[Oo]|[Oo](?=\d)', '0', text)
    
    return fixed

def split (text):
    mat = re.search(r'[a-zA-Z]', text)
    if mat:
        index = mat.start()
        # Part 1: Everything before the first letter (stripped of whitespace)
        number_part = text[:index].strip()
        # Part 2: Everything from the first letter onwards
        unit_part = text[index:].strip()
        return number_part, unit_part
    
    return text, ""


def clean_to_float(value):

    """Helper to turn '420000.00 KGS' or '#17808000.00#' into 420000.0"""
    if isinstance(value, float) or isinstance(value, int):
        return float(value)
    
    number_part , unit = split(str(value))
    fixed_text = fix_ocr(number_part)

    cleaned = re.sub(r'[^\d.]', '', fixed_text)

    return float(cleaned) if cleaned else 0.0

def normalize_text(text: str) -> str:
    if not text:
        return ""
    
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def normalize_company_name(name:str) -> str:
    """Normalize company names for comparison"""
    if not name:
        return ""
    
    name = name.upper().strip()
    
    # Common abbreviation expansions
    replacements = {
        "LIMITED": "LTD",
        "PRIVATE": "PVT",
        "CORPORATION": "CORP",
        "INCORPORATED": "INC",
        "COMPANY": "CO",
        "AND": "&",
        "  ": " ",  # Double spaces
    }
    
    for old, new in replacements.items():
        name = name.replace(old, new)
    
    # Remove punctuation
    name = name.replace(".", "").replace(",", "").strip()
    
    return name


def max_val(quantity, value):
    maximum_val = quantity + ((value/100)*quantity)
    return maximum_val

def min_val(quantity, value):
    minimum_val = quantity - ((value/100)*quantity)
    return minimum_val


def fuzzy_match(s1: str, s2: str) -> float:
    """Returns a similarity score between 0 and 1."""
    return SequenceMatcher(None, s1.lower().strip(), s2.lower().strip()).ratio()

def compare_lc_and_invoice(lc, invoice, additional) -> Dict:
   
    lc_desc_clean = smart_ocr_fix(lc.clean_goods_description)
    inv_desc_clean = smart_ocr_fix(invoice.description_of_goods)

    discrepancies = []

    lc_norm = lc_desc_clean.replace("-", " ").strip()
    inv_norm = inv_desc_clean.replace("-", " ").strip()

    #checking module
    
    invoice.hs_code = 12123131
    invoice.is_signed = False
    invoice.total_amount = 20000000

    # print(f" The clean Invoice description {inv_desc_clean}")
    # print(f"The cleaned LC description {lc_desc_clean}")

    if lc_desc_clean == inv_desc_clean:
        pass

    
    elif lc_desc_clean.upper() == inv_desc_clean.upper():
        discrepancies.append({
            'field': 'Goods Description', 
            'severity': 'LOW', 
            "message": "Casing mismatch. The bank prefers ALL CAPS as per the LC."
        }) 

    elif lc_norm == inv_norm:
        discrepancies.append({
            'field': 'Goods Description', 
            'severity': 'LOW',
            "message": f"Hyphen mismatch! Invoice says '{invoice.description_of_goods}' but LC requires '{lc.clean_goods_description}'. The bank may charge a $250 fee."
        }) 
    
    else:
        discrepancies.append({
        'field': 'Goods Description', 
        'severity': 'LOW', 
        "message": "Goods description has casing and hyphen mismatch."
    })
    
    max_amount = max_val(lc.amount, lc.tolerance_plus_percentage)
    min_amount = min_val(lc.amount, lc.tolerance_plus_percentage)

    if min_amount <= invoice.total_amount <= max_amount:
        pass
    else:
        discrepancies.append({
            'field': 'Amount Mismatch',
            'severity': 'CRITICAL',
            'message': f"The Amount in Invoice doesn't match with LC and doesn't Fall under the tolerance minimum {min_amount} and maximum {max_amount}"
        })

   
    lc_benef_clean = lc.beneficiary.lower().strip()
    inv_exp_clean = invoice.exporter_name.lower().strip()

    if inv_exp_clean in lc_benef_clean:
        name_score = 1.0
    else:
        name_score = fuzzy_match(inv_exp_clean, lc_benef_clean)

    if name_score < 0.9 and inv_exp_clean not in lc_benef_clean:
        discrepancies.append({
            'field': 'Beneficiary Name',
            'severity': 'CRITICAL',
            'message': f"Exporter name mismatch. Invoice: '{invoice.exporter_name}' not found in LC Beneficiary field."
        })

    # 3. HIGH: HS Code Verification
    if additional.must_have_hs_code:
        if str(lc.hs_code).strip() != str(invoice.hs_code).strip():
            discrepancies.append({
                'field': 'HS Code',
                'severity': 'HIGH',
                'message': f"HS Code mismatch. LC: {lc.hs_code}, Invoice: {invoice.hs_code}"
            })

    # 4. HIGH: Quantity Check
    # Extracts numeric quantity from LC raw text to compare with Invoice numeric quantity
    lc_qty = clean_to_float(lc.quantity)
    min_value = min_val(lc_qty, lc.tolerance_plus_percentage)
    max_value = max_val(lc_qty, lc.tolerance_plus_percentage)

    if min_value <= invoice.total_quantity <= max_value:
        pass
    else:
        discrepancies.append({
            'field': 'Quantity Mismatch',
            'severity': 'CRITICAL',
            'message': f"The quantity in Invoice doesn't match with Lc and Falls under the tolerance minimum {min_value} and maximum {max_value}"
        })

    
    # is_profoma = "PROFORMA" in invoice.full_text_raw.upper()

    # if not is_profoma and lc.lc_number not in invoice.full_text_raw:
    #     discrepancies.append({
    #         'field': 'LC Reference',
    #         'severity': 'CRITICAL',
    #         'message': f"LC Number {lc.lc_number} not explicitly mentioned on Invoice."
    #     })
    
    # elif is_profoma:
    #     return ("INFO: Proforma Invoice detected. LC Reference check bypassed.")


    if additional.must_have_exim_code:
        if lc.applicant_Exim_code.strip() != invoice.applicant_Exim_Code.strip():
            discrepancies.append({
            'field': 'Exim Code',
            'severity': 'CRITICAL',
            'message': f"Exim Code is Missing in Invoice"
        })

    
    if additional.must_have_applicant_pan:
        if invoice.applicant_Pan.strip() != lc.applicant_Pan.strip():
            discrepancies.append({
            'field': 'Pan Number',
            'severity': 'CRITICAL',
            'message': f"Pan number missing in Invoice"
        })
            
    if additional. must_be_signed_stamped:
        if not invoice.is_signed:
            discrepancies.append({
            'field': 'Stamp',
            'severity': 'CRITICAL',
            'message': f"Stamp is missing in Invoice"
        })
        if not invoice.is_stamped:
            discrepancies.append({
            'field': 'Signature',
            'severity': 'CRITICAL',
            'message': f"Signature is missing in Invoice"
        })


    score = result(discrepancies)
    return score


def result(discrepancy):
    penalty = 0
    for d in discrepancy:
        if d['severity'] == 'CRITICAL': penalty += 100
        elif d['severity'] == 'HIGH' : penalty += 40
        # elif d['MILD'] == 'MILD' : penalty += 10
        elif d['severity'] == 'LOW' : penalty += 5
    
    score = max(0, 100 - penalty)

    return {
        'Status' : " PASS " if score >= 85 else " FAIL ", 
        'Score' : score, 
        'Discrepancy': discrepancy
    }

def df_result(df):
    pentalty = 0
    for i in df['severity']:
        if i == 'CRITICAL' : pentalty += 100
        elif i == 'HIGH' : pentalty += 40
        elif i == 'LOW' : pentalty += 5

    score = max(0, 100 - pentalty)

    return {
        'Status' : " PASS " if score >= 85 else " FAIL ", 
        'Score' : score
    }

def convert_to_kg(value: float, unit: str) -> float:
    """Convert weight to KGS for comparison"""
    conversions = {
        "KGS": 1.0,
        "KG": 1.0,
        "MT": 1000.0,      # 1 metric ton = 1000 kg
        "MTS": 1000.0,
        "LBS": 0.453592,   # 1 pound = 0.453592 kg
        "LB": 0.453592,
    }
    unit_upper = unit.upper().strip()
    multiplier = conversions.get(unit_upper, 1.0)
    return value * multiplier

    

def compare_lc_bol(lc, bol) -> dict:
    discrepancy = []

    if bol.shipped_date > lc.shipment_date_object:
        discrepancy.append({
            'field': 'Shipment Date',
            'severity': 'CRITICAL',
            'message': f"Bill of landing shipment date exceeds LC shipment date"
        })

    
    normalized_port_dis_Lc = lc.final_destination
    normalized_port_dis_bol = bol.port_of_discharge

    print(f"Normalized Port LC: {normalized_port_dis_Lc}")
    print(f"Normalized Port BOl: {normalized_port_dis_bol}")

    bol_count = normalized_port_dis_bol.split(',')[-1].strip()
    lc_count = normalized_port_dis_Lc.split(',')[-1].strip()

    print(f"Discharge BOL: {bol_count}")
    print(f"Discharge LC :{lc_count}")

    if normalized_port_dis_bol.upper().strip() == normalized_port_dis_Lc.upper().strip():
        pass

    elif bol_count.upper().strip() == lc_count.upper().strip():
        discrepancy.append({
            'field': 'Port of Discharge',
            'severity': 'LOW',
            'message': f"Destination city differs: BOL shows '{bol_count}' vs LC '{lc_count}'. Same country - verify if acceptable."
        })

    else:
        discrepancy.append({
            'field': 'Port of Discharge',
            'severity': 'CRITICAL',
            'message': f"The port of discharge doesn't match BOL: {normalized_port_dis_bol} and LC: {normalized_port_dis_Lc}"
        })

    nor_lc_applicant = normalize_company_name(lc.applicant)
    nor_bol_consignee = normalize_company_name(bol.consignee)

    score = fuzzy_match(nor_bol_consignee, nor_lc_applicant)

    if nor_bol_consignee == nor_lc_applicant:
        pass
    
    elif score >= 0.90:
        discrepancy.append({
            'field': 'Consignee Name in BOL',
            'severity': 'LOW',
            'message': f"Minor difference in consignee name. BOL: '{bol.consignee}' vs LC: '{lc.applicant}'. Most banks will accept but verify."
        })

    else:
        discrepancy.append({
            'field': 'Consignee Name in BOL',
            'severity': 'CRITICAL',
            'message': f"Major difference in consignee name. BOL: '{bol.consignee}' vs LC: '{lc.applicant}'. Most banks likely reject ."
        })

    
    if not bol.is_clean:
        discrepancy.append({
            'field': 'BOL clean',
            'severity': 'CRITICAL',
            'message': f"BOL is not clean - banks require clean BOL"
        })

    if not bol.has_carrier_signature:
        discrepancy.append({
            'field': 'BOL carrier signature',
            'severity': 'CRITICAL',
            'message': f"Missing carrier signature - required by UCP 600"
        })

    bol_weight_in_kg = convert_to_kg(bol.gross_weight_value, bol.gross_weight_unit)
    lc_quantity_kg = clean_to_float(lc.quantity)

    max_allowed = max_val(lc_quantity_kg, lc.tolerance_plus_percentage)
    min_allowed = min_val(lc_quantity_kg, lc.tolerance_minus_percentage)

    if not (min_allowed <= bol_weight_in_kg <= max_allowed):
        discrepancy.append({
            'field': 'Quantity Mismatch',
            'severity': 'HIGH',
            'message': f"Quantity in BOL doesn't match with LC with tolerance "
        })
        
    nor_lc_beneficiary = lc.beneficiary
    nor_bol_beneficiary = bol.shipper

    score2 = fuzzy_match(nor_bol_beneficiary, nor_lc_beneficiary)

    if nor_lc_beneficiary == nor_bol_beneficiary:
        pass
    
    elif score2 >= 0.90:
        discrepancy.append({
            'field': 'Beneficiary name in BOL',
            'severity': 'LOW',
            'message': f"Minor difference in Beneficiary name. BOL: '{bol.shipper}' vs LC: '{lc.beneficiary}'. Most banks will accept but verify."
        })

    else:
        discrepancy.append({
            'field': 'Beneficiary Name in BOL',
            'severity': 'CRITICAL',
            'message': f"Major difference in Beneficiary name. BOL: '{bol.shipper}' vs LC: '{lc.beneficiary}'. Most banks likely reject ."
        })


    lc_desc_clean = smart_ocr_fix(lc.clean_goods_description)
    bol_desc_clean = smart_ocr_fix(bol.description_of_goods)
    
    lc_norm = lc_desc_clean.replace("-", " ").strip()
    bol_norm = bol_desc_clean.replace("-", " ").strip()



    if lc_desc_clean == bol_desc_clean:
        pass
    
    elif lc_desc_clean.upper() == bol_desc_clean.upper():
        discrepancy.append({
            'field': 'Goods Description', 
            'severity': 'LOW', 
            "message": "Casing mismatch. The bank prefers ALL CAPS as per the LC."
        }) 

    elif lc_norm == bol_norm:
        discrepancy.append({
            'field': 'Goods Description', 
            'severity': 'LOW',
            "message": f"Hyphen mismatch! BOL says '{bol.description_of_goods}' but LC requires '{lc.clean_goods_description}'. The bank may charge a $250 fee."
        }) 
    
    else:
        discrepancy.append({
        'field': 'Goods Description', 
        'severity': 'LOW', 
        "message": "Goods description has casing and hyphen mismatch."
        })
    

    lc_upper = lc.place_of_loading_country.upper().strip()
    bol_upper = bol.port_of_loading_country.upper().strip()

    if "ANY PLACE IN" in lc.place_of_loading or "ANY PORT IN" in lc.place_of_loading:

        if lc_upper == bol_upper:
            pass
        else:
             discrepancy.append({
            'field': 'Port in BOL', 
            'severity': 'CRITICAL', 
            "message": f"Port '{bol_upper}' is not in {lc_upper} as required by LC"
            })


    else:
        score3 = fuzzy_match(lc.place_of_loading, bol.port_of_loading )
        if normalize_text(lc.place_of_loading) == normalize_text(bol.port_of_loading):
            pass

        elif score3 >= 0.85:
            discrepancy.append({
            'field': 'Port Mismatch', 
            'severity': 'LOW', 
            "message": f"Minor variation: '{bol.port_of_loading}' vs '{lc.place_of_loading}'"
            })

        else:
             discrepancy.append({
            'field': 'Port Mismtach', 
            'severity': 'CRITICAL', 
            "message": f"Port mismatch: BOL '{bol.port_of_loading}' vs LC '{lc.place_of_loading}'"
        })

    score = result(discrepancy)
    print(score)












    


        





    

    
