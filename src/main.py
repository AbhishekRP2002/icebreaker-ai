import click
import os
import json
import asyncio
import aiosqlite
import logging
from dotenv import load_dotenv
from llama_cloud_services import LlamaExtract
from pydantic import BaseModel, Field
from llama_cloud.core.api_error import ApiError
from typing import Optional, List
from rich.pretty import pprint


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


async def parse_resume(pdf_path: str):
    logger.info(f"Extracting data from resume: {pdf_path}")
    try:
        existing_agent = extractor.get_agent(name="resume-screening")
        if existing_agent:
            extractor.delete_agent(existing_agent.id)
    except ApiError as e:
        if e.status_code == 404:
            pass
        else:
            raise

    extractor_agent = extractor.create_agent(
        name="resume-screening", data_schema=CandidateResumeData
    )
    resume_data = extractor_agent.extract(pdf_path)
    pprint(resume_data)
    return resume_data.data


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
                data["name"],
                data["email"],
                data["phone"],
                json.dumps(data["technical_skills"].dict()),
                json.dumps([exp.dict() for exp in data["experience"]]),
                json.dumps(data["projects"]),
                json.dumps([edu.dict() for edu in data["education"]]),
                json.dumps(data.get("certifications")),
                data.get("key_accomplishments"),
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
    parsed_data = await parse_resume(pdf_path)
    await store_in_db(parsed_data)
    click.echo("✅ Resume parsed and stored successfully!")
    click.echo(json.dumps(parsed_data, indent=4))


if __name__ == "__main__":
    cli()
