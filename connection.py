import os
import certifi
from pymongo import MongoClient
from dotenv import load_dotenv

ca = certifi.where()

load_dotenv()

MONGO_URI = os.getenv('MONGODB_URI')

client = MongoClient(MONGO_URI, tlsCAFile=ca)
print("yes")
db = client['hire_db']
collection = db['candidate'] # open_position/candidate

# Example document
# new_job1 = {
#     "job_title": "Software Engineer",
#     "responsibilities": "Design, code, and test software.",
#     "qualifications": "Bachelor's degree in Computer Science",
#     "eligibility": "Must have 2+ years of experience in software development.",
#     "hard_skills": "Programming languages (e.g., Python, Java, C++), software development lifecycle, testing and debugging, version control (e.g., Git).",
#     "soft_skills": "Problem-solving, attention to detail, teamwork, time management."
# }
# new_job2 = {
#     "job_title": "Data Analyst",
#     "responsibilities": "Collect, clean, and interpret data.",
#     "qualifications": "Bachelor's degree in a related field.",
#     "eligibility": "1+ years of experience in data analysis.",
#     "hard_skills": "Data cleaning, statistical analysis, data visualization (e.g., Tableau, Power BI), SQL, Excel.",
#     "soft_skills": "Analytical thinking, communication, critical thinking, adaptability."
# }

# new_job3 = {
#     "job_title": "HR Manager",
#     "responsibilities": "Recruit, train, and manage employees.",
#     "qualifications": "Bachelor's degree in HR or related field.",
#     "eligibility": "3+ years of experience in HR management, proven ability to handle sensitive data and maintain confidentiality.",
#     "hard_skills": "Employee relations, talent acquisition, payroll management, HR software (e.g., Workday, BambooHR), labor law knowledge.",
#     "soft_skills": "Leadership, communication, conflict resolution, problem-solving, organizational skills."
# }
# new_job4 = {
#     "job_title": "Marketing Specialist",
#     "responsibilities": "Assisting with the production of creative marketing copy and digital marketing materials such as web design, content writing, social content, PPC, SEO, and influencer marketing.\nManaging multiple social media channels.\nPlanning and reporting on marketing campaigns.\nConducting necessary research to write informative yet engaging content.\nProofreading and editing articles and blogs.\nWorking collaboratively with the creative team and marketing team.\nOther ad-hoc duties as required.",
#     "qualifications": "A natural flair for creative and informative writing.\nA strong desire to learn and develop new skills.\nThe ability to prioritize work and complete tasks to meet deadlines.\nThe ability to be a team player who can also work autonomously.\nBilingual is welcome but not required.",
#     "eligibility": "This position is open to Malaysian citizens and candidates with full working rights in Malaysia.\nNo remote work is available; only genuine candidates who are committed to career growth.",
#     "hard_skills": "Content creation\nSEO\nSocial media management\nCopywriting\nPPC advertising\nMarket research",
#     "soft_skills": "Creativity\nCommunication\nTeamwork\nTime management\nAdaptability"
# }

new_candidate1 = {'id': 'C0001', 'applied_job': 'Software Engineer', 'score': '85', 'name': 'Long Qin Hui', 'phone': '+60123456789', 'email': 'qin.hui@example.com', 'location': 'Kuala Lumpur, Malaysia', 'work_experience': ['5 years at XYZ Software'], 'education': ['Bachelor of Computer Science'], 'hard_skills': 'Java, Python, SQL', 'soft_skills': 'Teamwork, Problem-solving', 'languages': 'English, Mandarin', 'project_links': 'https://github.com/qinhui', 'status': 'Accepted', 'resume_path': 'C:/Users/longh/Documents/experian/uploads/Long Qin Hui CV 07_10.pdf'}

new_candidate2 = {'id': 'C0002', 'applied_job': 'Software Engineer', 'score': '100', 'name': 'Nyong Chin Venn', 'phone': '+60129876543', 'email': 'chin.venn@example.com', 'location': 'Penang, Malaysia', 'work_experience': ['3 years at ABC Solutions'], 'education': ['Master of Information Technology'], 'hard_skills': 'C++, PHP, JavaScript', 'soft_skills': 'Leadership, Time Management', 'languages': 'English, Malay', 'project_links': 'https://portfolio.example.com/nyongvenn', 'status': 'In-Progress', 'resume_path': 'C:/Users/longh/Documents/experian/uploads/Long Qin Hui CV 07_10.pdf'}

new_candidate3 = {'id': 'C0003', 'applied_job': 'Software Engineer', 'score': '99', 'name': 'Ethan Walker', 'phone': '+60134567890', 'email': 'ethan.walker@example.com', 'location': 'Singapore', 'work_experience': ['4 years at DEF Tech'], 'education': ['Bachelor of Software Engineering'], 'hard_skills': 'Python, Django, Java', 'soft_skills': 'Communication, Critical Thinking', 'languages': 'English', 'project_links': 'https://linkedin.com/in/ethanwalker', 'status': 'In-Progress', 'resume_path': 'C:/Users/longh/Documents/experian/uploads/Long Qin Hui CV 07_10.pdf'}

# Insert the document into the collection
# insert_result = collection.insert_many([new_job1, new_job2, new_job3, new_job4])
test =list(collection.find())
print(test)

# collection.insert_many([new_candidate1, new_candidate2, new_candidate3])
# List of IDs to delete
ids_to_delete = ["C0004", "C0005", "C0006", "C0007"]

# Delete documents with the specified IDs
result = collection.delete_many({"id": {"$in": ids_to_delete}})

# Print the number of documents deleted
print(f'Deleted {result.deleted_count} documents.')