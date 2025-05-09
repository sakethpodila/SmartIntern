from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
from agents.resume_parser import traditional_resume_parser, llm_resume_parser, reconcile_parsed_outputs
from agents.chatbot import get_llm_response
from agents.extract_query import generate_query_for_jobsearch
from agents.job_search import get_jobs
from agents.embed import get_embeddings
from vectorDB import VectorDatabase
import os
import fitz
import docx2txt
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


# ------------------------------ Initializing Global Variables for easy access ------------------------------------------

# LLM_MODEL = "google/flan-t5-base"
# EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


# Get the Hugging Face API from .env file
load_dotenv()
hf_api_key = os.getenv('HF_API_KEY')
openai_api_key = os.getenv('OPENAI_API_KEY')

# llm_api_url = f"https://api-inference.huggingface.co/models/{LLM_MODEL}"

# openai_api_url = "https://api.openai.com/v1/chat/completions"

# embedding_api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{EMBEDDING_MODEL}"

# hf_headers = {
#             "Authorization": f"Bearer {hf_api_key}",
#             }

openai_headers = {
    "Authorization": f"Bearer {openai_api_key}",
}

app = FastAPI()

# Global vector database instance
vector_db = VectorDatabase()

# Country name to ISO 3166-1 alpha-2 code mapping
COUNTRY_CODE_MAPPING = {
    "United States": "us",
    "United Kingdom": "uk",
    "Canada": "ca",
    "Australia": "au",
    "India": "in",
    "Germany": "de",
    "France": "fr",
    "Spain": "es",
    "Italy": "it",
    "Netherlands": "nl",
    "Singapore": "sg",
    "Ireland": "ie",
    "United Arab Emirates": "ae",
    "Japan": "jp",
    "South Korea": "kr",
    "Switzerland": "ch",
    "Sweden": "se",
    "New Zealand": "nz",
    # Add more countries you expect
}

# ---------------------------- FUNCTIONS DEFINED FOR BACKEND PROCESSING ---------------------------------------------

# Return the country code for the given country name
def get_country_code(country_name: str) -> str:
    """Convert full country name to two-letter ISO code."""
    return COUNTRY_CODE_MAPPING.get(country_name.strip(), None)

# Converts the list of dictionaries of job postings to a list of strings for embedding
def build_job_texts(jobs: list[dict]) -> list[str]:
    job_texts = []
    
    for job in jobs:
        text = f"""
        Job Title: {job.get('job_title', '')}
        Job Publisher: {job.get('job_publisher', '')}
        Employment Type: {job.get('job_employment_type', '')}
        Location: {job.get('job_location', '')}
        Job Description: {job.get('job_description', '')}
        """.strip()
        
        job_texts.append(text)
    
    return job_texts

# Concatenates the resume summary and the chat history
def combine_summary_and_chat(resume_summary: dict, chat_history: list[dict]) -> str:
    # Format the resume summary
    formatted_summary = f"""
    Summary:
    {resume_summary.get('Summary', 'No summary provided.')}

    Key Projects:
    {resume_summary.get('Projects', 'No projects listed.')}
    """.strip()

    # Format the chat history
    formatted_chat_history = "\n".join(
        [f"{msg['role'].capitalize()}: {msg['content']}" for msg in chat_history]
    )

    # Combine the formatted summary and chat history
    combined_text = f"""
    Candidate Profile:
    {formatted_summary}

    Conversation History:
    {formatted_chat_history}
    """.strip()

    return combined_text

# Compares the candidate vector with the job vectors and returns the top_k most similar jobs using cosine similarity
def rank_jobs_by_similarity(candidate_vector, job_vectors, jobs, top_k):
    """
    Rank job listings by similarity to the candidate vector.

    Parameters:
    - candidate_vector: list[float] or np.array, the embedded resume+intent vector
    - job_vectors: list[list[float]], embeddings of job listings
    - jobs: list[dict], original job dictionaries aligned with job_vectors
    - top_k: int, number of top matches to return

    Returns:
    - list of tuples: (job_dict, similarity_score)
    """
    if len(jobs) != len(job_vectors):
        raise ValueError("Length of jobs and job_vectors must be the same.")

    # Ensure vectors are NumPy arrays
    job_matrix = np.array(job_vectors)
    candidate_vec = np.array(candidate_vector).reshape(1, -1)

    # Compute cosine similarity scores
    similarities = cosine_similarity(candidate_vec, job_matrix)[0]

    # Sort indices by highest similarity
    sorted_indices = np.argsort(similarities)[::-1][:top_k]

    # Return top_k (job_dict, score) pairs
    return [(jobs[i], similarities[i]) for i in sorted_indices]


# --------------------------------------  FASTAPI Functions ----------------------------------------------------

class ResumeParserRequest(BaseModel):
    file: UploadFile
    country: str

