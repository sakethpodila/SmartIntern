import streamlit as st
import json
import requests

BACKEND_URL = "http://127.0.0.1:8000"  # Replace with your backend URL

st.title("SmartIntern 🧑‍🎓")
st.subheader("Your Personal AI Assistant for a simpler Job Searching experience")

# Initializing the chatbot memory variables for frontend
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
    
if 'job_queries' not in st.session_state:
    st.session_state.job_queries = []
    
if 'ready_to_search' not in st.session_state:
    st.session_state.ready_to_search = False
    
# File Upload Code    
uploaded_file = st.file_uploader("Upload your resume", type=["pdf", "docx"])
st.session_state.country = st.text_input("Enter the country where you are looking for a job")

if st.button("Parse Resume") and uploaded_file is not None:
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
            st.session_state.resume_summary = response.json()
            print(st.session_state.resume_summary)
            if st.session_state.resume_summary:
                st.success("Your resume has been successfully parsed!")
                
        except Exception as e:
            st.error("An error occurred while parsing your resume.")
            st.write(str(e))

# Interactive Chatbot Code

@st.cache_data
def get_chatbot_response(user_query, resume_summary):
    # API call to get the chatbot response
    try:
        response = requests.post(f"{BACKEND_URL}/get_query_response/", json={"query": user_query, "resume_summary": resume_summary})
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Error getting response from the chatbot")
            return None
    except Exception as e:
        st.error("An error occurred while getting the chatbot response.")
        st.write(str(e))
        
# Display previous chat
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
user_query = st.chat_input("Ask me anything about job search with respect to your resume!")

if user_query:
    # Add user query to chat history
    st.chat_message("user").markdown(user_query)
    st.session_state.job_queries.append(user_query)
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_query
        })    
    
    # Call backend with query and resume summary
    assistant_reply = get_chatbot_response(user_query, st.session_state.resume_summary)

    st.chat_message("assistant").markdown(assistant_reply)
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": assistant_reply
        })