from dotenv import load_dotenv
import os
import openai

LLM_MODEL = "gpt-3.5-turbo" 

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

EMBEDDING_MODEL = "text-embedding-3-small"

# Length of each embedding is 1536 for text-embedding-3-small
def get_embeddings(arr:list) -> list[list[float]]:
    
    response = openai.embeddings.create(
        input=arr,
        model=EMBEDDING_MODEL    
    )
    
    embeddings = [record.embedding for record in response.data]
    
    return embeddings

# res = get_embeddings(["Hello world", "How are you?"])

# print(len(res[0]))