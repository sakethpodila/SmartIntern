from dotenv import load_dotenv
from openai import OpenAI
import os

LLM_MODEL = "gpt-3.5-turbo" 

# Loading the environment variables from the .env file
load_dotenv()
client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))

def get_llm_response(query, resume_summary):
    try:
        prompt = (
            '''Answer the following question/query based on the resume summary provided, 
            in second person referencing the user as the subject in question, and given context and
            return a string as response:\n\n'''
            f"Resume Summary: {resume_summary}\n\n"
            f"Question/Query: {query}\n\n"
            f"Answer:"
        )
        
        # Call OpenAI API (using GPT-3.5 or GPT-4)
        response = client.chat.completions.create(
            model=LLM_MODEL,  # or "gpt-4" for a more powerful model
            messages=[
                {"role": "system", "content": "You are custom interactive chatbot for an intelligent job search experience"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )
        
        # print(response)
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"Error in creating prompt: {e}")
        return "Error in creating prompt."