import json
import logging
import asyncio
from typing import Dict, Any, AsyncGenerator
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner

from app.config import settings
from app.services.github_service import github_service
from app.agents.github_agent import run_github_agent
from app.agents.resume_agent import run_resume_agent
from app.agents.career_agent import run_career_agent
from app.agents.types import (
    FinalPortfolioReviewReport, 
    GitHubAnalysisOutput, 
    RepositoryReview, 
    ResumeImprovementsOutput, 
    ProjectBullet, 
    CareerAnalysisOutput, 
    RoadmapStep, 
    RecommendedProject, 
    RoleFit
)

logger = logging.getLogger("coordinator")

COORDINATOR_INSTRUCTION = """
You are the Lead Coordinator Agent of the GitHub Portfolio Reviewer system.
Your job is to read:
1. The GitHub user's profile metadata.
2. The GitHub Analysis Agent report.
3. The Resume Agent report.
4. The Career Agent report.

You must synthesize a highly professional, encouraging, and actionable executive summary.
This summary MUST be a concise, bulleted list of AT MOST 5 key points summarizing the developer's profile, strengths, biggest skill gaps, and next career actions.
Keep the points detailed but clear and direct (not too short, not too long). Avoid generic fluff. Do not use JSON formatting.
Format each bullet point as a markdown item starting with a dash (e.g. '- point 1').
"""

def create_coordinator_agent() -> Agent:
    return Agent(
        name="coordinator_agent",
        model=settings.GEMINI_MODEL,
        instruction=COORDINATOR_INSTRUCTION
    )

def is_api_key_mock() -> bool:
    key = settings.GEMINI_API_KEY.strip()
    return not key or key.startswith("YOUR_") or key == "mock-key"

async def run_mock_flow(github_url: str) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Simulates the agentic workflow with high-fidelity mock data.
    Allows end-to-end frontend/backend testing without a Gemini key.
    """
    username = github_service.extract_username(github_url)
    logger.info(f"Running MOCK portfolio review flow for: {username}")
    
    # 1. Scrape GitHub
    yield {
        "status": "scraping_github",
        "message": "[MOCK MODE] Scraping profile details, repository languages, and readme headers from GitHub..."
    }
    await asyncio.sleep(1.5)
    
    # 2. GitHub Analysis Agent
    yield {
        "status": "analyzing_repos",
        "message": "[MOCK MODE] GitHub Analysis Agent evaluating project complexity, commit velocity, and styling quality..."
    }
    await asyncio.sleep(1.5)
    
    # 3. Resume Agent
    yield {
        "status": "writing_resume",
        "message": "[MOCK MODE] Resume Agent generating professional ATS-ready project resume bullets..."
    }
    await asyncio.sleep(1.5)
    
    # 4. Career Agent
    yield {
        "status": "planning_career",
        "message": "[MOCK MODE] Career Agent identifying skill gaps, constructing timeline roadmaps, and matching job roles..."
    }
    await asyncio.sleep(1.5)
    
    # 5. Coordinator Synthesis
    yield {
        "status": "synthesizing",
        "message": "[MOCK MODE] Coordinator Agent synthesizing final review summary..."
    }
    await asyncio.sleep(1.0)
    
    # Generate high quality mock data matching types.py
    mock_report = FinalPortfolioReviewReport(
        username=username,
        name=f"Jane Developer ({username})",
        bio="Full Stack Developer passionate about responsive UI, TypeScript, and robust API design.",
        followers=128,
        avatar_url=f"https://github.com/{username}.png",
        github_url=f"https://github.com/{username}",
        
        github_analysis=GitHubAnalysisOutput(
            portfolio_score=85,
            strengths=[
                "Excellent repository structure with logical file grouping",
                "Detailed README files containing clear installation commands and setup instructions",
                "Strong use of modern TypeScript, React, and Tailwind CSS for layouts",
                "Consistent commit history with descriptive git logs"
            ],
            weaknesses=[
                "Lack of automated unit or integration tests across primary repos",
                "Few Dockerfiles or containerization configurations for backend deployments",
                "Several repositories have outdated dependency branches"
            ],
            repository_reviews=[
                RepositoryReview(
                    name="e-commerce-dashboard",
                    quality_score=90,
                    key_technologies=["Next.js", "TypeScript", "Tailwind CSS", "Prisma", "PostgreSQL"],
                    review_comments="Highly functional frontend dashboard with responsive tables, state management (Zustand), and interactive dark mode. Database relationships are well-modeled, but could benefit from indexes on search columns.",
                    documentation_rating="Excellent"
                ),
                RepositoryReview(
                    name="task-scheduler-api",
                    quality_score=80,
                    key_technologies=["FastAPI", "Python", "Redis", "Celery", "Docker"],
                    review_comments="Good application of async workers for background jobs. Clean separation of routers and database queries. Needs a unit test suite to cover the Celery task edge cases.",
                    documentation_rating="Good"
                ),
                RepositoryReview(
                    name="personal-portfolio-v2",
                    quality_score=85,
                    key_technologies=["React", "Vite", "Framer Motion", "Tailwind CSS"],
                    review_comments="Visually stunning landing page with smooth page-scroll animations. Asset files are structured neatly, though image bundle sizes could be optimized using Next.js Image or WebP compression.",
                    documentation_rating="Fair"
                )
            ],
            primary_tech_stack=["TypeScript", "React", "Python", "FastAPI", "PostgreSQL"]
        ),
        
        resume_improvements=ResumeImprovementsOutput(
            general_improvements=[
                "Create a dedicated 'Projects' section using a consistent reverse-chronological order.",
                "Explicitly detail your usage of Celery and Redis in your Experience bullet points to showcase background job processing skills.",
                "Ensure all technologies listed in your Skills section are backed by at least one codebase project in the portfolio."
            ],
            ats_bullets=[
                ProjectBullet(
                    repo_name="e-commerce-dashboard",
                    bullets=[
                        "Architected an administrative e-commerce dashboard using Next.js and Prisma, improving page-load performance by 35% through dynamic server-side rendering.",
                        "Integrated a robust multi-column database schema in PostgreSQL, reducing complex transaction search query latency by 200ms.",
                        "Designed responsive UI layouts using Tailwind CSS and managed global state using Zustand, reducing boilerplate code by 40%."
                    ]
                ),
                ProjectBullet(
                    repo_name="task-scheduler-api",
                    bullets=[
                        "Developed an asynchronous job queue using FastAPI, Redis, and Celery, successfully processing over 10k background tasks daily.",
                        "Configured Docker containers for PostgreSQL, Redis, and the FastAPI application, shortening local environment deployment times to a single command.",
                        "Separated task routing logics and created clean repository patterns in Python, lowering backend codebase maintenance costs."
                    ]
                )
            ]
        ),
        
        career_analysis=CareerAnalysisOutput(
            skills_gap=[
                "Automated testing frameworks (Jest, pytest)",
                "CI/CD deployment pipelines (GitHub Actions, Docker Compose)",
                "System design patterns (Horizontal Scaling, Caching strategies with Redis at scale)"
            ],
            roadmap=[
                RoadmapStep(
                    step_number=1,
                    topic="Automated Testing",
                    skills_to_acquire=["pytest for FastAPI endpoints", "React Testing Library for dashboard elements"],
                    recommended_resources=["pytest official documentation", "React Testing Library official guides"],
                    estimated_time="2 weeks"
                ),
                RoadmapStep(
                    step_number=2,
                    topic="CI/CD and DevOps Pipelines",
                    skills_to_acquire=["GitHub Actions yaml workflows", "Docker Compose configuration for multi-service local stacks"],
                    recommended_resources=["GitHub Actions Codelabs", "Docker official tutorials"],
                    estimated_time="3 weeks"
                ),
                RoadmapStep(
                    step_number=3,
                    topic="System Design at Scale",
                    skills_to_acquire=["Redis caching decorators", "Database indexing and execution plan analysis (EXPLAIN)"],
                    recommended_resources=["Designing Data-Intensive Applications (Book)", "System Design Primer GitHub repository"],
                    estimated_time="4 weeks"
                )
            ],
            recommended_projects=[
                RecommendedProject(
                    title="Real-Time Analytics Platform",
                    description="Build a high-throughput endpoint using FastAPI and WebSockets that ingests page clicks, queues them via Redis, saves aggregated logs into PostgreSQL, and showcases real-time updates in a Next.js graph dashboard.",
                    suggested_tech_stack=["FastAPI", "WebSockets", "Redis", "Next.js", "Chart.js"],
                    difficulty="Advanced"
                ),
                RecommendedProject(
                    title="DevOps Pipeline Boilerplate",
                    description="Construct a template repository with a full Next.js/FastAPI stack pre-configured with ESLint, Ruff, pytest, GitHub Actions (automated test runner), and multi-stage Dockerfiles.",
                    suggested_tech_stack=["Docker", "GitHub Actions", "pytest", "TypeScript"],
                    difficulty="Intermediate"
                )
            ],
            role_fits=[
                RoleFit(
                    role_name="Full Stack Engineer",
                    match_percentage=90,
                    reasoning="Strong React layouts combined with functional FastAPI routes. Standardize testing patterns to reach senior level."
                ),
                RoleFit(
                    role_name="Backend Engineer",
                    match_percentage=80,
                    reasoning="Competent with Python, FastAPI, and Redis. Needs more experience with database tuning and pipeline tooling."
                ),
                RoleFit(
                    role_name="DevOps Engineer",
                    match_percentage=45,
                    reasoning="Understands basic Docker configs, but lacks deep experience with K8s, Terraform, or complex cloud monitoring configurations."
                ),
                RoleFit(
                    role_name="AI/ML Engineer",
                    match_percentage=30,
                    reasoning="No machine learning repositories, training scripts, or AI libraries detected. Strongly focused on software engineering."
                )
            ]
        ),
        
        summary="- Jane Developer shows strong full-stack capabilities with clean React/TypeScript frontends and Python/FastAPI backends.\n- Key strength is in project structure and detailed setup documentations across primary repositories.\n- Primary skill gaps include automated unit/integration testing (pytest, Jest) and CI/CD pipelines.\n- Recommended next step is to build a DevOps pipeline boilerplate and implement caching decorators at scale.\n- Following the roadmap will prepare her for competitive senior Full Stack and Backend engineering roles."
    )
    
    yield {
        "status": "completed",
        "message": "[MOCK MODE] Synthesized final review report successfully.",
        "result": mock_report.model_dump()
    }

async def run_coordinator_flow(github_url: str) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Coordinates the multi-agent execution flow.
    Yields progressive JSON statuses to stream logs to the client,
    and yields the final report object as the last item.
    """
    # If API key is mock, run the mock simulator instead
    if is_api_key_mock():
        async for event in run_mock_flow(github_url):
            yield event
        return

    try:
        # Step 1: Scrape GitHub
        yield {
            "status": "scraping_github",
            "message": "Connecting to GitHub API and downloading repository metadata, READMEs, and commit histories..."
        }
        github_data = await github_service.fetch_portfolio_data(github_url)
        logger.info(f"Successfully scraped GitHub data for {github_data['username']}")
        
        # Step 2: GitHub Analysis Agent
        yield {
            "status": "analyzing_repos",
            "message": "GitHub Analysis Agent: Assessing repository architectures, documentation quality, and calculating portfolio scores..."
        }
        github_analysis = await run_github_agent(github_data)
        logger.info("Successfully executed GitHub Analysis Agent.")
        
        # Step 3: Resume Agent
        yield {
            "status": "writing_resume",
            "message": "Resume Agent: Formulating general resume enhancements and crafting STAR-method project bullet points..."
        }
        # Serialize the analysis to send it to downstream agents
        github_analysis_json = github_analysis.model_dump_json(indent=2)
        resume_improvements = await run_resume_agent(github_analysis_json)
        logger.info("Successfully executed Resume Agent.")
        
        # Step 4: Career Agent
        yield {
            "status": "planning_career",
            "message": "Career Agent: Conducting skill-gap analysis, mapping out learning roadmaps, and checking role fit compatibility..."
        }
        career_analysis = await run_career_agent(github_analysis_json)
        logger.info("Successfully executed Career Agent.")
        
        # Step 5: Synthesis
        yield {
            "status": "synthesizing",
            "message": "Coordinator Agent: Reviewing all agent evaluations to synthesize the final executive report..."
        }
        
        coordinator_agent = create_coordinator_agent()
        runner = InMemoryRunner(agent=coordinator_agent)
        runner.auto_create_session = True
        
        from google.genai import types
        
        synthesis_prompt = f"""
        User Profile:
        Username: {github_data.get('username')}
        Bio: {github_data.get('bio')}
        Followers: {github_data.get('followers')}
        
        GitHub Analysis Report:
        {github_analysis.model_dump_json(indent=2)}
        
        Resume Improvements:
        {resume_improvements.model_dump_json(indent=2)}
        
        Career Analysis:
        {career_analysis.model_dump_json(indent=2)}
        """
        content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=synthesis_prompt)]
        )
        
        summary_text = ""
        async for event in runner.run_async(
            user_id="system",
            session_id="coordinator_synthesis_session",
            new_message=content
        ):
            if event.content and event.content.parts:
                if event.author != "user" and not event.partial:
                    for part in event.content.parts:
                        if part.text:
                            summary_text = part.text
                            
        logger.info("Successfully synthesized final report.")
        
        # Compile final report
        final_report = FinalPortfolioReviewReport(
            username=github_data.get("username", ""),
            name=github_data.get("name") or github_data.get("username", ""),
            bio=github_data.get("bio") or "",
            followers=github_data.get("followers", 0),
            avatar_url=github_data.get("avatar_url") or "",
            github_url=github_data.get("html_url") or github_url,
            github_analysis=github_analysis,
            resume_improvements=resume_improvements,
            career_analysis=career_analysis,
            summary=summary_text.strip()
        )
        
        yield {
            "status": "completed",
            "message": "Synthesized final review report successfully.",
            "result": final_report.model_dump()
        }
        
    except Exception as e:
        err_msg = str(e)
        if "API key not valid" in err_msg or "API_KEY_INVALID" in err_msg or "INVALID_ARGUMENT" in err_msg or "ClientError" in err_msg:
            logger.warning(f"Live Gemini API Key invalid ({err_msg}). Falling back to Mock Mode...")
            yield {
                "status": "scraping_github",
                "message": "[FALLBACK] Live Gemini API Key invalid. Automatically running mock evaluation..."
            }
            await asyncio.sleep(2.0)
            async for event in run_mock_flow(github_url):
                yield event
            return
            
        logger.error(f"Error in Coordinator flow: {e}", exc_info=True)
        yield {
            "status": "failed",
            "message": f"Orchestration failed: {str(e)}"
        }
