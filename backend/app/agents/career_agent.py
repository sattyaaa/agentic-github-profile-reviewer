import json
import logging
from typing import Dict, Any
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from app.agents.types import CareerAnalysisOutput

logger = logging.getLogger("career_agent")

CAREER_AGENT_INSTRUCTION = """
You are an experienced career counselor and engineering manager.
Your task is to review the candidate's GitHub portfolio analysis and generate professional career guidance.

Specifically, you must:
1. Identify skill gaps: what technologies, libraries, tools, or theoretical topics (like system design, database indexing, caching, testing, CI/CD) are missing from their current profile based on modern industry standards?
2. Design a personalized learning roadmap with 3-5 sequential, structured steps/phases to close their gaps. Keep the topic and skills concise.
3. Recommend 2-3 specific projects to build to bridge those gaps and list the exact stack they should use. Keep descriptions short and focused.
4. Estimate their career role fit percentage (0-100) and reasoning for the following roles:
   - Backend Engineer
   - Frontend Engineer
   - Full Stack Engineer
   - AI/ML Engineer
   - DevOps Engineer
   Use their repo counts, languages, and complex patterns as indicator inputs. Keep reasoning concise (at most 2 sentences).

Your output MUST conform exactly to the response schema. Keep suggestions highly specific, actionable, modern, and concise (not too short, not too long).
"""

def create_career_agent() -> Agent:
    return Agent(
        name="career_agent",
        model="gemini-2.5-flash",
        instruction=CAREER_AGENT_INSTRUCTION,
        output_schema=CareerAnalysisOutput
    )

async def run_career_agent(github_analysis_json: str) -> CareerAnalysisOutput:
    """
    Runs the Career Agent using the findings from the GitHub analysis.
    """
    logger.info("Running Career Agent...")
    agent = create_career_agent()
    runner = InMemoryRunner(agent=agent)
    runner.auto_create_session = True
    
    from google.genai import types
    
    prompt = f"Analyze the following GitHub evaluation findings and generate career roadmap suggestions:\n{github_analysis_json}"
    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=prompt)]
    )
    
    raw_text = ""
    async for event in runner.run_async(
        user_id="system",
        session_id="career_analysis_session",
        new_message=content
    ):
        if event.content and event.content.parts:
            if event.author != "user" and not event.partial:
                for part in event.content.parts:
                    if part.text:
                        raw_text = part.text
                        
    logger.info(f"Career agent raw text length: {len(raw_text)}")
    
    cleaned_json = raw_text.strip()
    if cleaned_json.startswith("```"):
        cleaned_json = cleaned_json.split("\n", 1)[1]
    if cleaned_json.endswith("```"):
        cleaned_json = cleaned_json.rsplit("\n", 1)[0]
    cleaned_json = cleaned_json.strip()
    
    try:
        data = json.loads(cleaned_json)
        return CareerAnalysisOutput(**data)
    except Exception as e:
        logger.error(f"Error parsing Career agent response JSON: {e}. Raw: {raw_text}")
        return CareerAnalysisOutput(
            skills_gap=["Database indexing", "System design"],
            roadmap=[],
            recommended_projects=[],
            role_fits=[]
        )
