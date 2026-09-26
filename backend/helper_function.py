import json
from pydantic import ValidationError
from SendingPdf import send_pdf, send_text

def get_structured_data(prompt, file_name, schema):

    try:
        if hasattr(file_name, 'seek'):
            file_name.seek(0)

        raw_json = send_pdf(prompt = prompt, file_name = file_name, schema = schema )
        response_dict = json.loads(raw_json)
        
        structured_lc = schema(**response_dict)
        return structured_lc
        
    except json.JSONDecodeError:
        print("Failed to decode JSON from AI response.")
        print(f"Raw Output: {raw_json}")
    except ValidationError as e:
        print(f"Pydantic Validation Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    
    return None

def get_structured_data_text(prompt, text, schema):
     
    try:
        raw_json = send_text(prompt = prompt, text = text, schema = schema )

        response_dict = json.loads(raw_json)
        
        structured_lc = schema(**response_dict)

        return structured_lc
        
    except json.JSONDecodeError:
        print("Failed to decode JSON from AI response.")
        print(f"Raw Output: {raw_json}")
    except ValidationError as e:
        print(f"Pydantic Validation Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return None




