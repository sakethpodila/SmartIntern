# The extract_query function:
# Extracts the most important points in the chat history and resume summary
# and generates a query for the sending through the jsearch api.

from dotenv import load_dotenv
from openai import OpenAI
import os

LLM_MODEL = "gpt-3.5-turbo" 

# Loading the environment variables from the .env file
load_dotenv()
client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))

def generate_query_for_jobsearch(resume_summary: dict, chat_history: list[dict]):
    try:
        # Format the chat history into readable lines
        formatted_chat_history = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in chat_history])
        
        summary =   f"""
        Summary: {resume_summary.get('Summary', 'No summary provided.')}
        """
        
        # Crafting the system and user prompts for the LLM
        
        system_prompt = f"""
        You are a job search assistant. Your task is to generate a concise job search query based on the candidate's resume summary and the given chat history with the user.
        - Focus on extracting the **desired job role**, **location** (if mentioned), **job level** (e.g., entry level, senior), and **job type** (e.g., AI, ML).
        - The query should include the job role and the job level/type, such as "entry-level AI jobs" or "internship in AI" or "senior Data Scientist".
        - If the resume mentions a specific job level (e.g., internship, entry-level, senior), include it.
        - If no job level is mentioned, generate a generic query like "AI jobs" or "developer jobs".
        - The query should be simple and clear, with the format "[Job Level] [Job Type] jobs".
        - Avoid including technical skills or personal details.
        """

        
        user_prompt = f"""
         Resume Summary:
        {summary}
        
        Chat History:
        {formatted_chat_history}

        ---

        Task:
        Based on the above resume summary and the most recent chat history conversation also keeping in mind the entire chat history, generate a **short, clear job search query** that includes the **job role**, **job level** (e.g., entry-level, internship), and **job type** (e.g., AI, ML).
        The query should be in the format:
        - "[Job Level] [Job Type] jobs"
        Example queries:
        - "AI jobs"
        - "internship in AI"
        - "senior developer jobs"
        - "junior data scientist jobs"
        Ensure that the query reflects the job level/type mentioned in the resume.
        """.strip()
        
        # Call OpenAI API (using GPT-3.5 or GPT-4)
        response = client.chat.completions.create(
            model=LLM_MODEL,  # or "gpt-4" for a more powerful model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
        )
                
        jsearch_query = response.choices[0].message.content.strip()

        return jsearch_query
    
    except Exception as e:
        print(f"Error in extracting query: {e}")
        return None