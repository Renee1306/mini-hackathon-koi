import os
import PyPDF2
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

AZURE_API_KEY = os.getenv('AZURE_API_KEY', '4960b7d3c80e4043a9849ea4a5add5d8')
AZURE_API_URL = os.getenv('AZURE_API_URL', 'https://resume-scanner.openai.azure.com/openai/deployments/gpt-35-turbo-16k/chat/completions?api-version=2024-08-01-preview')

# Function to extract text from PDF
def extract_pdf_text(file_path):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page in range(len(reader.pages)):
            text += reader.pages[page].extract_text()
        return text

# Function to load job positions from the file
def load_jobs():
    jobs = []
    with open('database/open_position.txt', 'r') as f:
        for line in f:
            parts = line.strip().split('|')
            job = {
                'title': parts[0],
                'description': parts[1],
                'qualification': parts[2],
                'experience': parts[3]
            }
            jobs.append(job)
    return jobs

# Function to call Azure API to score the resume against the job description
def call_azure_api(resume_text, job_description):
    headers = {
        'Content-Type': 'application/json',
        'api-key': AZURE_API_KEY
    }

    data = {
        "messages": [
            {"role": "system", "content": "You are a resume parser."},
            {"role": "user", "content": f"Evaluate how well this resume matches the following job description: {job_description}. Here is the resume: {resume_text}. Give Your comment of whether or not to hire this candidate for this position."}
        ]
    }

    response = requests.post(AZURE_API_URL, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Azure API request failed"}

@app.route('/get_jobs', methods=['GET'])
def get_jobs():
    jobs = load_jobs()
    return jsonify([{"title": job['title']} for job in jobs])

@app.route('/')
def index():
    return render_template('test.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'resume' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['resume']
    applied_job = request.form.get('applied_job')

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and file.filename.endswith('.pdf'):
        file_path = os.path.join('uploads', file.filename)
        file.save(file_path)

        # Extract text from the uploaded PDF
        resume_text = extract_pdf_text(file_path)

        # Load the selected job description
        jobs = load_jobs()
        selected_job = next((job for job in jobs if job['title'] == applied_job), None)

        if not selected_job:
            return jsonify({'error': 'Job not found'}), 404

        job_description = f"{selected_job['description']} {selected_job['qualification']} {selected_job['experience']}"

        # Send the resume and job description to Azure OpenAI
        azure_response = call_azure_api(resume_text, job_description)

        if 'error' in azure_response:
            return jsonify({'error': azure_response['error']}), 500

        # Extract score (assuming Azure returns a score in its response)
        score = azure_response['choices'][0]['message']['content']

        # Return the name and score in the response
        extracted_info = {
            'Name': 'Extracted from resume',  # Implement proper name extraction if needed
            'Score': score
        }

        return jsonify(extracted_info)

    return jsonify({'error': 'Unsupported file format'}), 400

if __name__ == '__main__':
    app.run(debug=True)
