from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
from agents.resume_parser import traditional_resume_parser, llm_resume_parser, reconcile_parsed_outputs
from agents.chatbot import get_llm_response
from agents.extract_query import generate_query_for_jobsearch
from agents.job_search import get_jobs
import os
import fitz
import docx2txt


# Initializing Global Variables for easy access

LLM_MODEL = "google/flan-t5-base"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


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

def get_country_code(country_name: str) -> str:
    """Convert full country name to two-letter ISO code."""
    return COUNTRY_CODE_MAPPING.get(country_name.strip(), None)

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
        jsearch_query = generate_query_for_jobsearch(request.resume_summary)
        country = get_country_code(request.country)
        print(f"Country Code: {country},\nJsearch Query:{jsearch_query}", flush=True)
        raw_jobs_data = get_jobs(jsearch_query, country)
        
        # Define the keys you want to keep
        selected_keys = [
            "job_publisher",
            "job_employment_type",
            "job_title",
            "job_apply_link",
            "job_description",
            "job_location",
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
    
if __name__ == '__main__':
    uvicorn.run(app, host = '127.0.0.1 --port 8000', port = 8000)
    # Run using : "uvicorn backend.app_backend:app --host 127.0.0.1 --port 8000 --reload"