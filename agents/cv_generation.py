from dotenv import load_dotenv
from openai import OpenAI
import os

LLM_MODEL = "gpt-3.5-turbo"

# Loading the environment variables from .env file
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def format_resume_summary(resume_summary: dict) -> str:
    return f"""
    Name: {resume_summary.get('Name', 'N/A')}
    Current Location: {resume_summary.get('Country', 'N/A')}

    Professional Background:
    {resume_summary.get('Summary', 'No summary provided.')}

    Notable Projects:
    {', '.join(resume_summary.get('Projects', []))}
    """.strip()

def format_job_details(job_details: dict) -> str:
    return f"""
    Role: {job_details.get('job_title', 'N/A')}
    Company: {job_details.get('job_publisher', 'N/A')}
    Location: {job_details.get('job_location', 'N/A')}
    Employment Type: {job_details.get('job_employment_type', 'N/A')}

    Job Description:
    {job_details.get('job_description', 'N/A')}
    """.strip()

def generate_cover_letter(resume_summary: dict, job_details: dict) -> str:
    try:
        formatted_resume = format_resume_summary(resume_summary)
        formatted_job = format_job_details(job_details)

        prompt = f"""
        You are a professional cover letter writer. Create a personalized cover letter that showcases the candidate's strengths and alignment with the job requirements.

        CANDIDATE INFORMATION:
        {formatted_resume}

        TARGET POSITION:
        {formatted_job}

        Guidelines:
        1. Begin with a professional greeting
        2. Express enthusiasm for the specific role and company
        3. Connect candidate's experience with job requirements
        4. Highlight relevant projects and achievements
        5. Express willingness for interview
        6. End with a professional closing
        7. Keep length to 300-400 words
        8. Use formal business letter format
        9. Focus on value proposition
        10. Include specific examples from projects

        Generate a compelling cover letter following these guidelines.
        """

        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert cover letter writer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"Error in cover letter generation: {str(e)}", flush=True)
        return None