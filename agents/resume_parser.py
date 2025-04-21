import re
import spacy
import requests
import json
from dotenv import load_dotenv
import os

LLM_MODEL = "mistralai/Mistral-Nemo-Instruct-2407" 

llm_api_url = f"https://api-inference.huggingface.co/models/{LLM_MODEL}"

load_dotenv()
hf_api_key = os.getenv('HF_API_KEY')

headers = {
    "Authorization": f"Bearer {hf_api_key}",
    "Content-Type": "application/json"
}



# Load the English NLP model from spaCy
nlp = spacy.load("en_core_web_sm")

def extract_section(text: str, section_keywords: list, next_section_keywords: list) -> list:
    """
    Extracts content between section_keywords and next_section_keywords, regardless of position.
    """
    pattern = rf"(?i)({'|'.join(section_keywords)})\s*[:\-\n]*\s*(.*?)(?=({'|'.join(next_section_keywords)})\s*[:\-\n]*|\Z)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        section_text = match.group(2).strip()
        lines = [line.strip("•●- \t") for line in section_text.split("\n") if line.strip()]
        return lines
    return []

def traditional_resume_parser(text: str, country: str) -> dict:
    doc = nlp(text)

    # Extract name from top line or first PERSON entity
    lines = text.strip().split("\n")
    name = lines[0].strip() if lines and len(lines[0].strip().split()) <= 4 else None
    if not name:
        for ent in list(doc.ents)[:5]:
            if ent.label_ == "PERSON":
                name = ent.text
                break

    # Extract email and phone
    email = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    phone = re.findall(r"\+?\d[\d\s\-]{7,}", text)

    # Extract sections flexibly
    education = extract_section(text, ["education", "academic background"], ["experience", "skills", "projects", "certifications"])
    experience = extract_section(text, ["experience", "work experience"], ["skills", "projects", "education", "certifications"])
    skills = extract_section(text, ["skills", "technical skills"], ["experience", "projects", "education", "certifications"])
    projects = extract_section(text, ["projects"], ["experience", "education", "certifications"])
    internships = extract_section(text, ["internships"], ["experience", "education", "projects"])
    certifications = extract_section(text, ["certifications"], ["experience", "education", "projects"])
    achievements = extract_section(text, ["achievements", "accomplishments"], ["experience", "education", "projects"])

    # Extract summary (usually the paragraph before first section)
    summary_match = re.search(r"(?s)(.*?)(?=\n(?:education|experience|skills|projects|internships|certifications|achievements)\b)", text, re.IGNORECASE)
    summary = [line.strip() for line in summary_match.group(1).strip().split("\n") if line.strip()] if summary_match else []

    return {
        "name": name,
        "email": email.group() if email else None,
        "phone": phone[0] if phone else None,
        "country": country,
        "summary": summary,
        "education": education,
        "experience": experience,
        "skills": skills,
        "projects": projects,
        "internships": internships,
        "certifications": certifications,
        "achievements": achievements
    }

def llm_resume_parser(text: str, country: str) -> dict:
    prompt = (
        "You are an intelligent resume parser assistant. Your task is to extract structured information "
        "from raw resume text and return a clean, valid JSON with the following keys:\n"
        "- name\n"
        "- email\n"
        "- phone\n"
        "- country (use the one provided by the user)\n"
        "- summary\n"
        "- education (as a list of entries)\n"
        "- skills (as a list)\n"
        "- internships (as a list)\n"
        "- work_experience (as a list)\n"
        "- projects (as a list)\n"
        "- certifications (as a list)\n"
        "If a field is not available, return null or an empty list. "
        f"User provided country: {country}\n\n"
        f"Resume Text:\n{text}"
    )

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 1024,
            "temperature": 0.2,
            "return_full_text": False
        }
    }

    response = requests.post(llm_api_url, headers=headers, json=payload)
    print(response.json(), flush=True)

    if response.status_code == 200:
        try:
            result = response.json()
            # print(f"Result: {result}", flush=True)
            content = result[0]["generated_text"]  # Extract generated text from Hugging Face API

            # parsed_json = json.loads(content) if isinstance(content, str) else content

            # Add country manually if missing
            if "country" not in content:
                content["country"] = country

            return content

        except Exception as e:
            return {"error": f"Failed to parse model output as JSON: {str(e)}"}

    else:
        return {
            "error": f"Hugging Face API request failed with status code {response.status_code}: {response.text}"
        }


def reconcile_parsed_outputs(traditional_data: dict, llm_data: dict) -> dict:
    # 🧠 Build Prompt
    prompt = (
        "You are an intelligent resume reconciliation assistant. Your task is to merge the resume information "
        "from a traditional parser and an LLM-based parser.\n"
        "Return only a valid JSON object with the following keys:\n"
        "- Name\n"
        "- Summary\n"
        "- Country\n\n"
        "The Summary should be a coherent paragraph combining the candidate's background, skills, and experience "
        "in a way suitable for semantic search or vector-based retrieval. "
        "Use the best available data from both sources.\n\n"
        f"Traditional Parsed Resume:\n{json.dumps(traditional_data, indent=2)}\n\n"
        f"LLM Parsed Resume:\n{json.dumps(llm_data, indent=2)}\n\n"
        "Reconciled Final Output:"
    )

    payload = {
        "inputs": prompt,
        "parameters": {
            "temperature": 0.3,
            "max_new_tokens": 512,
            "return_full_text": False
        }
    }

    response = requests.post(llm_api_url, headers=headers, json=payload)

    if response.status_code == 200:
        try:
            result = response.json()
            generated_text = result[0]["generated_text"]

            # # Parse and return clean JSON
            # parsed_json = json.loads(generated_text)
            return generated_text

        except Exception as e:
            return {"error": f"Failed to parse Hugging Face LLM output: {str(e)}"}

    else:
        return {"error": f"Hugging Face API request failed with status {response.status_code}: {response.text}"}
