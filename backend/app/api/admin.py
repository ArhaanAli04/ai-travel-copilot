"""
Admin API endpoints for data ingestion and management
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
import subprocess
import sys
from pathlib import Path
import logging


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


class IngestCityRequest(BaseModel):
    city: str
    categories: Optional[List[str]] = None


class IngestCityResponse(BaseModel):
    message: str
    city: str
    status: str


@router.post("/ingest-city", response_model=IngestCityResponse)
async def ingest_city(
    request: IngestCityRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger OSM POI ingestion for a specific city
    
    This endpoint runs the ingestion script in the background.
    TODO: Add authentication middleware for admin-only access
    """
    # Validate city
    valid_cities = ["mumbai", "goa", "delhi"]
    if request.city.lower() not in valid_cities:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid city. Valid options: {valid_cities}"
        )
    
    # Add background task to run ingestion script
    background_tasks.add_task(
        run_ingestion_script,
        request.city,
        request.categories
    )
    
    logger.info(f"🚀 Started background ingestion for {request.city}")
    
    return IngestCityResponse(
        message=f"Ingestion started for {request.city}. Check logs for progress.",
        city=request.city,
        status="processing"
    )


def run_ingestion_script(city: str, categories: Optional[List[str]] = None):
    """Run the ingestion script as a subprocess"""
    script_path = Path(__file__).parent.parent.parent / "scripts" / "ingest_osm_pois.py"
    
    cmd = [sys.executable, str(script_path), city]
    
    if categories:
        cmd.extend(["--categories"] + categories)
    
    logger.info(f"Running command: {' '.join(cmd)}")
    
    try:
        # ✅ Better subprocess handling
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        stdout, stderr = process.communicate(timeout=600)
        
        if process.returncode == 0:
            logger.info(f"✅ Ingestion completed for {city}")
            # Log key metrics from output
            if "INGESTION COMPLETE" in stdout:
                for line in stdout.split('\n'):
                    if any(keyword in line for keyword in ['Total POIs', 'Stored', 'Embedded', 'Uploaded']):
                        logger.info(f"  {line.strip()}")
        else:
            logger.error(f"❌ Ingestion failed for {city}")
            if stderr:
                logger.error(f"Error output: {stderr[:500]}")  # First 500 chars
    
    except subprocess.TimeoutExpired:
        logger.error(f"⏱️ Ingestion timeout for {city}")
        process.kill()
    except Exception as e:
        logger.error(f"❌ Ingestion exception for {city}: {e}")



@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Admin API is running"
    }
