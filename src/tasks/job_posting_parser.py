import os
import json
import asyncio
import aiohttp
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from google import genai
import logging
from google.genai import types  # noqa
from rich.pretty import pprint

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


load_dotenv()

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


class JobPostingData(BaseModel):
    """Structured data model for job posting information"""
    job_title: str = Field(description="The title of the job position")
    job_posting_url: Optional[str] = Field(
        default=None, description="The url of the job posting")
    company: str = Field(description="The name of the company posting the job")
    location: Optional[str] = Field(
        default=None,
        description="Job location (city, state, country, or remote)")
    job_type: Optional[str] = Field(
        default=None,
        description="Type of employment (Full-time, Part-time, Contract, Internship, etc.)")
    experience_level: Optional[str] = Field(
        default=None,
        description="Required experience level (Entry, Mid, Senior, etc.)")
    years_of_experience: Optional[str] = Field(
        default=None, description="Required years of experience")
    salary_range: Optional[str] = Field(
        default=None, description="Salary range if mentioned")
    department: Optional[str] = Field(
        default=None, description="Department or team if mentioned")
    required_skills_qualifications: Optional[str] = Field(
        default=None, description="Required technical skills and qualifications")
    preferred_skills_qualifications: Optional[str] = Field(
        default=None, description="Preferred or nice-to-have skills and qualifications")
    role_responsibilities: Optional[str] = Field(
        default=None, description="Job responsibilities and duties if mentioned")
    benefits_perks: Optional[str] = Field(
        default=None, description="Benefits and perks mentioned")
    job_description: Optional[str] = Field(
        default=None, description="Full job description")
    work_arrangement: Optional[str] = Field(
        default=None, description="Work arrangement (Remote, Hybrid, On-site)")


