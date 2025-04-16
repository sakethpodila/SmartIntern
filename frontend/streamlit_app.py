import streamlit as st
import json
import requests

BACKEND_URL = "http://localhost:8000"  # Replace with your backend URL

st.title("SmartIntern 🧑‍🎓")
st.subheader("Your Personal AI Assistant for simpler Job Searching experience")

# Input Fields
uploaded_file = st.file_uploader("Upload your resume", type=["pdf", "docx"])
country = st.text_input("Enter the country where you are looking for a job")

if st.button("Parse Resume") and uploaded_file is not None:
    with st.spinner("Parsing resume..."):
        
        files = {
            "file": (uploaded_file.name,
                     uploaded_file,
                     uploaded_file.type)
        }
        data = {"country": country}