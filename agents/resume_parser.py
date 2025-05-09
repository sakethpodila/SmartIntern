import re
import spacy
import requests
import json
from dotenv import load_dotenv
import os
from openai import OpenAI

LLM_MODEL = "gpt-3.5-turbo" 

# llm_api_url = f"https://api-inference.huggingface.co/models/{LLM_MODEL}"

load_dotenv()
client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))
# headers = {
#     "Authorization": f"Bearer {hf_api_key}",
#     "Content-Type": "application/json"
# }



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
    try:
        system_prompt = (
            "You are an intelligent resume parser assistant. Your task is to extract structured information "
            "from raw resume text and present it in clean, readable format. Just return the result in the form of a dict with clear labels. "
            "The output format should be like:\n"
            "Name: ...\n"
            "Email: ...\n"
            "Phone: ...\n"
            "job_country: ...\n"
            "Summary: ...\n"
            "Education:\n  - Entry 1\n  - Entry 2\n"
            "Skills:\n  - Skill 1\n  - Skill 2\n"
            "Internships:\n  - Internship 1\n"
            "Work Experience:\n  - Job 1\n"
            "Projects:\n  - Project 1\n"
            "Certifications:\n  - Cert 1\n"
            "Achievements:\n  - Achievement 1\n"
            "Return as much info as you can. If a field is missing, just leave it blank or mention 'None'.\n\n"
            f"User-provided country where they want to apply for a job: {country}\n\n"
            f"Resume Text:\n{text}"
        )

        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": system_prompt}
            ],
            temperature=0.2
        )

        content = response.choices[0].message.content
        # print("🔍 Raw LLM Output:\n", content, flush=True)

        parsed_json = json.loads(content) if isinstance(content, str) else content

        if "job_country" not in parsed_json:
            parsed_json["job_country"] = country

        return parsed_json

    except Exception as e:
        return {"error": f"Failed to call OpenAI or parse response: {str(e)}"}
    

def reconcile_parsed_outputs(traditional_data: dict, llm_data: dict) -> dict:
    try:
        prompt = (
            "You are an intelligent resume reconciliation assistant. Your task is to merge the resume information "
            "from a traditional parser and an LLM-based parser.\n"
            "Return only a dictionary with the following keys:\n"
            "- Name\n"
            "- Summary\n"
            "- Projects\n"
            "- Country\n\n"
            "The Summary key should contain comprehensive, detailed professional description that combines the candidate’s background, skills, projects, and experience along with achievements(optional)."
            "Use rich, descriptive language suitable for semantic search or retrieval. Include relevant keywords from both parsed resumes."
            "Also include coursework, courses that the candidate has completed or taken, and any other relevant information that can be used to enhance the summary."
            "in a way suitable for semantic search or vector-based retrieval. "
            "The Summary should be atleast 300 words in length.\n\n"
            "Summary should also contain the Country specified  by the user where they would like to apply for a job.\n\n"
            "Use the best available and unique data respectively from both sources.\n\n"
            f"Traditional Parsed Resume:\n{json.dumps(traditional_data, indent=2)}\n\n"
            f"LLM Parsed Resume:\n{json.dumps(llm_data, indent=2)}\n\n"
            "Reconciled Final Output:"
        )

    
        # Call OpenAI API (using GPT-3.5 or GPT-4)
        response = client.chat.completions.create(
            model=LLM_MODEL,  # or "gpt-4" for a more powerful model
            messages=[
                {"role": "system", "content": "You are a resume reconciliation assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        

        # Extract the response content
        generated_text = response.choices[0].message.content
        # print("🔍 Reconciled Output:\n", generated_text, flush=True)
        
        # Parse the generated text into a dictionary
        parsed_output = json.loads(generated_text) if isinstance(generated_text, str) else generated_text

        # Return the generated text (which should be the reconciled JSON)
        return parsed_output

    except Exception as e:
        return {"error": f"Failed to call OpenAI API or parse response: {str(e)}"}
