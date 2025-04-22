from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
from agents.resume_parser import traditional_resume_parser, llm_resume_parser, reconcile_parsed_outputs
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

llm_api_url = f"https://api-inference.huggingface.co/models/{LLM_MODEL}"

openai_api_url = "https://api.openai.com/v1/chat/completions"

embedding_api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{EMBEDDING_MODEL}"

hf_headers = {
            "Authorization": f"Bearer {hf_api_key}",
            }

openai_headers = {
    "Authorization": f"Bearer {openai_api_key}",
}

app = FastAPI()

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
        
        print(f"Extracted text from {file.filename} ({file_type}):\n {text}", flush=True)
          
        
        # Step 2 : Run the traditional and LLM parsers
        traditional_data = traditional_resume_parser(text, country)
        # print(f"Traditional Parser Output: {traditional_data}", flush=True)
        
        llm_data = llm_resume_parser(text, country)
        # print(f"LLM Parser Output: {llm_data}", flush=True)
        
        # Step 3 : Reconcile the two using LLM
        final_result = reconcile_parsed_outputs(traditional_data, llm_data)
        print(f"Final Result: {final_result}", flush=True)
        
if __name__ == '__main__':
    uvicorn.run(app, host = '127.0.0.1 --port 8000', port = 8000)
    # Run using : "uvicorn app_backend:app --host 127.0.0.1 --port 8000 --reload"