@app.post('/parse_resume/')
async def parse_resume(
    file: UploadFile = File(...),
    country: str = Form(...)
    ):
        # Step 1 : Extract raw text from uploaded file
        
        contents = await file.read()
        file_type = file.filename.split('.')[-1].lower()

        if file_type == 'pdf':
            with fitz.open(stream=contents, filetype="pdf") as doc:
                text = "\n".join([page.get_text() for page in doc])
        elif file_type in ['docx', 'doc']:
            with open(f"/tmp/{file.filename}", 'wb') as f:
                f.write(contents)
            text = docx2txt.process(file.filename)
        else:
            return {"error": "Unsupported file type"}
        
        # print(f"Extracted text from {file.filename} ({file_type}):\n {text}", flush=True)
          
        
        # Step 2 : Run the traditional and LLM parsers
        traditional_data = traditional_resume_parser(text, country)
        # print(f"Traditional Parser Output: {traditional_data}", flush=True)
        
        llm_data = llm_resume_parser(text, country)
        # print(f"LLM Parser Output: {llm_data}", flush=True)
        
        # Step 3 : Reconcile the two using LLM
        parsed_resume = reconcile_parsed_outputs(traditional_data, llm_data)
        # print(f"Final Result: {parsed_resume}", flush=True)
        
        return parsed_resume

class QueryResponseRequest(BaseModel):
    query: str
    resume_summary: dict
    chat_history: list[dict]
    
@app.post('/get_query_response/')
async def get_query_response(request: QueryResponseRequest):
    return get_llm_response(request.query, request.resume_summary, request.chat_history)

class RetrieveJobsRequest(BaseModel):
    country: str
    resume_summary: dict
    chat_history: list[dict]
    
@app.post('/retrieve_jobs/')
async def retrieve_jobs(request: RetrieveJobsRequest):
        jsearch_query = generate_query_for_jobsearch(request.resume_summary, request.chat_history)
        country = get_country_code(request.country)
        print(f"Country Code: {country},\nJsearch Query:{jsearch_query}", flush=True)
        raw_jobs_data = get_jobs(jsearch_query, country)
        
        # Define the keys you want to keep
        selected_keys = [
            "job_publisher", # The company which put up the job
            "job_employment_type", # The type of employment (e.g., full-time, part-time, etc.)
            "job_title", # The title of the job Eg: Software Engineer, Data Scientist, etc.
            "job_apply_link", # Application Link
            "job_description", # The description of the job
            "job_location", # The location of the job
        ]
        
        # Filter the keys in each job dictionary
        jobs = [
                { key: job.get(key) for key in selected_keys }
                for job in raw_jobs_data["data"]
                ]

            
        # Add the job to the list of jobs
        # print(f"Job: {jobs}", flush=True)
        # print(f"Jobs: {raw_jobs_data['data'][0]}", flush=True)
        
        return jobs

# Filtering the job listings based on the resume summary and chat context
class FilterJobsRequest(BaseModel):
    jobs: list[dict]
    resume_summary: dict
    chat_history: list[dict]
    top_k: int
    
@app.post('/filter_jobs/')
async def filter_jobs(request: FilterJobsRequest):
    
    # Getting embeddings of jobs
    job_texts = build_job_texts(request.jobs)
    job_texts_embeddings = get_embeddings(job_texts)
    # print(len(job_texts_embeddings), flush=True)
    # print(len(job_texts_embeddings[0]), flush=True)
    
    
    # Combining the resume summary and chat history into a single string for the vector database(vdb) or candidate embedding
    # Resume summary is a dictionary with keys: Name, Summary, Projects, Country
    # Chat history is a list of dictionaries with keys: role and content
    combined_string_vdb = combine_summary_and_chat(request.resume_summary, request.chat_history)
    
    # We can use two methods for comparing the job postings with resume summary and chat history
    
    # 1. Using the embeddings of the job postings and the combined string to get the most relevant job postings
    candidate_embedding = get_embeddings(combined_string_vdb)
    top_matches = rank_jobs_by_similarity(candidate_embedding, job_texts_embeddings, request.jobs, request.top_k)

    # print(len(candidate_embedding), flush=True)
    # print(len(candidate_embedding[0]), flush=True)
    
    return top_matches
    
    # 2. Using the vector database(chunk the combined string and store in a vector DB) and compare to get the most relevant job postings

# generating a cover letter
class CoverLetterRequest(BaseModel):
    resume_summary: dict
    job_details: dict

@app.post('/generate_cover_letter/')
async def generate_cover_letter_endpoint(request: CoverLetterRequest):
    """Generate a cover letter"""
    try:
        from agents.cv_generation import generate_cover_letter
        
        # Debug prints
        print("\n=== Cover Letter Generation Request ===")
        print(f"Resume Summary: {request.resume_summary}")
        print(f"Job Details: {request.job_details}")
        
        cover_letter = generate_cover_letter(
            resume_summary=request.resume_summary,
            job_details=request.job_details
        )
        
        if cover_letter is None:
            error_msg = "Cover letter generation failed - received None from generator"
            print(f"\nError: {error_msg}")
            return {"error": error_msg}
        
        print("\n=== Generated Cover Letter ===")
        print(cover_letter[:100] + "...")  # Print first 100 chars
        return {"cover_letter": cover_letter}
    
    except Exception as e:
        error_msg = f"Cover letter generation failed: {str(e)}"
        print(f"\nError: {error_msg}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return {"error": error_msg}

    
if __name__ == '__main__':
    uvicorn.run(app, host = '127.0.0.1', port = 8000)
    # Run using : "uvicorn backend.app_backend:app --host 127.0.0.1 --port 8000 --reload"