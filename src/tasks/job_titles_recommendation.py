import json
from typing import List
from google import genai
from src.tasks.resume_parser import CandidateResumeData
import os
from dotenv import load_dotenv

load_dotenv()

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


async def generate_job_titles(
    resume_data: CandidateResumeData, given_job_title: str = None
) -> List[str]:
    prompt = ""
    if given_job_title:
        prompt = f"""Based on the candidate's experience, past projects and skills, suggest 5 more similar job titles to '{given_job_title}' 
        which closely align with the candidate's profile making him an ideal feat for the job role.
        Consider their:
        - Technical skills: {resume_data.technical_skills.model_dump()}
        - Experience: {[exp.model_dump() for exp in resume_data.experience]}
        - Education: {[edu.model_dump() for edu in resume_data.education]}
        Return only a JSON array of strings containing the job titles."""
    else:
        prompt = f"""Based on the candidate's experience, past projects and skills, suggest the top 3 job titles 
        the candidate has the maximum change of getting interviewed. 
        Consider their:
        - Technical skills: {resume_data.technical_skills.model_dump()}
        - Experience: {[exp.model_dump() for exp in resume_data.experience]}
        - Education: {[edu.model_dump() for edu in resume_data.education]}
        Return only a JSON array of strings containing the job titles."""

    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt],
        config={"response_mime_type": "application/json"},
    )

    return json.loads(response.text)
