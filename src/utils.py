import asyncio
import json
import os
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field
from rich.pretty import pprint  # noqa
try:
    from src.main import parse_resume, CandidateResumeData
    from src.tasks.job_posting_parser import JobPostingParser, create_job_info_from_parsed_data
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
    from main import parse_resume, CandidateResumeData
    from tasks.job_posting_parser import JobPostingParser, create_job_info_from_parsed_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

load_dotenv()
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


class ReceiverDetails(BaseModel):
    """Structured data model for receiver information"""
    name: str = Field(description="Name of the receiver")
    email: str = Field(description="Email address of the receiver")
    job_title: Optional[str] = Field(
        default=None, description="Job title of the receiver")
    company: Optional[str] = Field(
        default=None, description="Company of the receiver")


class SenderDetails(BaseModel):
    """Structured data model for sender information"""
    name: str = Field(description="Name of the sender")
    email: str = Field(description="Email address of the sender")
    phone: str = Field(description="Phone number of the sender")
    technical_skills: Dict[str, Any] = Field(
        description="Technical skills of the sender")
    experience: List[Dict[str, Any]] = Field(
        description="Work experience of the sender")
    projects: List[str] = Field(description="Projects of the sender")
    education: List[Dict[str, Any]] = Field(
        description="Education of the sender")
    certifications: Optional[List[str]] = Field(
        default=None, description="Certifications of the sender")
    key_accomplishments: Optional[str] = Field(
        default=None, description="Key accomplishments of the sender")


