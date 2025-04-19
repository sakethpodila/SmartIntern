from typing import List, Dict, Optional
import aiohttp
import asyncio
from datetime import datetime
import logging
from backend.models.job_schema import JobPost, JobSearchParameters
from backend.core.config import get_settings
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class JobFetcher: 
    def __init__(self):
        """initialize job fetcher with settings"""
        settings = get_settings()
        # Don't include https:// in the host
        self.base_url = "https://jsearch.p.rapidapi.com"
        self.headers = {
            "x-rapidapi-key": settings.JSEARCH_API_KEY,
            "X-rapidapi-host": "jsearch.p.rapidapi.com"  # Just the host, not full URL
        }

    async def search_jobs(self, params: JobSearchParameters):
        """Search for jobs using Jsearch"""
        try:
            endpoint = f'{self.base_url}/search'
            query_params = {
                'query': f'{params.query} {params.location or ""}'.strip(),
                'page': str(params.offset // 10 + 1),
                'num_pages': '1',
                'remote_jobs_only': str(params.remote).lower() if params.remote else 'false'
            }

            logger.info(f"Making request with headers: {self.headers}")
            logger.info(f"Query params: {query_params}")

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(
                        endpoint,
                        headers=self.headers,
                        params=query_params,
                        ssl=True,
                        timeout=30
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f'API error: {response.status}, Details: {error_text}')
                            raise HTTPException(
                                status_code=response.status,
                                detail=f"API error: {error_text}"
                            )

                        data = await response.json()
                        return [self._parse_job_data(job) for job in data.get('data', [])]

                except aiohttp.ClientConnectorError as e:
                    logger.error(f'Connection error: {str(e)}')
                    raise HTTPException(
                        status_code=503,
                        detail="Unable to connect to job search service"
                    )

        except Exception as e:
            logger.error(f'Error fetching jobs: {str(e)}')
            raise

    def _parse_job_data(self, job_data: Dict) -> JobPost:
        """Convert API response to JobPost model"""
        # Handle location fields that might be None
        city = job_data.get("job_city", "")
        country = job_data.get("job_country", "")
        location = f"{city}, {country}" if city and country else city or country or "Remote"

        return JobPost(
            job_id=job_data.get("job_id"),
            title=job_data.get("job_title"),
            company=job_data.get("employer_name"),
            location=location,  # Use processed location string
            description=job_data.get("job_description", ""),
            requirements=self._extract_requirements(job_data.get("job_description", "")),
            salary_range=job_data.get("job_salary", ""),
            posted_date=self._parse_date(job_data.get("job_posted_at_datetime_utc")),
            job_type=job_data.get("job_employment_type"),
            url=job_data.get("job_apply_link")
        )
    
    def _extract_requirements(self, description: str) -> List[str]:
        """Extract requirements from job description"""
        requirements = []
        lines = description.split('\n')
        in_requirements = False
        
        for line in lines:
            line = line.strip()
            if any(x in line.lower() for x in ["requirements:", "qualifications:", "what you'll need:"]):
                in_requirements = True
                continue
            if in_requirements and line:
                if line.startswith(('•', '-', '●', '*')):
                    requirements.append(line.lstrip('•-●* '))
            if in_requirements and any(x in line.lower() for x in ["benefits:", "what we offer:", "about us:"]):
                break
                
        return requirements

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object""" 
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            return None
