from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2
import re
import io
from typing import List, Dict
import os

app = FastAPI()

# Enable CORS for frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Model once
model = SentenceTransformer('all-MiniLM-L6-v2')

def extract_text_from_pdf(pdf_file) -> str:
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file))
        text = ""
        max_pages = min(len(pdf_reader.pages), 20)
        for page_num in range(max_pages):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n"
        return text
    except Exception:
        return ""

def extract_text_from_docx(docx_file) -> str:
    try:
        from docx import Document
        doc = Document(io.BytesIO(docx_file))
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception:
        return ""

def clean_text(text: str) -> str:
    text = re.sub(r'http\S+|www.\S+|\S+@\S+', '', text)
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text.lower()).strip()
    return text

def extract_skills(text: str) -> List[str]:
    skills_dictionary = [
        'python', 'java', 'c++', 'javascript', 'typescript', 'sql', 'r', 'scala',
        'react', 'angular', 'vue', 'node.js', 'django', 'flask', 'fastapi',
        'aws', 'azure', 'gcp', 'kubernetes', 'docker', 'jenkins', 'terraform',
        'machine learning', 'deep learning', 'nlp', 'computer vision',
        'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy',
        'data analysis', 'data science', 'data engineering', 'analytics',
        'mongodb', 'postgresql', 'mysql', 'cassandra',
        'git', 'github', 'gitlab', 'agile', 'scrum',
        'leadership', 'communication', 'problem solving', 'teamwork',
        'project management', 'critical thinking',
        'rest api', 'graphql', 'microservices', 'devops', 'ci/cd',
        'linux', 'windows', 'bash', 'shell scripting',
        'html', 'css', 'web development', 'mobile development', 'ios', 'android'
    ]
    text_lower = text.lower()
    found_skills = [skill for skill in skills_dictionary if skill in text_lower]
    return list(set(found_skills))

@app.post("/api/rank")
async def rank(job_description: str = Form(...), files: List[UploadFile] = File(...)):
    resumes = {}
    for file in files:
        content = await file.read()
        if file.filename.endswith('.pdf'):
            text = extract_text_from_pdf(content)
        elif file.filename.endswith('.docx'):
            text = extract_text_from_docx(content)
        else:
            text = ""
        
        if text.strip():
            resumes[file.filename] = text

    if not resumes:
        return JSONResponse(content={"error": "No valid resumes found"}, status_code=400)

    # Processing logic
    job_skills = extract_skills(job_description)
    cleaned_job = clean_text(job_description)
    job_embedding = model.encode([cleaned_job])[0]

    resume_names = list(resumes.keys())
    resume_texts = list(resumes.values())
    cleaned_resumes = [clean_text(t) for t in resume_texts]
    resume_embeddings = model.encode(cleaned_resumes)

    similarities = cosine_similarity([job_embedding], resume_embeddings)[0]
    
    results = []
    for idx, name in enumerate(resume_names):
        similarity_score = float(similarities[idx])
        resume_skills = extract_skills(resume_texts[idx])
        matched_skills = list(set(job_skills) & set(resume_skills))
        missing_skills = list(set(job_skills) - set(resume_skills))
        
        results.append({
            'candidate_name': name,
            'score': round(similarity_score * 100, 1),
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'match_count': len(matched_skills)
        })

    results.sort(key=lambda x: x['score'], reverse=True)
    return {"results": results, "job_skills_count": len(job_skills)}

# Root endpoint for Vercel
@app.get("/")
async def root():
    return {"message": "Resume Screening API is running"}
