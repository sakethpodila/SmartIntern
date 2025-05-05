import streamlit as st
import json
import requests

BACKEND_URL = "http://127.0.0.1:8000"  # Replace with your backend URL

st.set_page_config(
    page_title = "SmartIntern",
    page_icon = "🧑‍🎓",
    layout = "wide"
)

st.title("SmartIntern 🧑‍🎓")
st.subheader("Your Personal AI Assistant for a simpler Job Searching experience")

# Initializing the chatbot memory variables for frontend
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
    
# if 'job_queries' not in st.session_state:
#     st.session_state.job_queries = []
    
if 'ready_to_search' not in st.session_state:
    st.session_state.ready_to_search = False

# Ensure filtered_jobs and generated_cover_letters are initialized in session state
if "filtered_jobs" not in st.session_state:
    st.session_state.filtered_jobs = []

if "generated_cover_letters" not in st.session_state:
    st.session_state.generated_cover_letters = {}
    
# File Upload Code    
uploaded_file = st.file_uploader("Upload your resume", type=["pdf", "docx"])

available_countries = [
    "United States", "United Kingdom", "India", "Canada", "Australia",
    "Germany", "France", "Spain", "Italy", "Netherlands", "Singapore",
    "Ireland", "United Arab Emirates", "Japan", "South Korea", "Switzerland",
    "Sweden", "New Zealand"
]

selected_country = st.selectbox(
    "Select your job search country:",
    options=available_countries,
    index=2
)

num_of_matches = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] # number of job matches to display

st.session_state.top_k = st.selectbox(
    "Select the number of top job matches to display:",
    options=num_of_matches ,
    index=4
)

st.session_state.country = selected_country

# ------------------------------------------------------- Functions for making API calls ------------------------------------------

if st.button("Parse Resume") and uploaded_file is not None and st.session_state.country:
    with st.spinner("Parsing resume..."):
        
        files = {
            "file": (uploaded_file.name,
                     uploaded_file.getvalue(),
                     uploaded_file.type)
        }
        data = {"country": st.session_state.country}
        
        # API call to parse the resume
        try:
            response =  requests.post(f"{BACKEND_URL}/parse_resume/", files=files, data=data)
            # print(response.json())
            st.session_state.resume_summary = response.json()
            # print(st.session_state.resume_summary)
            
            # st.session_state.resume_summary is a dictionary with keys: Name, Summary, Projects, Country
            if st.session_state.resume_summary:
                st.success("Your resume has been successfully parsed!")
                
        except Exception as e:
            st.error("An error occurred while parsing your resume.")
            st.write(str(e))
            
# Retrieving the jobs based on the resume and chat history
@st.cache_data
def get_job_listings(country, resume_summary, chat_history):
    # API call to get the jobs based on the resume summary
    try:
        response = requests.post(f"{BACKEND_URL}/retrieve_jobs/", json={"country": country, "resume_summary": resume_summary, "chat_history": chat_history})
        if response.status_code == 200:
            st.session_state.ready_to_search = True
            return response.json()
        else:
            st.error("Error getting jobs")
            return None
        
    except Exception as e:
        st.error("An error occurred while getting jobs.")
        st.write(str(e))

