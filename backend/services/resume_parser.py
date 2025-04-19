from typing import Dict, BinaryIO, Optional, List
import PyPDF2
from docx import Document
from io import BytesIO
import spacy
import re
from pathlib import Path
import logging
from backend.models.user_schema import ResumeData, ContactInfo
import fitz

logger = logging.getLogger(__name__)

class ResumeParser:
    def __init__(self):
        """intializing the resume parser with required models"""
        
        #loading spaCy model for NER
        self.nlp = spacy.load('en_core_web_sm')

        # email, phone patterns
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        self.phone_pattern = r'\b(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b'

        self.skills_keywords = set(['python', 'javascript', 'java', 'c++', 'sql', 'machine learning', 'data analysis', 'aws', ])

    async def parse(
            self,
            file: BinaryIO,
            extract_contact: bool = True, 
            extract_skills: bool = True
    ) -> ResumeData:
        try:
            # extract text from file
            text = await self._extract_text(file)

            # initialize parsed data
            parsed_data = {
                'raw_text': text, 
                'contact_info': self._extract_contact_info(text) if extract_contact else {},
                'education': self._extract_education(text),
                'experience': self._extract_experience(text), 
                'skills': self._extract_skills(text) if extract_skills else [],
                'summary': self._extract_summary(text) 
                }
            
            return ResumeData(**parsed_data)
        
        except Exception as e:
            logger.error(f'Error in resume parsing: {str(e)}')
            raise
    
    async def _extract_text(self, file: BinaryIO) -> str:
        # extract text from pdf or doc file"

        content = await file.read()
        file_ext = Path(file.filename).suffix.lower()

        if file_ext == '.pdf':
            return self._parse_pdf(content)
        elif file_ext == '.docx':
            return self._parse_docx(content)
        else:
            raise ValueError(f'Unsupported file type: {file_ext}')
        
    def _parse_pdf(self, content: bytes) -> str:
        """
        Extract text from PDF using both PyMuPDF and PyPDF2 for better accuracy
        """
        try:
            # First try with PyMuPDF (more accurate)
            with fitz.open(stream=content, filetype="pdf") as pdf:
                text = ""
                for page in pdf:
                    text += page.get_text()
                
                if text.strip():
                    return text

            # Fallback to PyPDF2 if PyMuPDF didn't get text
            with BytesIO(content) as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text

        except Exception as e:
            logger.error(f"Error parsing PDF: {str(e)}")
            raise ValueError(f"Could not parse PDF: {str(e)}")
    
    def _parse_docx(self, content: bytes) -> str:
        with BytesIO(content) as docx_file:
            doc = Document(docx_file)
            return ' '.join(paragraph.text for paragraph in doc.paragraphs)
        
    def _extract_contact_info(self, text: str) -> Dict:

        # use spaCy for named entity recognition
        doc = self.nlp(text)

        contact_info = {
            "name": "",
            "email": "",
            "phone": "",
            "location": "",
            "linkedin": ""
        }

        # extract email
        emails = re.findall(self.email_pattern, text)
        if emails:
            contact_info['email'] = emails[0]
        
        #extract phone
        phones = re.findall(self.phone_pattern, text)
        if phones:
            contact_info['phone'] = phones[0]
        
        # extract name and location using NER
        for ent in doc.ents:
            if ent.label == "PERSON" and not contact_info['name']:
                contact_info['name'] = ent.text
            elif ent.label == "GPE" and not contact_info['location']:
                contact_info['location'] = ent.text

        return contact_info
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from text"""
        found_skills = []
        text_lower = text.lower()
        
        for skill in self.skills_keywords:
            if skill.lower() in text_lower:
                found_skills.append({
                "name": skill,
                "category": self._categorize_skill(skill),
                "proficiency": None,
                "years": None
            })

        return found_skills

    def _categorize_skill(self, skill: str) -> str:
        """Categorize skills into types"""
        categories = {
            "programming": ["python", "javascript", "java", "c++", "sql"],
            "cloud": ["aws", "azure", "gcp"],
            "ml": ["machine learning", "tensorflow", "pytorch"],
            "frameworks": ["django", "fastapi", "react"]
        }
        
        skill_lower = skill.lower()
        for category, skills in categories.items():
            if skill_lower in skills:
                return category
        return "other"
    
    def _extract_summary(self, text: str) -> Optional[str]:
        # Look for common summary section headers
        summary_headers = ["summary", "professional summary", "objective"]
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            if any(header in line.lower() for header in summary_headers):
                # Return next non-empty line
                for next_line in lines[i+1:]:
                    if next_line.strip():
                        return next_line.strip()
        return None
    
    # Add after _extract_summary method:
    def _extract_education(self, text: str) -> List[Dict]:
        """
        Extract education information from resume text
        Returns list of education entries
        """
        education_list = []
        # Common education section headers
        edu_headers = ["education", "academic background", "academic history"]
        # Common degree patterns
        degree_patterns = [
            r"(B\.?S\.?|Bachelor of Science)",
            r"(B\.?A\.?|Bachelor of Arts)",
            r"(M\.?S\.?|Master of Science)",
            r"(M\.?B\.?A\.?|Master of Business Administration)",
            r"(Ph\.?D\.?|Doctor of Philosophy)"
        ]
        
        # Find education section
        lines = text.split('\n')
        edu_section = ""
        in_edu_section = False
        
        for line in lines:
            line = line.strip()
            if any(header in line.lower() for header in edu_headers):
                in_edu_section = True
                continue
            if in_edu_section:
                if line and len(line) > 3:  # Skip empty or very short lines
                    edu_section += line + "\n"
                # Stop if we hit another section
                if line.lower() in ["experience", "skills", "projects"]:
                    break
        
        # Process education section
        if edu_section:
            # Use spaCy for entity recognition
            doc = self.nlp(edu_section)
            
            current_edu = {}
            for ent in doc.ents:
                if ent.label_ == "ORG":  # Likely a university/institution
                    if current_edu:
                        education_list.append(current_edu.copy())
                    current_edu = {"institution": ent.text}
                elif ent.label_ == "DATE":
                    if "start_date" not in current_edu:
                        current_edu["start_date"] = ent.text
                    else:
                        current_edu["end_date"] = ent.text
            
            # Add degree information
            for pattern in degree_patterns:
                matches = re.finditer(pattern, edu_section, re.IGNORECASE)
                for match in matches:
                    if current_edu:
                        current_edu["degree"] = match.group()
            
            # Add last education entry
            if current_edu:
                education_list.append(current_edu)
        
        return education_list

    def _extract_experience(self, text: str) -> List[Dict]:
        """
        Extract work experience information from resume text
        Returns list of experience entries
        """
        experience_list = []
        # Common experience section headers
        exp_headers = ["experience", "work experience", "employment history"]
        
        # Find experience section
        lines = text.split('\n')
        exp_section = ""
        in_exp_section = False
        
        for line in lines:
            line = line.strip()
            if any(header in line.lower() for header in exp_headers):
                in_exp_section = True
                continue
            if in_exp_section:
                if line and len(line) > 3:
                    exp_section += line + "\n"
                # Stop if we hit another section
                if line.lower() in ["education", "skills", "projects"]:
                    break
        
        # Process experience section
        if exp_section:
            # Use spaCy for entity recognition
            doc = self.nlp(exp_section)
            
            current_exp = {}
            bullet_points = []
            
            for sent in doc.sents:
                # Look for company names and job titles
                for ent in sent.ents:
                    if ent.label_ == "ORG":
                        if current_exp:
                            if bullet_points:
                                current_exp["description"] = bullet_points
                            experience_list.append(current_exp.copy())
                            bullet_points = []
                        current_exp = {"company": ent.text}
                    elif ent.label_ == "DATE":
                        if "start_date" not in current_exp:
                            current_exp["start_date"] = ent.text
                        else:
                            current_exp["end_date"] = ent.text
                
                # Collect bullet points
                sent_text = sent.text.strip()
                if sent_text.startswith(('•', '-', '●')):
                    bullet_points.append(sent_text.lstrip('•-● '))
            
            # Add last experience entry
            if current_exp:
                if bullet_points:
                    current_exp["description"] = bullet_points
                experience_list.append(current_exp)
        
        return experience_list


    