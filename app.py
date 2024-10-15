from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import PyPDF2
import requests
import re

app = Flask(__name__)

# Azure API details
AZURE_API_KEY = os.getenv('AZURE_API_KEY', '1841c227a9fb4e93ad18cbdefc4d4b10')
AZURE_API_URL = os.getenv('AZURE_API_URL', 'https://resumescreener.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-08-01-preview')

# Function to read candidates.txt and parse data
def read_candidates():
    candidates = []
    with open('database/candidates.txt', 'r') as file:
        for line in file:
            # Split each line by the '|' character and store it as a list
            candidate_data = line.strip().split('|')
            candidates.append(candidate_data)
    return candidates

# Function to read open_position.txt and parse data
def read_positions():
    positions = []
    with open('database/open_position.txt', 'r') as file:
        for line in file:
            position_data = line.strip().split('|')
            # Replace commas with newlines for proper display in HTML
            position_data[1] = position_data[1].replace(', ', '\n')  # Responsibilities
            position_data[2] = position_data[2].replace(', ', '\n')  # Qualifications
            position_data[3] = position_data[3].replace(', ', '\n')  # Eligibility
            positions.append(position_data)
    return positions

# Function to sanitize input by replacing newlines with commas
def sanitize_input(text):
    return text.replace('\n', ', ').replace('\r', '')  # Replaces newlines with commas

# Function to append new job details to open_position.txt
def write_position(job_title, responsibilities, qualifications, eligibility):
    job_title = sanitize_input(job_title)
    responsibilities = sanitize_input(responsibilities)
    qualifications = sanitize_input(qualifications)
    eligibility = sanitize_input(eligibility)

    with open('database/open_position.txt', 'a') as file:
        file.write(f"{job_title}|{responsibilities}|{qualifications}|{eligibility}\n")

# Function to search positions by job title
def search_positions(search_term):
    positions = read_positions()
    if search_term:
        search_term = search_term.lower()  # Normalize the search term
        filtered_positions = [position for position in positions if search_term in position[0].lower()]
        return filtered_positions
    return positions

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