class SampleInputGenerator:
    """Generator for creating enhanced sample inputs using job posting parser and resume data"""

    def __init__(self):
        self.job_parser = JobPostingParser()
        self.job_urls = {
            "uber_ml": "https://www.uber.com/global/en/careers/list/144219",
            "microsoft_swe": "https://jobs.careers.microsoft.com/global/en/job/1847896",
            "rubrik_backend": "https://www.rubrik.com/company/careers/departments/job.6109450.1929"
        }

    async def parse_resume_data(self, pdf_path: str) -> Optional[CandidateResumeData]:
        """
        Parse resume and return structured data

        Args:
            pdf_path: Path to the PDF resume file

        Returns:
            CandidateResumeData: Parsed resume data or None if parsing fails
        """
        try:
            logger.info(f"Parsing resume: {pdf_path}")
            parsed_data = await parse_resume(pdf_path, CandidateResumeData)
            logger.info(f"Successfully parsed resume for: {parsed_data.name}")
            return parsed_data
        except Exception as e:
            logger.error(f"Error parsing resume {pdf_path}: {e}")
            return None

    def create_receiver_details(self, name: str, email: str, job_title: str = None, company: str = None) -> ReceiverDetails:
        """
        Create receiver details structure

        Args:
            name: Name of the receiver
            email: Email address of the receiver
            job_title: Job title of the receiver (optional)
            company: Company of the receiver (optional)

        Returns:
            ReceiverDetails: Structured receiver information
        """
        return ReceiverDetails(
            name=name,
            email=email,
            job_title=job_title,
            company=company
        )

    def create_sender_details(self, resume_data: CandidateResumeData) -> SenderDetails:
        """
        Create sender details from resume data

        Args:
            resume_data: Parsed resume data

        Returns:
            SenderDetails: Structured sender information
        """
        return SenderDetails(
            name=resume_data.name,
            email=resume_data.email,
            phone=resume_data.phone,
            technical_skills=resume_data.technical_skills.model_dump(),
            experience=[exp.model_dump() for exp in resume_data.experience],
            projects=resume_data.projects,
            education=[edu.model_dump() for edu in resume_data.education],
            certifications=resume_data.certifications if hasattr(
                resume_data, "certifications") else None,
            key_accomplishments=resume_data.key_accomplishments if hasattr(
                resume_data, "key_accomplishments") else None
        )

    async def parse_job_postings(self) -> Dict[str, Any]:
        """
        Parse job postings from configured URLs

        Returns:
            Dict[str, Any]: Dictionary of parsed job data
        """
        logger.info("Parsing job postings...")
        job_data = {}

        for job_name, url in self.job_urls.items():
            try:
                logger.info(f"Parsing job posting: {job_name}")
                parsed_job = await self.job_parser.parse_job_posting(url)
                job_data[job_name] = parsed_job
                logger.info(
                    f"Successfully parsed {job_name}: {parsed_job.job_title} at {parsed_job.company}")
            except Exception as e:
                logger.error(f"Failed to parse {job_name}: {e}")
                job_data[job_name] = self._create_fallback_job_data(job_name)

        return job_data

    def _create_fallback_job_data(self, job_name: str) -> Any:
        """
        Create fallback job data when parsing fails

        Args:
            job_name: Name of the job posting

        Returns:
            Object with job data structure
        """
        if job_name == "uber_ml":
            return type('obj', (object,), {
                'job_title': 'ML Engineer',
                'company': 'Uber',
                'location': 'San Francisco, CA / Remote',
                'job_type': 'Full-time',
                'experience_level': 'Mid',
                'years_of_experience': '1+',
                'required_skills': ['Python', 'Machine Learning', 'Deep Learning', 'TensorFlow/PyTorch'],
                'preferred_skills': ['Computer Vision', 'NLP', 'AWS', 'Docker'],
                'job_description': 'ML Engineer role at Uber focusing on developing and deploying machine learning models.'
            })()
        elif job_name == "microsoft_swe":
            return type('obj', (object,), {
                'job_title': 'Software Engineer',
                'company': 'Microsoft',
                'location': 'Redmond, WA / Remote',
                'job_type': 'Full-time',
                'experience_level': 'Mid',
                'years_of_experience': '1+',
                'required_skills': ['Java', 'C#', 'JavaScript', 'Web Development'],
                'preferred_skills': ['Azure', 'React', 'Spring Boot', '.NET Core'],
                'job_description': 'Software Engineer role at Microsoft building innovative solutions.'
            })()
        elif job_name == "rubrik_backend":
            return type('obj', (object,), {
                'job_title': 'Backend Engineer',
                'company': 'Rubrik',
                'location': 'Tel Aviv, Israel / Remote',
                'job_type': 'Full-time',
                'experience_level': 'Mid-Senior',
                'years_of_experience': '3+',
                'required_skills': ['Golang', 'Python', 'SQL', 'Distributed Systems'],
                'preferred_skills': ['AWS', 'Azure', 'GCP', 'Cybersecurity'],
                'job_description': 'Backend Engineer role at Rubrik building cloud-native security solutions.'
            })()

    def create_sample_input(self, receiver_details: ReceiverDetails, sender_details: SenderDetails, job_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a complete sample input for email generation

        Args:
            receiver_details: Receiver information
            sender_details: Sender information
            job_info: Job information

        Returns:
            Dict[str, Any]: Complete sample input structure
        """
        return {
            "receiver_details": receiver_details.model_dump(),
            "sender_details": sender_details.model_dump(),
            "job_information": job_info
        }

    async def generate_enhanced_sample_inputs(self):
        """Generate enhanced sample inputs using job posting parser and resume data"""
        try:
            logger.info("Starting enhanced sample input generation...")

            logger.info("Parsing resumes...")
            abhishek_data = await self.parse_resume_data("data/120CS0208_Abhishek_sc.pdf")
            sumit_data = await self.parse_resume_data("data/Sumit-Nainani-2810.pdf")

            if not abhishek_data or not sumit_data:
                logger.error("Failed to parse one or more resumes")
                return

            job_data = await self.parse_job_postings()

            logger.info("Creating sample 1: ML Engineer at Uber")
            uber_job_info = create_job_info_from_parsed_data(
                job_data["uber_ml"], self.job_urls["uber_ml"])

            sample_1 = self.create_sample_input(
                receiver_details=self.create_receiver_details(
                    name="Sarah Johnson",
                    email="sarah.johnson@uber.com",
                    job_title="Senior ML Engineer",
                    company="Uber"
                ),
                sender_details=self.create_sender_details(abhishek_data),
                job_info=uber_job_info
            )

            logger.info("Creating sample 2: Software Engineer at Microsoft")
            microsoft_job_info = create_job_info_from_parsed_data(
                job_data["microsoft_swe"], self.job_urls["microsoft_swe"])

            sample_2 = self.create_sample_input(
                receiver_details=self.create_receiver_details(
                    name="Michael Chen",
                    email="michael.chen@microsoft.com",
                    job_title="Senior Software Engineer",
                    company="Microsoft"
                ),
                sender_details=self.create_sender_details(sumit_data),
                job_info=microsoft_job_info
            )

            logger.info("Writing sample inputs to files...")
            with open("data/sample_ip_email_gen_mle.json", "w") as f:
                json.dump(sample_1, f, indent=2)

            with open("data/sample_ip_email_gen_swe.json", "w") as f:
                json.dump(sample_2, f, indent=2)

            logger.info("✅ Enhanced sample inputs generated successfully!")
            logger.info("Files created:")
            logger.info(
                "- data/sample_ip_email_gen_mle.json (ML Engineer at Uber)")
            logger.info(
                "- data/sample_ip_email_gen_swe.json (Software Engineer at Microsoft)")

            self._print_job_summary(job_data)

        except Exception as e:
            logger.error(f"Error generating enhanced sample inputs: {e}")
            raise

    def _print_job_summary(self, job_data: Dict[str, Any]):
        """Print summary of parsed job information"""
        logger.info("\nParsed Job Information Summary:")
        for job_name, job in job_data.items():
            logger.info(f"\n{job.company} - {job.job_title}:")
            logger.info(f"  Location: {job.location}")
            logger.info(f"  Experience: {job.years_of_experience}")
            if hasattr(job, 'required_skills') and job.required_skills:
                skills_preview = job.required_skills[:3] if isinstance(
                    job.required_skills, list) else str(job.required_skills)[:50]
                logger.info(f"  Required Skills: {skills_preview}...")


async def main():
    """Main function to run the sample input generator"""
    try:
        generator = SampleInputGenerator()
        await generator.generate_enhanced_sample_inputs()
    except Exception as e:
        logger.error(f"Failed to generate sample inputs: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