class JobPostingParser:
    """Parser for extracting structured job posting data using Firecrawl + Gemini"""

    def __init__(self, firecrawl_api_key: Optional[str] = None):
        self.firecrawl_api_key = firecrawl_api_key or os.getenv(
            "FIRECRAWL_API_KEY")
        if not self.firecrawl_api_key:
            raise ValueError(
                "Firecrawl API key is required. Set FIRECRAWL_API_KEY environment variable or pass it to constructor.")

        self.firecrawl_base_url = "https://api.firecrawl.dev/v1"
        self.firecrawl_headers = {
            "Authorization": f"Bearer {self.firecrawl_api_key}",
            "Content-Type": "application/json"
        }

    async def scrape_job_posting(self, job_url: str) -> str:
        """
        Scrape job posting content using Firecrawl API in markdown format

        Args:
            job_url: URL of the job posting

        Returns:
            str: Markdown content of the job posting
        """
        try:
            payload = {
                "url": job_url,
                "formats": ["markdown"],
                "onlyMainContent": True,
                "blockAds": True,
                "proxy": "basic",
                "timeout": 30000
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.firecrawl_base_url}/scrape",
                    headers=self.firecrawl_headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()

                        if data.get("success") and data.get("data", {}).get("markdown"):
                            return data["data"]["markdown"]
                        else:
                            raise Exception(
                                f"Failed to scrape job data: {data.get('data', {}).get('error', 'Unknown error')}")
                    else:
                        error_text = await response.text()
                        raise Exception(
                            f"Firecrawl API request failed with status {response.status}: {error_text}")

        except Exception as e:
            logger.error(
                f"Error scraping job posting from {job_url}: {str(e)}")
            raise e

    async def parse_job_posting(self, job_url: str) -> JobPostingData:
        """
        Parse job posting from URL and return structured data

        Args:
            job_url: URL of the job posting

        Returns:
            JobPostingData: Structured job posting information
        """
        try:
            logger.info(f"Scraping job posting from: {job_url}")
            job_content = await self.scrape_job_posting(job_url)

            logger.info(
                "Parsing job content with Gemini using Pydantic schema.")

            system_prompt = f"""
            You are an expert job posting parser. Extract structured information from job postings with high accuracy.
            Focus on extracting:
            1. Exact job title and company name
            2. Location and remote work policy
            3. Experience requirements, level, years of experience, qualifications etc.
            4. Required and preferred technical skills
            5. Job responsibilities and duties
            6. Benefits and perks
            7. Any other relevant job details

            Be precise and extract only information that is explicitly mentioned in the job posting.
            For skills, focus on technical skills, programming languages, frameworks, tools, and technologies.
            
            Output JSON format:
            {JobPostingData.model_json_schema()}
            """

            user_prompt = f"""
            Please extract all relevant job posting information from the following job posting content.

            Pay special attention to:
            - Job title and company name
            - Location and work arrangement (remote, hybrid, on-site)
            - Experience requirements and years of experience
            - Required technical skills and qualifications
            - Preferred skills and nice-to-have qualifications
            - Job responsibilities and duties
            - Benefits and perks
            - Salary information if available
            - Application deadlines if mentioned
            - Visa sponsorship information if mentioned

            Job Posting Content:
            {job_content}

            Extract this information according to the provided schema in JSON format STRICTLY.
            """

            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[system_prompt, user_prompt],
                config={
                    "response_mime_type": "application/json",
                    "response_schema": JobPostingData
                }
            )

            logger.info("Extracting structured data from Gemini response...")

            try:
                if hasattr(response, 'parsed') and response.parsed:
                    parsed_job_data = response.parsed
                    pprint(parsed_job_data)
                    logger.info(
                        "Successfully parsed structured data using response.parsed")
                else:
                    logger.warning(
                        "response.parsed not available, falling back to manual parsing")
                    if hasattr(response, 'text') and response.text:
                        extracted_data = json.loads(response.text)
                        parsed_job_data = JobPostingData(**extracted_data)
                    else:
                        raise Exception("No response data found")
            except Exception as e:
                logger.error(f"Failed to extract structured data: {e}")
                raise Exception(
                    f"Failed to extract structured data from Gemini response: {e}")

            parsed_job_data.job_posting_url = job_url

            logger.info(
                f"Successfully created JobPostingData: {parsed_job_data.job_title} at {parsed_job_data.company}")

            return parsed_job_data

        except Exception as e:
            logger.error(
                f"Error parsing job posting from {job_url}: {str(e)}")

            try:
                logger.info(
                    "Attempting fallback parsing without structured output...")
                fallback_response = gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[f"""
                    Extract job information from this job posting and return as JSON:
                    {job_content}

                    Return only a JSON object with these fields:
                    - job_title (string)
                    - company (string)
                    - location (string, optional)
                    - job_type (string, optional)
                    - experience_level (string, optional)
                    - years_of_experience (string, optional)
                    - required_skills_qualifications (array of strings, optional)
                    - preferred_skills_qualifications (array of strings, optional)
                    - job_description (string)
                    """],
                    config={
                        "response_mime_type": "application/json",
                        "response_schema": JobPostingData
                    }
                )

                if hasattr(fallback_response, 'parsed') and fallback_response.parsed:
                    parsed_job_data = fallback_response.parsed
                else:
                    fallback_data = json.loads(fallback_response.text)
                    parsed_job_data = JobPostingData(**fallback_data)

                parsed_job_data.job_posting_url = job_url
                logger.info("Fallback parsing successful")
                return parsed_job_data

            except Exception as fallback_error:
                logger.error(
                    f"Fallback parsing also failed: {fallback_error}")
                return JobPostingData(
                    job_title="Unknown",
                    company="Unknown",
                    location="Unknown",
                    job_type="Full-time",
                    experience_level="Unknown",
                    years_of_experience="Unknown",
                    job_description=f"Failed to parse job posting: {str(e)}"
                )

    async def parse_multiple_jobs(self, job_urls: list) -> list[JobPostingData]:
        """
        Parse multiple job postings concurrently

        Args:
            job_urls: List of job posting URLs

        Returns:
            list[JobPostingData]: List of structured job posting data
        """
        tasks = [self.parse_job_posting(url) for url in job_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid_results = []
        for result in results:
            if isinstance(result, JobPostingData):
                valid_results.append(result)
            else:
                logger.error(f"Failed to parse job: {result}")

        return valid_results


def create_job_info_from_parsed_data(parsed_data: JobPostingData, job_url: str) -> Dict[str, Any]:
    """
    Convert parsed job posting data to the format expected by email generation service

    Args:
        parsed_data: Parsed job posting data
        job_url: Original job URL

    Returns:
        Dict containing job information in email generation format
    """
    return {
        "job_title": parsed_data.job_title,
        "company": parsed_data.company,
        "job_url": job_url,
        "years_of_experience": parsed_data.years_of_experience,
        "location": parsed_data.location,
        "job_type": parsed_data.job_type,
        "department": parsed_data.department or "Engineering",
        "required_skills": parsed_data.required_skills_qualifications or [],
        "preferred_skills": parsed_data.preferred_skills_qualifications or [],
        "job_description": parsed_data.job_description,
        "experience_level": parsed_data.experience_level,
        "salary_range": parsed_data.salary_range,
        "responsibilities": parsed_data.role_responsibilities,
        "benefits": parsed_data.benefits_perks or [],
        "remote_policy": parsed_data.work_arrangement,
    }


async def main():
    """Example usage of the job posting parser"""
    parser = JobPostingParser()

    job_urls = [
        "https://www.uber.com/global/en/careers/list/144219/",
        # "https://jobs.careers.microsoft.com/global/en/job/1847896",
        "https://www.rubrik.com/company/careers/departments/job.6109450.1929"
    ]

    for i, url in enumerate(job_urls, 1):
        logger.info(f"\n{i}. Testing URL: {url}")

        try:
            logger.info("Step 1: Scraping job content with Firecrawl...")
            job_content = await parser.scrape_job_posting(url)
            logger.info(
                f"Successfully scraped {len(job_content)} characters of content")
            logger.info(f"Content preview: {job_content[:200]}...")

            logger.info("\nStep 2: Parsing with Gemini...")
            job_data = await parser.parse_job_posting(url)

            logger.info("✅ Successfully parsed job posting!")
            logger.info(f"   Job Title: {job_data.job_title}")
            logger.info(f"   Company: {job_data.company}")
            logger.info(f"   Location: {job_data.location}")
            logger.info(f"   Experience: {job_data.years_of_experience}")
            logger.info(f"   Job Type: {job_data.job_type}")
            logger.info(
                f"   Required Skills: {job_data.required_skills_qualifications[:5] if job_data.required_skills_qualifications else 'None'}...")
            logger.info(
                f"   Preferred Skills: {job_data.preferred_skills_qualifications[:3] if job_data.preferred_skills_qualifications else 'None'}...")

            job_info = create_job_info_from_parsed_data(job_data, url)
            logger.info("\n   Job Info for Email Generation:")
            logger.info(f"   {json.dumps(job_info, indent=4)}")

        except Exception as e:
            logger.error(f"❌ Failed to parse {url}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
