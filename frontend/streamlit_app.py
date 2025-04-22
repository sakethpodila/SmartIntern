import streamlit as st
import json
import requests

BACKEND_URL = "http://127.0.0.1:8000"  # Replace with your backend URL

st.title("SmartIntern 🧑‍🎓")
st.subheader("Your Personal AI Assistant for a simpler Job Searching experience")

# Input Fields
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
        requests.post(f"{BACKEND_URL}/parse_resume/", files=files, data=data)