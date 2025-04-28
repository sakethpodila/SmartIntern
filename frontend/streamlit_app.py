import streamlit as st
import json
import requests

BACKEND_URL = "http://127.0.0.1:8000"  # Replace with your backend URL

st.title("SmartIntern 🧑‍🎓")
st.subheader("Your Personal AI Assistant for a simpler Job Searching experience")

# Initializing the chatbot memory variables for frontend
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
    
# if 'job_queries' not in st.session_state:
#     st.session_state.job_queries = []
    
if 'ready_to_search' not in st.session_state:
    st.session_state.ready_to_search = False
    
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

st.session_state.country = selected_country

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
            
# Gettings the jobs based on the resume
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

# Getting Response from Chatbot Code

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
    print((st.session_state.jobs[0]))
    st.success("Your job search is completed!")

    # else:
    # st.error("Please parse your resume first.")
    
# if st.session_state.jobs:

