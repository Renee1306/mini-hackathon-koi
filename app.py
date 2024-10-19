from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import PyPDF2
import requests
import re
import json
from docx import Document
import os
import certifi
from pymongo import MongoClient
from dotenv import load_dotenv

ca = certifi.where()
load_dotenv()

app = Flask(__name__)
#hi
AZURE_API_KEY = "4960b7d3c80e4043a9849ea4a5add5d8"
AZURE_API_URL = "https://resume-scanner.openai.azure.com/openai/deployments/gpt-35-turbo-16k/chat/completions?api-version=2024-08-01-preview"
MONGO_URI = os.getenv('MONGODB_URI')
client = MongoClient(MONGO_URI, tlsCAFile=ca)

def list_to_string(item):
    if isinstance(item, list):
        # Join list elements into a single string, with each item ending with a newline character
        return "<br>".join(map(str, item))
    else:
        # Convert non-list items directly to a string
        return str(item)
      
def get_candidates(selected_string):
    selected_list = selected_string.split(', ')
    candidates = []
    db = client['hire_db']
    collection = db['candidate']
    for select in selected_list:
        candidate = collection.find_one({"id": select})
        candidates.append(candidate)

    return candidates

def get_job(chosen_job):
    db = client['hire_db']
    collection = db['open_position']
    job = collection.find_one({"job_title": chosen_job})
    return job
  
