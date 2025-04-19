from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from backend.models.job_schema import JobPost, JobSearchParameters
from backend.services.job_fetcher import JobFetcher
from backend.core.config import get_settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

async def get_job_fetcher() -> JobFetcher:
    """Dependency to get JobFetcher instance"""
    settings = get_settings()
    return JobFetcher()

@router.get('/search', response_model=List[JobPost])
async def search_jobs(
    query: str, 
    location: Optional[str] = None, 
    experience_level: Optional[str] = None,
    remote: Optional[bool] = None, 
    limit: int = Query(default=10, ge=1, le=100),
    offset: int= Query(default=0, ge=0),
    job_fetcher: JobFetcher = Depends(get_job_fetcher)
) -> List[JobPost]:
    """
    Search for jobs with given parameters
    Args:
        query: Search query (e.g., "python developer")
        location: Job location
        experience_level: Required experience level
        remote: Whether to show remote jobs only
        limit: Number of results per page
        offset: Pagination offset
    Returns:
        List of job postings
    """
    try:
        search_params = JobSearchParameters(
            query=query,
            location=location,
            experience_level=experience_level,
            remote=remote,
            limit=limit,
            offset=offset
        )
    
        jobs = await job_fetcher.search_jobs(search_params)
        return jobs[:limit]
    
    except Exception as e:
        logger.error(f'Error searching jobs: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get('/{job_id}', response_model=JobPost)
async def get_job_details(
    job_id: str,
    job_fetcher: JobFetcher = Depends(get_job_fetcher)
) -> JobPost:
    """
    Get detailed information about a specific job
    Args:
        job_id: Unique job identifier
    Returns:
        Detailed job information
    """

    try: 
        # search with job ID
        jobs = await job_fetcher.search_jobs(
            JobSearchParameters(query=f'job_id: {job_id}')
        )
        if not jobs:
            raise HTTPException(status_code=404, detail='Job not found')
        return jobs[0]
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f'Error fetching job details: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))
        