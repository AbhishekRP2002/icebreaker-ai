from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import tempfile
import asyncio  # noqa: F401
from pydantic import ValidationError
from src.main import parse_resume, CandidateResumeData
from src.tasks.job_posting_parser import JobPostingParser

app = FastAPI(title="Icebreaker AI",
              description="Icebreaker AI is a platform that helps you find the perfect job for you.",
              version="0.1.0")


@app.post("/parse_resume")
async def parse_resume_endpoint(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400, detail="Only PDF files are supported.")
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        try:
            resume_data = await parse_resume(tmp_path, CandidateResumeData)
        except ValidationError as ve:
            raise HTTPException(status_code=422, detail=str(ve))
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Resume parsing failed: {str(e)}")
        finally:
            os.remove(tmp_path)
        return JSONResponse(content=resume_data.model_dump())
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"File handling failed: {str(e)}")


@app.post("/parse_job_posting")
async def parse_job_posting_endpoint(job_url: str):
    """
    Parse job posting from a given URL and return structured job information

    Args:
        job_url: URL of the job posting to parse

    Returns:
        JSONResponse: Structured job posting data
    """
    if not job_url or not job_url.strip():
        raise HTTPException(
            status_code=400, detail="Job URL is required and cannot be empty.")

    try:
        parser = JobPostingParser()

        job_data = await parser.parse_job_posting(job_url)

        return JSONResponse(content=job_data.model_dump())

    except ValueError as ve:
        raise HTTPException(
            status_code=400, detail=f"Configuration error: {str(ve)}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Job posting parsing failed: {str(e)}")


@app.get("/check-health")
async def check_health():
    return JSONResponse(content={"status": "ok"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
