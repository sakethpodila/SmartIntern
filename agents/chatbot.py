from dotenv import load_dotenv
from openai import OpenAI
import os

LLM_MODEL = "gpt-3.5-turbo" 

# Loading the environment variables from the .env file
load_dotenv()
client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))

def get_llm_response(user_query, resume_summary, chat_history):
    try:
        # Format the chat history into readable lines
        formatted_history = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in chat_history])
        
        # Format the Resume Summary into readable lines
        formatted_resume_summary = f"""
        Name: {resume_summary.get('Name', 'N/A')}
        Country: {resume_summary.get('Country', 'N/A')}

        Summary:
        {resume_summary.get('Summary', 'No summary provided.')}

        Key Projects:
        {resume_summary.get('Projects', 'No projects listed.')}
        """.strip()

        # Crafting the prompt for the LLM
        prompt = f"""
        You are an intelligent and helpful job search assistant. You are guiding a user through understanding and clarifying their job preferences based on their background and ongoing conversation.

        Politely refuse to answer questions on topics unrelated to job search or career development.

        ### Candidate Profile:
        {formatted_resume_summary}

        ### Conversation History:
        {formatted_history}

        ---

        Now, based on the user's latest message and their background, respond helpfully. Your goals are to:
        - Answer the user's question
        OR
        - Ask a relevant follow-up to refine their preferences (e.g., preferred tech stack, role types, industry interests, work location).

        Stay focused on helping the user navigate their job search. If their profile is complete enough, you may recommend starting the job search process.

        ---

        ### User's Latest Message:
        {user_query}

        Respond as a friendly, knowledgeable assistant.
        """.strip()
        
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