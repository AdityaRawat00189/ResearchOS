"""
FastAPI application — endpoints for job submission, status polling,
document preview, and file download.
"""
import os
import uuid
import logging
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.models import GenerateRequest, StatusResponse
from app.state import GraphState
from app.job_store import job_store
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

NODE_PROGRESS = {
    "input_init": 10,
    "web_search": 20,
    "extraction": 35,
    "relevance_check": 45,
    "outline": 55,
    "section_writer": 70,
    "quality_recheck": 80,
    "validation": 90,
    "export": 100,
    "completed": 100,
    "error": 0,
}

ALL_NODES = [
    "input_init", "web_search", "extraction", "relevance_check",
    "outline", "section_writer", "quality_recheck", "validation", "export",
]


def run_pipeline(job_id: str, initial_state: dict) -> None:
    """Execute the LangGraph pipeline synchronously (called in a background thread)."""
    from app.graph.builder import research_graph

    try:
        logger.info("Starting pipeline for job %s", job_id)
        job_store.set_status(job_id, "running", node="input_init", progress=5)

        config = {"recursion_limit": settings.recursion_limit}
        final_state = research_graph.invoke(initial_state, config=config)

        job_store.update(job_id, {
            "status": "completed",
            "current_node": "completed",
            "progress_pct": 100,
            "final_doc_path": final_state.get("final_doc_path"),
            "nodes_completed": ALL_NODES,
        })
        logger.info("Pipeline completed for job %s", job_id)

    except Exception as exc:
        logger.error("Pipeline failed for job %s: %s", job_id, exc, exc_info=True)
        job_store.set_status(job_id, "error", error=str(exc))


app = FastAPI(
    title="ResearchOS",
    description="Automated Research Paper Generation Pipeline",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "ResearchOS"}


@app.post("/generate")
async def generate_paper(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
):
    """Submit a new paper generation job.

    Returns the job_id for status polling.
    """
    job_id = uuid.uuid4().hex[:12]

    initial_state: GraphState = {
        "job_id": job_id,
        "topic": request.topic,
        "min_pages": request.min_pages,
        "citation_style": request.citation_style,
        "keywords": request.keywords or [],
        "domain": request.domain or "",
        "search_queries": [],
        "search_results": [],
        "chunks": [],
        "relevance_retry_count": 0,
        "outline": [],
        "sections": {},
        "writing_retry_count": {},
        "validation_report": {},
        "validation_retry_count": 0,
        "final_doc_path": None,
        "status": "queued",
        "nodes_completed": [],
        "error": None,
    }

    job_store.create(job_id, {
        "status": "queued",
        "current_node": "",
        "progress_pct": 0,
        "error": None,
        "nodes_completed": [],
        "final_doc_path": None,
    })

    background_tasks.add_task(run_pipeline, job_id, initial_state)

    logger.info("Job %s queued for topic: %s", job_id, request.topic)
    return {"job_id": job_id}


@app.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str):
    """Poll the current status of a generation job."""
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    current_node = job.get("current_node", "")
    return StatusResponse(
        job_id=job_id,
        status=job.get("status", "unknown"),
        current_node=current_node,
        progress_pct=job.get("progress_pct", NODE_PROGRESS.get(current_node, 0)),
        error=job.get("error"),
        nodes_completed=job.get("nodes_completed", []),
    )


@app.get("/download/{job_id}")
async def download_file(job_id: str):
    """Download the generated .docx file."""
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    doc_path = job.get("final_doc_path")
    if not doc_path or not os.path.exists(doc_path):
        raise HTTPException(
            status_code=404,
            detail="Document not yet generated or file not found",
        )

    return FileResponse(
        path=doc_path,
        filename=os.path.basename(doc_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@app.get("/preview/{job_id}")
async def preview_file(job_id: str):
    """Return the .docx file bytes for frontend preview (mammoth.js)."""
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    doc_path = job.get("final_doc_path")
    if not doc_path or not os.path.exists(doc_path):
        raise HTTPException(
            status_code=404,
            detail="Document not yet generated or file not found",
        )

    return FileResponse(
        path=doc_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@app.get("/jobs")
async def list_jobs():
    """List all job IDs."""
    return {"jobs": job_store.list_jobs()}