# getting the cover letter
def generate_cover_letter(resume_data: dict, job_data: dict) -> dict:
    """Call backend API to generate cover letter"""
    try:
        st.write("Sending request to generate cover letter...")
        
        response = requests.post(
            f"{BACKEND_URL}/generate_cover_letter/",
            json={
                "resume_summary": resume_data,
                "job_details": job_data
            }
        )
        
        st.write(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            # print(result, flush=True)
            if "error" in result:
                st.error(f"Backend Error: {result['error']}")
            return result
        else:
            st.error(f"HTTP Error {response.status_code}: {response.text}")
            return {"error": response.text}
    
    except Exception as e:
        st.error(f"Request Error: {str(e)}")
        return {"error": str(e)}
        
# Filtering the job listings based on the resume summary
@st.cache_data
def filter_job_listings(jobs, resume_summary, chat_history, top_k):
    # Filter the job listings based on the resume summary
    try:
        filtered_jobs = requests.post(f"{BACKEND_URL}/filter_jobs/", json={'jobs': jobs, 'resume_summary': resume_summary, 'chat_history': chat_history, 'top_k': top_k})
        if filtered_jobs.status_code == 200:
            return filtered_jobs.json()
        else:
            st.error("Error filtering jobs")
            return None
    except Exception as e:
        st.error("An error occurred while filtering jobs.")
        st.write(str(e))
    
# Getting Response from Chatbot
@st.cache_data
def get_chatbot_response(user_query, resume_summary, chat_history):
    # API call to get the chatbot response
    try:
        response = requests.post(f"{BACKEND_URL}/get_query_response/", json={"query": user_query, "resume_summary": resume_summary, "chat_history": chat_history})
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Error getting response from the chatbot")
            return None
    except Exception as e:
        st.error("An error occurred while getting the chatbot response.")
        st.write(str(e))
        
# ------------------------------------------------------- Interface for application ---------------------------------------------
# INTERACTIVE CHATBOT
        
# Display previous chat messages
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
    
user_query = st.chat_input("Ask me anything about job search with respect to your resume!")

if user_query:
    # Add user query to chat history
    st.chat_message("user").markdown(user_query)    
    # st.session_state.job_queries.append(user_query)
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_query
        })    
    
    # Call backend with query and resume summary
    assistant_reply = get_chatbot_response(user_query, st.session_state.resume_summary, st.session_state.chat_history)

    st.chat_message("assistant").markdown(assistant_reply)    
    # st.session_state.job_queries.append(assistant_reply)
    st.session_state.chat_history.append({
    "role": "assistant",
    "content": assistant_reply
    })
    
# JOB SEARCH
if st.button("Start Job Search"):
    st.session_state.jobs = get_job_listings(country=st.session_state.country, resume_summary=st.session_state.resume_summary, chat_history=st.session_state.chat_history)
    # print((st.session_state.jobs[0]))
    st.success("Your job search is completed!")

    # else:
    # st.error("Please parse your resume first.")
    
    st.session_state.filtered_jobs = filter_job_listings(
        st.session_state.jobs, 
        st.session_state.resume_summary, 
        st.session_state.chat_history, 
        st.session_state.top_k
        )
    
if "filtered_jobs" in st.session_state and st.session_state.filtered_jobs:
    st.subheader("🔍 Top Matching Jobs for You")

    for i, (job, score) in enumerate(st.session_state.filtered_jobs, start=1):
        with st.expander(f"{i}. {job['job_title']} at {job['job_publisher']} — Score: {score:.2f}"):
            st.markdown(f"**🏢 Employer:** {job['job_publisher']}")
            st.markdown(f"**📍 Location:** {job['job_location']}")
            st.markdown(f"**🧑‍💼 Employment Type:** {job['job_employment_type']}")
            st.markdown(f"**📄 Description:**")
            st.write(job['job_description'])

            # Store cover letter in session state when generated
            if st.button("📝 Generate Cover Letter", key=f"cv_btn_{i}"):
                with st.spinner("Creating your cover letter..."):
                    cv_response = generate_cover_letter(
                        resume_data=st.session_state.resume_summary,
                        job_data=job
                    )
                    # Store the response in session state
                    st.session_state.generated_cover_letters[i] = cv_response

            # Display cover letter if it exists in session state
            if i in st.session_state.generated_cover_letters:
                cv_response = st.session_state.generated_cover_letters[i]
                if "error" in cv_response:
                    st.error(cv_response["error"])
                elif "cover_letter" in cv_response:
                    st.markdown("### Your Cover Letter")
                    st.text_area(
                        label="Cover Letter Content",
                        value=cv_response["cover_letter"],
                        height=400,
                        key=f"cv_text_{i}",
                        disabled=True
                    )
                    
                    st.download_button(
                        label="📥 Download Cover Letter",
                        data=cv_response["cover_letter"],
                        file_name=f"cover_letter_{job['job_title'].replace(' ', '_')}.txt",
                        mime="text/plain",
                        key=f"download_cv_{i}"
                    )

            st.markdown("---")
            if job.get('job_apply_link'):
                st.markdown(f"[🚀 Apply Now]({job['job_apply_link']})", unsafe_allow_html=True)
# else:
#     st.warning("No job matches found. Please adjust your preferences.")

# if st.session_state.jobs:

