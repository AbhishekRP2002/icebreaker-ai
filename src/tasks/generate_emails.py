"""
module to generate email for the candidate for a given job posting
1-1 mapping b/w candidate and employee working in the target company
"""
import json
import asyncio
from typing import Dict, List, Optional, Any, TypedDict
from enum import Enum

from langgraph.graph import StateGraph, START, END
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class EmailType(str, Enum):
    SIMPLE = "simple"
    PERSONALIZED = "personalized"
    CONTEXTUAL = "contextual"


class Tone(str, Enum):
    FORMAL = "formal"
    FRIENDLY = "friendly"
    CONCISE = "concise"
    ENTHUSIASTIC = "enthusiastic"


class EmailState(TypedDict):
    """State for the email generation workflow"""
    receiver_details: Dict[str, Any]
    sender_details: Dict[str, Any]
    job_information: Dict[str, Any]
    email_type: EmailType
    tone: Tone
    contextual_data: Optional[Dict[str, Any]]
    generated_email: Optional[str]
    email_subject: Optional[str]
    error: Optional[str]


class EmailGenerator:
    """Main class for generating personalized cold emails"""

    def __init__(self, model_name: str = "claude-3-sonnet-20240229"):
        self.model = ChatAnthropic(model=model_name, temperature=0.7)
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> StateGraph:
        """Create the LangGraph workflow for email generation"""

        workflow = StateGraph(EmailState)

        # Add nodes
        workflow.add_node("validate_input", self._validate_input)
        workflow.add_node("extract_context", self._extract_context)
        workflow.add_node("generate_simple_email", self._generate_simple_email)
        workflow.add_node("generate_personalized_email",
                          self._generate_personalized_email)
        workflow.add_node("generate_contextual_email",
                          self._generate_contextual_email)
        workflow.add_node("finalize_email", self._finalize_email)

        # Add edges
        workflow.add_edge(START, "validate_input")
        workflow.add_edge("validate_input", "extract_context")

        # Conditional routing based on email type
        workflow.add_conditional_edges(
            "extract_context",
            self._route_email_type,
            {
                EmailType.SIMPLE: "generate_simple_email",
                EmailType.PERSONALIZED: "generate_personalized_email",
                EmailType.CONTEXTUAL: "generate_contextual_email"
            }
        )

        workflow.add_edge("generate_simple_email", "finalize_email")
        workflow.add_edge("generate_personalized_email", "finalize_email")
        workflow.add_edge("generate_contextual_email", "finalize_email")
        workflow.add_edge("finalize_email", END)

        return workflow.compile()

    async def _validate_input(self, state: EmailState) -> EmailState:
        """Validate input data and set defaults"""
        try:
            # Validate required fields
            required_fields = ["receiver_details",
                               "sender_details", "job_information"]
            for field in required_fields:
                if field not in state or not state[field]:
                    raise ValueError(f"Missing required field: {field}")

            # Set default email type and tone if not provided
            if "email_type" not in state:
                state["email_type"] = EmailType.SIMPLE

            if "tone" not in state:
                state["tone"] = Tone.FRIENDLY

            # Initialize contextual data
            if "contextual_data" not in state:
                state["contextual_data"] = {}

            return state

        except Exception as e:
            state["error"] = f"Validation error: {str(e)}"
            return state

    async def _extract_context(self, state: EmailState) -> EmailState:
        """Extract contextual information for personalized emails"""
        try:
            if state["email_type"] in [EmailType.PERSONALIZED, EmailType.CONTEXTUAL]:
                # Extract key information for personalization
                contextual_data = {
                    "sender_skills": state["sender_details"].get("technical_skills", {}),
                    "sender_experience": state["sender_details"].get("experience", []),
                    "sender_projects": state["sender_details"].get("projects", []),
                    "job_requirements": state["job_information"].get("required_skills", ""),
                    "job_preferred": state["job_information"].get("preferred_skills", ""),
                    "company_name": state["job_information"].get("company", ""),
                    "job_title": state["job_information"].get("job_title", ""),
                    "receiver_name": state["receiver_details"].get("name", ""),
                    "receiver_title": state["receiver_details"].get("job_title", "")
                }

                # For contextual emails, we would add more data here
                if state["email_type"] == EmailType.CONTEXTUAL:
                    contextual_data.update({
                        "github_data": await self._fetch_github_data(state),
                        "company_news": await self._fetch_company_news(state),
                        "linkedin_data": await self._fetch_linkedin_data(state)
                    })

                state["contextual_data"] = contextual_data

            return state

        except Exception as e:
            state["error"] = f"Context extraction error: {str(e)}"
            return state

    async def _fetch_github_data(self, state: EmailState) -> Dict[str, Any]:
        """Fetch GitHub data using utility functions"""
        from ..utils import GitHubAPI

        try:
            github_api = GitHubAPI()
            username = state["sender_details"].get("github_username")

            if not username:
                return {
                    "recent_commits": [],
                    "top_languages": [],
                    "popular_repos": [],
                    "contribution_graph": {}
                }

            # Fetch user info, repos, and activity concurrently
            user_info, repos, activity = await asyncio.gather(
                github_api.get_user_info(username),
                github_api.get_user_repos(username),
                github_api.get_user_activity(username)
            )

            return {
                "user_info": user_info,
                "repositories": repos,
                "activity": activity
            }
        except Exception as e:
            print(f"Error fetching GitHub data: {e}")
            return {
                "recent_commits": [],
                "top_languages": [],
                "popular_repos": [],
                "contribution_graph": {}
            }

    async def _fetch_company_news(self, state: EmailState) -> Dict[str, Any]:
        """Fetch company news using utility functions"""
        from ..utils import CompanyNewsAPI, WebScraper

        try:
            company_name = state["job_information"].get("company", "")
            if not company_name:
                return {
                    "recent_news": [],
                    "tech_announcements": [],
                    "company_events": []
                }

            async with CompanyNewsAPI() as news_api:
                async with WebScraper() as scraper:
                    news, tech_news, website_info, events = await asyncio.gather(
                        news_api.search_company_news(company_name),
                        news_api.get_company_tech_news(company_name),
                        scraper.scrape_company_website(company_name),
                        scraper.search_tech_events(company_name)
                    )

                    return {
                        "general_news": news,
                        "tech_news": tech_news,
                        "website_info": website_info,
                        "events": events
                    }
        except Exception as e:
            print(f"Error fetching company news: {e}")
            return {
                "recent_news": [],
                "tech_announcements": [],
                "company_events": []
            }

    async def _fetch_linkedin_data(self, state: EmailState) -> Dict[str, Any]:
        """Fetch LinkedIn data using utility functions"""
        from ..utils import LinkedInAPI

        try:
            linkedin_api = LinkedInAPI()
            company_name = state["job_information"].get("company", "")

            if not company_name:
                return {
                    "receiver_posts": [],
                    "company_updates": [],
                    "shared_connections": []
                }

            company_updates = await linkedin_api.get_company_updates(company_name)

            return {
                "company_updates": company_updates,
                "receiver_posts": [],
                "shared_connections": []
            }
        except Exception as e:
            print(f"Error fetching LinkedIn data: {e}")
            return {
                "receiver_posts": [],
                "company_updates": [],
                "shared_connections": []
            }

    def _route_email_type(self, state: EmailState) -> EmailType:
        """Route to appropriate email generation based on type"""
        return state["email_type"]

    async def _generate_simple_email(self, state: EmailState) -> EmailState:
        """Generate a simple, template-based email"""
        try:
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="""You are an expert at writing professional cold emails for job referrals. 
                Generate a simple, professional email that introduces the candidate and expresses interest in the job opportunity.
                Keep it concise and professional while maintaining the specified tone."""),
                MessagesPlaceholder(variable_name="context"),
                HumanMessage(content="""Generate a simple cold email with the following details:
                
                Receiver: {receiver_name} ({receiver_title} at {company})
                Sender: {sender_name} ({sender_email})
                Job: {job_title} at {company}
                Tone: {tone}
                
                Requirements:
                - Keep it under 150 words
                - Use the specified tone
                - Include a clear call to action
                - Be professional but approachable""")
            ])

            context = self._build_context_message(state)

            chain = prompt | self.model
            response = await chain.ainvoke({
                "context": context,
                "receiver_name": state["receiver_details"]["name"],
                "receiver_title": state["receiver_details"]["job_title"],
                "company": state["job_information"]["company"],
                "sender_name": state["sender_details"]["name"],
                "sender_email": state["sender_details"]["email"],
                "job_title": state["job_information"]["job_title"],
                "tone": state["tone"]
            })

            state["generated_email"] = response.content
            return state

        except Exception as e:
            state["error"] = f"Simple email generation error: {str(e)}"
            return state

    async def _generate_personalized_email(self, state: EmailState) -> EmailState:
        """Generate a personalized email using candidate and job information"""
        try:
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="""You are an expert at writing personalized cold emails for job referrals.
                Create a personalized email that highlights the candidate's relevant experience and skills that match the job requirements.
                Use specific examples from their background to show why they're a great fit."""),
                MessagesPlaceholder(variable_name="context"),
                HumanMessage(content="""Generate a personalized cold email with the following details:
                
                Receiver: {receiver_name} ({receiver_title} at {company})
                Sender: {sender_name} ({sender_email})
                Job: {job_title} at {company}
                Tone: {tone}
                
                Sender Skills: {sender_skills}
                Sender Experience: {sender_experience}
                Job Requirements: {job_requirements}
                Job Preferred: {job_preferred}
                
                Requirements:
                - Highlight 2-3 specific skills/experiences that match the job
                - Reference specific projects or achievements
                - Keep it under 200 words
                - Use the specified tone
                - Include a clear call to action""")
            ])

            context = self._build_context_message(state)

            chain = prompt | self.model
            response = await chain.ainvoke({
                "context": context,
                "receiver_name": state["receiver_details"]["name"],
                "receiver_title": state["receiver_details"]["job_title"],
                "company": state["job_information"]["company"],
                "sender_name": state["sender_details"]["name"],
                "sender_email": state["sender_details"]["email"],
                "job_title": state["job_information"]["job_title"],
                "tone": state["tone"],
                "sender_skills": json.dumps(state["contextual_data"]["sender_skills"], indent=2),
                "sender_experience": json.dumps(state["contextual_data"]["sender_experience"][:2], indent=2),
                "job_requirements": state["contextual_data"]["job_requirements"],
                "job_preferred": state["contextual_data"]["job_preferred"]
            })

            state["generated_email"] = response.content
            return state

        except Exception as e:
            state["error"] = f"Personalized email generation error: {str(e)}"
            return state

    async def _generate_contextual_email(self, state: EmailState) -> EmailState:
        """Generate a highly contextual email using external data"""
        try:
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content="""You are an expert at writing highly contextual cold emails for job referrals.
                Create an email that incorporates recent company news, GitHub activity, or LinkedIn information to make it highly personalized and relevant.
                Use specific contextual hooks to show genuine interest and research."""),
                MessagesPlaceholder(variable_name="context"),
                HumanMessage(content="""Generate a highly contextual cold email with the following details:
                
                Receiver: {receiver_name} ({receiver_title} at {company})
                Sender: {sender_name} ({sender_email})
                Job: {job_title} at {company}
                Tone: {tone}
                
                Contextual Data:
                GitHub: {github_data}
                Company News: {company_news}
                LinkedIn: {linkedin_data}
                
                Requirements:
                - Reference specific recent company news or events
                - Mention relevant GitHub projects or contributions
                - Include LinkedIn insights if available
                - Show genuine research and interest
                - Keep it under 250 words
                - Use the specified tone
                - Include a clear call to action""")
            ])

            context = self._build_context_message(state)

            chain = prompt | self.model
            response = await chain.ainvoke({
                "context": context,
                "receiver_name": state["receiver_details"]["name"],
                "receiver_title": state["receiver_details"]["job_title"],
                "company": state["job_information"]["company"],
                "sender_name": state["sender_details"]["name"],
                "sender_email": state["sender_details"]["email"],
                "job_title": state["job_information"]["job_title"],
                "tone": state["tone"],
                "github_data": json.dumps(state["contextual_data"]["github_data"], indent=2),
                "company_news": json.dumps(state["contextual_data"]["company_news"], indent=2),
                "linkedin_data": json.dumps(state["contextual_data"]["linkedin_data"], indent=2)
            })

            state["generated_email"] = response.content
            return state

        except Exception as e:
            state["error"] = f"Contextual email generation error: {str(e)}"
            return state

    def _build_context_message(self, state: EmailState) -> List[SystemMessage]:
        """Build context message for the LLM"""
        context = f"""
        Job Information:
        - Title: {state['job_information'].get('job_title', 'N/A')}
        - Company: {state['job_information'].get('company', 'N/A')}
        - Location: {state['job_information'].get('location', 'N/A')}
        - Department: {state['job_information'].get('department', 'N/A')}
        - Experience Level: {state['job_information'].get('experience_level', 'N/A')}
        
        Sender Information:
        - Name: {state['sender_details'].get('name', 'N/A')}
        - Email: {state['sender_details'].get('email', 'N/A')}
        - Phone: {state['sender_details'].get('phone', 'N/A')}
        - Key Accomplishments: {state['sender_details'].get('key_accomplishments', 'N/A')}
        """

        return [SystemMessage(content=context)]

    async def _finalize_email(self, state: EmailState) -> EmailState:
        """Finalize the email with subject line and formatting"""
        try:
            if state.get("error"):
                return state

            # Generate subject line
            subject_prompt = ChatPromptTemplate.from_messages([
                SystemMessage(
                    content="Generate a compelling subject line for a cold email job referral."),
                HumanMessage(content="""Generate a subject line for this email:
                
                Job: {job_title} at {company}
                Sender: {sender_name}
                Tone: {tone}
                
                Requirements:
                - Keep it under 60 characters
                - Be professional and compelling
                - Avoid spam trigger words""")
            ])

            chain = subject_prompt | self.model
            subject_response = await chain.ainvoke({
                "job_title": state["job_information"]["job_title"],
                "company": state["job_information"]["company"],
                "sender_name": state["sender_details"]["name"],
                "tone": state["tone"]
            })

            state["email_subject"] = subject_response.content.strip()

            return state

        except Exception as e:
            state["error"] = f"Email finalization error: {str(e)}"
            return state

    async def generate_email(self,
                             receiver_details: Dict[str, Any],
                             sender_details: Dict[str, Any],
                             job_information: Dict[str, Any],
                             email_type: EmailType = EmailType.SIMPLE,
                             tone: Tone = Tone.FRIENDLY) -> Dict[str, Any]:
        """Generate a personalized cold email"""

        initial_state = EmailState(
            receiver_details=receiver_details,
            sender_details=sender_details,
            job_information=job_information,
            email_type=email_type,
            tone=tone,
            contextual_data={},
            generated_email=None,
            email_subject=None,
            error=None
        )

        try:
            result = await self.workflow.ainvoke(initial_state)
            return {
                "success": result.get("error") is None,
                "email_subject": result.get("email_subject"),
                "email_body": result.get("generated_email"),
                "email_type": result.get("email_type"),
                "tone": result.get("tone"),
                "error": result.get("error")
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Workflow execution error: {str(e)}"
            }


# Example usage and testing functions
async def test_email_generation():
    """Test the email generation with sample data"""

    # Load sample data
    with open("data/sample_ip_email_gen_mle.json", "r") as f:
        mle_data = json.load(f)

    with open("data/sample_ip_email_gen_swe.json", "r") as f:
        swe_data = json.load(f)

    generator = EmailGenerator()

    # Test simple email
    print("=== Testing Simple Email ===")
    result = await generator.generate_email(
        receiver_details=mle_data["receiver_details"],
        sender_details=mle_data["sender_details"],
        job_information=mle_data["job_information"],
        email_type=EmailType.SIMPLE,
        tone=Tone.FRIENDLY
    )

    if result["success"]:
        print(f"Subject: {result['email_subject']}")
        print(f"Body: {result['email_body']}")
    else:
        print(f"Error: {result['error']}")

    print("\n" + "="*50 + "\n")

    # Test personalized email
    print("=== Testing Personalized Email ===")
    result = await generator.generate_email(
        receiver_details=swe_data["receiver_details"],
        sender_details=swe_data["sender_details"],
        job_information=swe_data["job_information"],
        email_type=EmailType.PERSONALIZED,
        tone=Tone.ENTHUSIASTIC
    )

    if result["success"]:
        print(f"Subject: {result['email_subject']}")
        print(f"Body: {result['email_body']}")
    else:
        print(f"Error: {result['error']}")

    print("\n" + "="*50 + "\n")

    # Test contextual email
    print("=== Testing Contextual Email ===")
    result = await generator.generate_email(
        receiver_details=mle_data["receiver_details"],
        sender_details=mle_data["sender_details"],
        job_information=mle_data["job_information"],
        email_type=EmailType.CONTEXTUAL,
        tone=Tone.FORMAL
    )

    if result["success"]:
        print(f"Subject: {result['email_subject']}")
        print(f"Body: {result['email_body']}")
    else:
        print(f"Error: {result['error']}")


if __name__ == "__main__":
    asyncio.run(test_email_generation())
