from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Optional
from backend.models.user_schema import ResumeData
from backend.services.resume_parser import ResumeParser
import logging

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post('/upload', response_model=ResumeData)
async def upload_resume(
    file: UploadFile = File(...),
    extract_contact: Optional[bool] = True,
    extract_skills: Optional[bool] = True
) -> Dict:
    
    #validate data types
    allowed_types = {
        'application/pdf': '.pdf', 
        'application/vnd.o'
        'penxmlformats-officedocument.wordprocessingml.document': '.docx'
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Supported types: {','.join(allowed_types.values())}"
        )
    
    try:
        # Initialize parser and processfile from the resume_parser.py service
        parser = ResumeParser()
        parsed_data = await parser.parse(
            file=file,
            extract_contact=extract_contact,
            extract_skills=extract_skills
        )

        logger.info(f'Successfully parsed resume: {file.filename}')
        return parsed_data
    
    except Exception as e:
        logger.error(f'Error parsing resume {file.filename}: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))
    