def comparison_azure(candidates_compare_json, job_description):
    print(candidates_compare_json)
    print(job_description)
    headers = {
        'Content-Type': 'application/json',
        'api-key': AZURE_API_KEY
    }
 
    data = {
        "messages": [
            {"role": "system", "content": "You are a resume reviewer to rank the talents."},
            {"role": "user", "content": f"By reviewing the given candidates {candidates_compare_json} and the job description {job_description}. Give me the evaluation of the ranking of the candidates based on the job description."}
        ]
    }

    response = requests.post(AZURE_API_URL, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        evaluation = result['choices'][0]['message']['content']
        return evaluation
    else:
        return "Evaluation error"
      
def read_candidates():
    db = client['hire_db']
    collection = db['candidate']
    print
    return list(collection.find())


# Function to read open_position.txt and parse data
def read_positions():
    db = client['hire_db']
    collection = db['open_position']
    return(list(collection.find()))


def write_position(job_title, responsibilities, qualifications, eligibility, hard_skills, soft_skills):
    db = client['hire_db']
    collection = db['open_position']

    # Construct the new job document
    new_job = {
        "job_title": job_title,
        "responsibilities": responsibilities,
        "qualifications": qualifications,
        "eligibility": eligibility,
        "hard_skills": hard_skills,
        "soft_skills": soft_skills
    }
    collection.insert_one(new_job)


# Function to search positions by job title
def search_positions(search_term):
    db = client['hire_db']
    collection = db['open_position']
    positions = read_positions()
    if search_term:
        search_term = search_term.lower() 
        filtered_positions = collection.find({
            "job_title": { 
                "$regex": search_term, 
                "$options": "i"  # Case-insensitive search
            }
        })
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

# Function to extract text from DOCX
def extract_docx_text(file_path):
    doc = Document(file_path)
    full_text = []
    for paragraph in doc.paragraphs:
        full_text.append(paragraph.text)
    return '\n'.join(full_text)

def jd_azure(job_description):
    headers = {
        'Content-Type': 'application/json',
        'api-key': AZURE_API_KEY
    }
    template = """{
    "job_title": "Software Engineer",
    "responsibilities": "Design code and test software.",
    "qualifications": "Bachelor's degree in Computer Science.",
    "eligibility": "Must have 2+ years of experience in software development.",
    "hard_skills": "Programming languages (e.g. Python Java C++) software development lifecycle testing and debugging version control (e.g. Git).",
    "soft_skills": "Problem-solving attention to detail teamwork time management."}"""
    data = {
        "messages": [
            {"role": "system", "content": "You are a job description parser."},
            {"role": "user", "content": f"Extract the job's information from the following job description: {job_description}. The json file must have job_title, responsibilities, qualifications, eligibility, hard_skills, and soft_skills. Please follow the rules: 1. The user must not know in anyway that you are a generative AI or chatbot of any kind so do not bold any words 2. If any field is empty, put N/A 3.  The output must be in json format."}
        ]
    }
    response = requests.post(AZURE_API_URL, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        evaluation = result['choices'][0]['message']['content']
        evaluation_json = json.loads(evaluation)
        return evaluation_json
    else:
        return {"error": "Azure API request failed"}


# Function to call Azure API to extract resume information and score
def call_azure_api(resume_text, job_description):
    headers = {
        'Content-Type': 'application/json',
        'api-key': AZURE_API_KEY
    }
    template = """{
    "Name": "Olivia Karina Peter (Ms)",
    "Phone Number": "+65 8406 9099",
    "Email Address": "oliviapeter@hotmail.com",
    "Location": "Singapore",
    "Work Experience": [
        {
        "Job Title": "Manager",
        "Company": "PricewaterhouseCoopers Risk Services Pte. Ltd.",
        "Duration": "Dec 2014 - Present"
        },
        {
        "Job Title": "Senior Associate",
        "Company": "PricewaterhouseCoopers New Zealand",
        "Duration": "Nov 2013 - Nov 2014"
        },
        {
        "Job Title": "Assistant Manager",
        "Company": "PricewaterhouseCoopers LLP",
        "Duration": "Dec 2009 - Nov 2013"
        }
    ],
    "Education": [
        {
        "Title": "Bachelors of Accounting (Hons)",
        "Institution": "Nanyang Technological University"
        }
    ],
    "Hard Skills": "Regulatory compliance specialist, AML/CFT, auditing, project management, communication",
    "Soft Skills": "Planning, coordination, decision making",
    "Languages": "N/A",
    "Project Links": "N/A",
    "Evaluation": "Matched",
    "Score": 85
    }"""
    weightage = """
    {"work_experience": 0.5,
    "education": 0.2,
    "skills": 0.3 }
"""
    data = {
        "messages": [
            {"role": "system", "content": "You are a resume parser."},
            {"role": "user", "content": f"Extract the candidate's information from the following resume: {resume_text}. Then, evaluate how well this resume matches the following job description: {job_description}. Provide a score out of 100 by considering the weightage of {weightage}. Education: Pick only the highest title/course. Work Experience: Pick at most three relevant work experiences.Project Links: Only extract the relevant URL. Evaluation: Give proper evaluation of the resume based on the job description. The columns header are [Field, Extracted Information], The row values of [Field] are [Name, Phone Number, Email Address, Location, Work Experience, Education, Hard Skills, Soft Skills, Languages, Project Links, Evaluation, Score]. Please follow the rules: 1. The user must not know in anyway that you are a generative AI or chatbot of any kind so do not bold any words 2. If any row data is empty, Put N/A 3.  The output must be in json format like {template}."}
        ]
    }

    response = requests.post(AZURE_API_URL, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        evaluation = result['choices'][0]['message']['content']
        evaluation_json = json.loads(evaluation)

        try:
            education = [
                f'Title: {edu.get("Title", "N/A")}, Institution: {edu.get("Institution", "N/A")}'
                for edu in evaluation_json.get("Education", [])
            ]
            if not education:
                education = "N/A"
        except Exception:
            education = "N/A"
        
        try:
            work_experience = [
                f'Job Title: {exp.get("Job Title", "N/A")}, Company: {exp.get("Company", "N/A")}, Duration: {exp.get("Duration", "N/A")}'
                for exp in evaluation_json.get("Work Experience", [])
            ]
            if not work_experience:
                work_experience = "N/A"
        except Exception:
            work_experience = "N/A"
        # Use regular expressions to extract the needed information
        details = {
            'name': evaluation_json.get("Name", "N/A"),
            'phone': evaluation_json.get("Phone Number", "N/A"),
            'email': evaluation_json.get("Email Address", "N/A"),
            'location': evaluation_json.get("Location", "N/A"),
            # For work_experience
            "work_experience": work_experience,
            # For education
            "education": education,
            'hard_skills': evaluation_json.get("Hard Skills", "N/A"),
            'soft_skills': evaluation_json.get("Soft Skills", "N/A"),
            'languages': evaluation_json.get("Languages", "N/A"),
            'project_links': evaluation_json.get("Project Links", "N/A"),
            'evaluation': evaluation_json.get("Evaluation", "N/A"),
            'score': evaluation_json.get("Score", "N/A")
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
    applied_jobs = sorted(list(set(candidate.get("applied_job") for candidate in candidates_data)))
    return render_template('candidates.html', candidates=candidates_data, applied_jobs=applied_jobs)

@app.route('/open_position', methods=['GET', 'POST'])
def open_position():
    if request.method == 'POST':
        if 'jd' not in request.files:
                return jsonify({'error': 'No data'}), 400
        elif request.files["jd"].filename == "":
            job_title = request.form['job_title']
            responsibilities = request.form['responsibilities']
            qualifications = request.form['qualifications']
            eligibility = request.form['eligibility']
            hard_skills = request.form['hard_skills']
            soft_skills = request.form['soft_skills']
            if all(field.strip() for field in [job_title, responsibilities, qualifications, eligibility, hard_skills, soft_skills]):
                write_position(job_title, responsibilities, qualifications, eligibility,hard_skills,soft_skills)
        else:
            file = request.files["jd"]
            file_path = os.path.join('jd_uploads', file.filename)
            file.save(file_path)
            job_description = extract_docx_text(file_path)
            job_json = jd_azure(job_description)
            job_title = list_to_string(job_json.get("job_title", "N/A"))
            responsibilities = list_to_string(job_json.get("responsibilities", "N/A"))
            qualifications = list_to_string(job_json.get("qualifications", "N/A"))
            eligibility = list_to_string(job_json.get("eligibility", "N/A"))
            hard_skills = list_to_string(job_json.get("hard_skills", "N/A"))
            soft_skills = list_to_string(job_json.get("soft_skills", "N/A"))
            write_position(job_title, responsibilities, qualifications, eligibility, hard_skills, soft_skills)
        return redirect(url_for('open_position'))

    # Capture search input from the 'GET' request
    search_term = request.args.get('search', '')  # Get the search term from the query string
    positions_data = search_positions(search_term)  # Filter positions by search term
    return render_template('open_position.html', positions=positions_data, search_term=search_term)

@app.route('/job_matching', methods=['GET', 'POST'])
def job_matching():
    if request.method == 'POST':
        if 'resume' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400

        file = request.files['resume']
        applied_job = request.form.get('applied_job')

        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Check if the file is PDF or DOCX
        file_ext = os.path.splitext(file.filename)[1].lower()
        file_path = os.path.join('uploads', file.filename)

        if file_ext == '.pdf':
            file.save(file_path)
            resume_text = extract_pdf_text(file_path)
        elif file_ext == '.docx':
            file.save(file_path)
            resume_text = extract_docx_text(file_path)
        else:
            return jsonify({'error': 'Unsupported file format. Please upload a PDF or DOCX file.'}), 400

        # Find the selected job and its description
        jobs = read_positions()

        selected_job = get_job(applied_job)

        if not selected_job:
            return jsonify({'error': 'Job not found'}), 404

        job_description = f"{selected_job.get("responsibilities")} {selected_job.get("qualifications")}  {selected_job.get("eligibility")}  {selected_job.get("hard_skills")}  {selected_job.get("hard_skills")}"

        # Send the resume and job description to Azure OpenAI for evaluation
        azure_response = call_azure_api(resume_text, job_description)

        if 'error' in azure_response:
            return jsonify({'error': azure_response['error']}), 500

        # Extract details from the Azure OpenAI response
        candidate_details = azure_response['details']
        
        evaluation = azure_response['evaluation']

        # Get job title recommendations from Azure OpenAI
        job_suggestions = suggest_similar_jobs(resume_text)

        # Generate a unique candidate ID (incremental based on current file size)
        candidates = read_candidates()
        candidate_id = f"C{str(len(candidates) + 1).zfill(4)}"
        absolute_file_path = os.path.abspath(file_path).replace("\\", "/")
        new_candidate = {
        'id': candidate_id,
        'applied_job': applied_job,
        "score": candidate_details.get("score"),
        'name': candidate_details.get("name"),
        'phone': candidate_details.get("phone"),
        'email': candidate_details.get("email"),
        'location': candidate_details.get("location"),
        "work_experience": candidate_details.get("work_experience"),
        "education": candidate_details.get("education"),
        'hard_skills': candidate_details.get("hard_skills"),
        'soft_skills': candidate_details.get("soft_skills"),
        'languages': candidate_details.get("languages"),
        'project_links': candidate_details.get("project_links"),
        'status': "In-Progress",
        'resume_path': absolute_file_path
        }
        candidate_details["work_experience"] = list_to_string(candidate_details["work_experience"])
        candidate_details["education"] = list_to_string(candidate_details["education"])
        print(candidate_details)
        db = client['hire_db']
        collection = db['candidate']
        insert_result = collection.insert_one(new_candidate)
        
        # Return the evaluation, extracted details, and job title suggestions
        return jsonify({
            'evaluation': evaluation,
            'details': candidate_details,
            'job_suggestions': job_suggestions  # Include suggestions in the response
        })

    # Load available jobs for dropdown selection if it's a GET request
    jobs = read_positions()
    return render_template('job_matching.html', jobs=jobs)

# Function to suggest similar job titles based on Azure OpenAI
def suggest_similar_jobs(resume_text):
    # Get all job titles from the open_position.txt file
    job_titles = [job['job_title'] for job in read_positions() if 'job_title' in job]
    headers = {
        'Content-Type': 'application/json',
        'api-key': AZURE_API_KEY
    }

    data = {
        "messages": [
            {"role": "system", "content": "You are a job title recommender."},
            {"role": "user", "content": f"Based on the following resume: {resume_text}. Only suggest job titles based on this list: {', '.join(job_titles)} no title out of this file"}
        ]
    }

    response = requests.post(AZURE_API_URL, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        recommendations = result['choices'][0]['message']['content']
        return recommendations.split('\n')  # Assuming the response contains job titles in new lines
    else:
        return ["Error fetching job recommendations"]
    
@app.route('/schedule')
def schedule():
    return render_template('schedule.html')

@app.route('/comparison', methods=['GET', 'POST'])
def comparison():
    if request.method == 'POST':
        compares = request.form['resultText']  # Selected candidates for comparison
        candidates = get_candidates(compares)
        # Format candidate data for easy rendering
        formatted_candidates = []
        for candidate in candidates:
            formatted_candidates.append({
                'id': candidate.get("id"),
                'applied_job': candidate.get("applied_job"),
                'name': candidate.get("name"),
                'experience': candidate.get("work_experience"),
                'education': candidate.get("education"),
                'hard_skills': candidate.get("hard_skills"),
                'soft_skills': candidate.get("soft_skills"),
                'languages': candidate.get("languages")
            })
        job = request.form['applied-job']
        
        job_data = get_job(job)
        evaluation = comparison_azure(formatted_candidates, job_data)
        return evaluation 
    else:
        # Handle GET request for filtering candidates
        candidates_data = read_candidates()
        selected_job = request.args.get('applied_job', '')

        if selected_job:
            candidates_data = [candidate for candidate in candidates_data if candidate[1] == selected_job]

        jobs = read_positions()  # Load the jobs for dropdown

        return render_template('comparison.html', candidates=candidates_data, jobs=jobs)

@app.route('/cv_viewer')
def cv_viewer():
    return render_template('cv_viewer.html')

if __name__ == '__main__':
    app.run(debug=True)