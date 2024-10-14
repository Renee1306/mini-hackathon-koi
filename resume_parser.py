import PyPDF2
import requests
import os
from dotenv import load_dotenv

# Load environment variables (Azure API key, URL)
load_dotenv()

API_KEY = os.getenv('AZURE_API_KEY')
API_URL = os.getenv('AZURE_API_URL')

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
    return text

def parse_resume(pdf_path):
    resume_text = extract_text_from_pdf(pdf_path)
    
    # Prepare the OpenAI API request, asking for specific key information
    headers = {
        'Content-Type': 'application/json',
        'api-key': API_KEY,
    }

    data = {
        "messages": [
            {"role": "system", "content": "You are an expert resume parser."},
            {"role": "user", "content": f"Extract and neatly format the following information from this resume: \
                \n1. Full name \
                \n2. Contact information (email, phone number) \
                \n3. Professional summary \
                \n4. Work experience (company names, job titles, duration, key achievements) \
                \n5. Education (degrees, institutions, graduation years) \
                \n6. Skills \
                \nHere is the resume text: {resume_text}"}
        ]
    }

    response = requests.post(API_URL, headers=headers, json=data)
    
    if response.status_code == 200:
        # Process the response to return the neatly formatted information
        result = response.json()
        return format_resume_output(result)
    else:
        return {"error": "Failed to parse resume. Please try again later."}

def format_resume_output(api_response):
    # This assumes that the response will contain structured data about the resume.
    # Extract only the necessary parts and format it neatly.
    content = api_response.get('choices', [{}])[0].get('message', {}).get('content', '')
    
    # Return the formatted output
    return {
        "Extracted Information": content
    }
