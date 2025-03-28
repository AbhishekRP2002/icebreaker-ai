import click
import os
import json
import asyncio
import aiosqlite
import logging
from dotenv import load_dotenv
from llama_cloud_services import LlamaExtract
from pydantic import BaseModel, Field
from typing import Optional, List
from rich.pretty import pprint
from google import genai


load_dotenv()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("icebreaker-agent")
extractor = LlamaExtract(
    api_key=os.getenv("LLAMA_CLOUD_API_KEY"),
    organization_id=os.getenv("LLAMA_CLOUD_ORG_ID"),
    project_id=os.getenv("LLAMA_CLOUD_PROJECT_ID"),
)
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


class Education(BaseModel):
    institution: str = Field(description="The institution of the candidate")
    degree: str = Field(description="The degree of the candidate")
    start_date: Optional[str] = Field(
        default=None, description="The start date of the candidate's education"
    )
    end_date: Optional[str] = Field(
        default=None, description="The end date of the candidate's education"
    )


class Experience(BaseModel):
    company: str = Field(description="The name of the company")
    title: str = Field(description="The title of the candidate")
    description: Optional[str] = Field(
        default=None, description="The description of the candidate's experience"
    )
    start_date: Optional[str] = Field(
        default=None, description="The start date of the candidate's experience"
    )
    end_date: Optional[str] = Field(
        default=None, description="The end date of the candidate's experience"
    )


class TechnicalSkills(BaseModel):
    programming_languages: List[str] = Field(
        description="The programming languages the candidate is proficient in."
    )
    frameworks: List[str] = Field(
        description="The tools/frameworks the candidate is proficient in, e.g. React, Django, PyTorch, etc."
    )
    skills: List[str] = Field(
        description="Other general skills the candidate is proficient in, e.g. Data Engineering, Machine Learning, etc."
    )


class CandidateResumeData(BaseModel):
    name: str = Field(description="name of the candidate")
    email: str = Field(description="email address of the candidate")
    phone: str = Field(description="phone number of the candidate")
    technical_skills: TechnicalSkills = Field(
        description="Technical skills of the candidate"
    )
    experience: List[Experience] = Field(
        description="Work experience details of the candidate"
    )
    projects: List[str] = Field(description="List of projects mentioned in the resume")
    education: List[Education] = Field(description="Education details of the candidate")
    certifications: Optional[List[str]] = Field(
        description="Certifications earned by the candidate"
    )
    key_accomplishments: Optional[str] = Field(
        description="Summarize the candidates highest achievements."
    )


async def init_db():
    async with aiosqlite.connect("db/resume_data.db") as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT,
                phone TEXT,
                technical_skills TEXT,
                experience TEXT,
                projects TEXT,
                education TEXT,
                certifications TEXT,
                key_accomplishments TEXT
            )
        """)
        logger.info("Database initialized.")
        await conn.commit()


async def parse_resume(pdf_path: str, model: BaseModel):
    logger.info(f"Extracting data from resume: {pdf_path}")
    file = gemini_client.files.upload(
        file=pdf_path, config={"display_name": pdf_path.split("/")[-1].split(".")[0]}
    )
    prompt = """
    You are an expert resume screening agent who has been tasked with extracting structured data about a candidate from their resume.
    Extract the following information in JSON format:
    - name: string
    - email: string
    - phone: string
    - technical_skills: object containing programming_languages (array), frameworks (array), and skills (array)
    - experience: array of objects containing company, title, description, start_date, and end_date
    - projects: array of strings
    - education: array of objects containing institution, degree, start_date, and end_date
    - certifications: array of strings (optional)
    - key_accomplishments: string (optional)
    """
    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt, file],
        config={"response_mime_type": "application/json", "response_schema": model},
    )
    pprint(response)
    resume_data = response.parsed
    return resume_data


# store parsed data in sql db
async def store_in_db(data):
    async with aiosqlite.connect("db/resume_data.db") as conn:
        await conn.execute(
            """
            INSERT INTO candidates (
                name, email, phone, technical_skills, experience,
                projects, education, certifications, key_accomplishments
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.name,
                data.email,
                data.phone,
                json.dumps(data.technical_skills.model_dump()),
                json.dumps([exp.model_dump() for exp in data.experience]),
                json.dumps(data.projects),
                json.dumps([edu.model_dump() for edu in data.education]),
                json.dumps(
                    data.certifications if hasattr(data, "certifications") else None
                ),
                data.key_accomplishments
                if hasattr(data, "key_accomplishments")
                else None,
            ),
        )
        await conn.commit()


@click.command()
@click.argument("pdf_path", type=click.Path(exists=True))
def cli(pdf_path):
    "CLI tool to parse resumes and store structured data in SQLite."
    asyncio.run(main(pdf_path))


async def main(pdf_path):
    await init_db()
    parsed_data = await parse_resume(pdf_path, CandidateResumeData)
    await store_in_db(parsed_data)
    click.echo("✅ Resume parsed and stored successfully!")


if __name__ == "__main__":
    cli()
