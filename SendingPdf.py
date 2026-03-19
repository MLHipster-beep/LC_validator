from google import genai
from google.genai import types

client = genai.Client(api_key="AIzaSyD5AEioj294fNVLGsp5PGw1dda0k86jJpM") #lucky, carp 

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
