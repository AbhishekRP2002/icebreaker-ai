from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import tempfile
import asyncio  # noqa: F401
from pydantic import ValidationError
from src.main import parse_resume, CandidateResumeData

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


@app.get("/check-health")
async def check_health():
    return JSONResponse(content={"status": "ok"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