# Function to call Azure API to extract resume information and score
def call_azure_api(resume_text, job_description):
    headers = {
        'Content-Type': 'application/json',
        'api-key': AZURE_API_KEY
    }

    data = {
        "messages": [
            {"role": "system", "content": "You are a resume parser."},
            {"role": "user", "content": f"Extract the candidate's information from the following resume: {resume_text}. Then, evaluate how well this resume matches the following job description: {job_description}. Provide a score out of 100. Education: Pick only the highest title/course and extract in this format - Title: ....\nInstitution:...\nResults:.... For example: Job Title: Business Sales Analyst Intern Company: Nestlé Duration: Mar 2022 - Oct 2023 Job Title: Coding Tutor Company: Build A Code Duration: Dec 2023 - Apr 2024 Work Experience: Pick relevant work experiences and each experience in this format Job Title: ....\nCompany:....\nDuration:..... For example: Title: BSc (Hons) Computer Science (Data Analytics) Institution: Asia Pacific University of Technology & Innovation Results: Current CGPA: 3.73 Project Links: Only extract the relevant URL. The output must be in table format. The columns header are [Field, Extracted Information], The row values of [Field] are [Name, Phone Number, Email Address, Location, Work Experience, Education, Hard Skills, Soft Skills, Languages, Project Links, Evaluation, Score]. Please follow the rules: 1. The user must not know in anyway that you are a generative AI or chatbot of any kind so do not bold any words 2. If any row data is empty, Put N/A "}
            
        ]
    }

    response = requests.post(AZURE_API_URL, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        evaluation = result['choices'][0]['message']['content']
        print(evaluation)
        # Use regular expressions to extract the needed information
        details = {
            'name': re.search(r'\|\s*Name\s*\|\s*(.+?)\s*\|', evaluation).group(1) if re.search(r'\|\s*Name\s*\|\s*(.+?)\s*\|', evaluation) else 'N/A',
            'phone': re.search(r'\|\s*Phone Number\s*\|\s*(.+?)\s*\|', evaluation).group(1) if re.search(r'\|\s*Phone Number\s*\|\s*(.+?)\s*\|', evaluation) else 'N/A',
            'email': re.search(r'\|\s*Email Address\s*\|\s*(.+?)\s*\|', evaluation).group(1) if re.search(r'\|\s*Email Address\s*\|\s*(.+?)\s*\|', evaluation) else 'N/A',
            'location': re.search(r'\|\s*Location\s*\|\s*(.+?)\s*\|', evaluation).group(1) if re.search(r'\|\s*Location\s*\|\s*(.+?)\s*\|', evaluation) else 'N/A',
            'work_experience': re.search(r'\|\s*Work Experience\s*\|\s*(.+?)\s*\|', evaluation).group(1) if re.search(r'\|\s*Work Experience\s*\|\s*(.+?)\s*\|', evaluation) else 'N/A',
            'education': re.search(r'\|\s*Education\s*\|\s*(.+?)\s*\|', evaluation).group(1) if re.search(r'\|\s*Education\s*\|\s*(.+?)\s*\|', evaluation) else 'N/A',
            'hard_skills': re.search(r'\|\s*Hard Skills\s*\|\s*(.+?)\s*\|', evaluation).group(1) if re.search(r'\|\s*Hard Skills\s*\|\s*(.+?)\s*\|', evaluation) else 'N/A',
            'soft_skills': re.search(r'\|\s*Soft Skills\s*\|\s*(.+?)\s*\|', evaluation).group(1) if re.search(r'\|\s*Soft Skills\s*\|\s*(.+?)\s*\|', evaluation) else 'N/A',
            'languages': re.search(r'\|\s*Languages\s*\|\s*(.+?)\s*\|', evaluation).group(1) if re.search(r'\|\s*Languages\s*\|\s*(.+?)\s*\|', evaluation) else 'N/A',
            'project_links': re.search(r'\|\s*Project Links\s*\|\s*(.+?)\s*\|', evaluation).group(1) if re.search(r'\|\s*Project Links\s*\|\s*(.+?)\s*\|', evaluation) else 'N/A',
            'evaluation': re.search(r'\|\s*Evaluation\s*\|\s*(.+?)\s*\|', evaluation).group(1) if re.search(r'\|\s*Evaluation\s*\|\s*(.+?)\s*\|', evaluation) else 'N/A',
            'score': re.search(r'\|\s*Score\s*\|\s*(\d+)(?:/\d+)?\s*\|', evaluation).group(1) if re.search(r'\|\s*Score\s*\|\s*(\d+)(?:/\d+)?\s*\|', evaluation) else 'N/A'
        }

        return {'evaluation': evaluation, 'details': details}
    else:
        return {"error": "Azure API request failed"}
    
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/candidates')
def candidates():
    candidates_data = read_candidates()
    return render_template('candidates.html', candidates=candidates_data)

@app.route('/open_position', methods=['GET', 'POST'])
def open_position():
    if request.method == 'POST':
        job_title = request.form['job_title']
        responsibilities = request.form['responsibilities']
        qualifications = request.form['qualifications']
        eligibility = request.form['eligibility']
        write_position(job_title, responsibilities, qualifications, eligibility)
        return redirect(url_for('open_position'))

    # Capture search input from the 'GET' request
    search_term = request.args.get('search', '')  # Get the search term from the query string
    positions_data = search_positions(search_term)  # Filter positions by search term
    return render_template('open_position.html', positions=positions_data, search_term=search_term)

# Job matching page route
@app.route('/job_matching', methods=['GET', 'POST'])
def job_matching():
    if request.method == 'POST':
        if 'resume' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['resume']
        applied_job = request.form.get('applied_job')

        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        if file and file.filename.endswith('.pdf'):
            file_path = os.path.join('uploads', file.filename)
            file.save(file_path)

            resume_text = extract_pdf_text(file_path)

            jobs = load_jobs()
            selected_job = next((job for job in jobs if job['title'] == applied_job), None)

            if not selected_job:
                return jsonify({'error': 'Job not found'}), 404

            job_description = f"{selected_job['description']} {selected_job['qualification']} {selected_job['experience']}"

            # Send the resume and job description to Azure OpenAI
            azure_response = call_azure_api(resume_text, job_description)

            if 'error' in azure_response:
                return jsonify({'error': azure_response['error']}), 500

            # Extract details from the response
            candidate_details = azure_response['details']
            evaluation = azure_response['evaluation']

            # Generate a unique candidate ID (incremental based on current file size)
            candidates = read_candidates()
            candidate_id = f"C{str(len(candidates) + 1).zfill(4)}"

            # Save the candidate's details into candidates.txt
            with open('database/candidates.txt', 'a') as file:
                file.write(f"{candidate_id}|{applied_job}|{candidate_details['score']}|{candidate_details['name']}|{candidate_details['phone']}|{candidate_details['email']}|{candidate_details['location']}|{candidate_details['work_experience']}|{candidate_details['education']}|{candidate_details['hard_skills']}|{candidate_details['soft_skills']}|{candidate_details['languages']}|{candidate_details['project_links']}|In-Progress\n")

            # Return evaluation and extracted details
            return jsonify({
                'evaluation': evaluation,
                'details': candidate_details
            })

    # Load available jobs for dropdown selection
    jobs = load_jobs()
    return render_template('job_matching.html', jobs=jobs)

@app.route('/schedule')
def schedule():
    return render_template('schedule.html')

@app.route('/support')
def support():
    return render_template('support.html')

if __name__ == '__main__':
    app.run(debug=True)