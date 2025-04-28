import requests
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("RAPID_API_KEY")

def get_jobs(query: str, country: str) -> None:

    url = "https://jsearch.p.rapidapi.com/search"

    querystring = {
        "query": query,
        "page": "1",
        "num_pages": "1",    # 2 pages -> approx 20 jobs
        "country": country,     # Optional; remove if global
        "date_posted": "all" # Optional filtering
    }

    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "jsearch.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code == 200:
        job_results = response.json()
        # for job in job_results["data"]:
        #     print(f"Title: {job['job_title']}")
        #     print(f"Company: {job['employer_name']}")
        #     print(f"Location: {job['job_city']}, {job['job_country']}")
        #     print(f"Link: {job['job_apply_link']}\n")
    else:
        print(f"Error: {response.status_code} - {response.text}")
        
    return job_results