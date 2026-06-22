import json
import logging
from typing import Dict, Any
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from app.agents.types import ResumeImprovementsOutput
from app.config import settings

logger = logging.getLogger("resume_agent")

RESUME_AGENT_INSTRUCTION = """
You are an expert technical resume writer and career coach.
Your task is to review the candidate's GitHub portfolio analysis and generate professional resume enhancements.

Specifically, you must:
1. Provide general resume improvements (tips on formatting, technical vocabulary, profiling languages and tools). Keep these suggestions concise and to the point (no more than 1-2 sentences each).
2. Generate 3-4 high-impact, ATS-ready project bullet points for their main repositories.
3. Formulate the bullet points using the STAR method: Situation, Task, Action, Result. Highlight the technical implementation details, scale, optimization, or business impact. Keep these bullets focused, precise, and not too long.

Your output MUST conform exactly to the response schema. Focus on professional, high-impact phrasing. Do not use raw markdown formats like list items or stars inside the JSON string arrays themselves.
"""

def create_resume_agent() -> Agent:
    return Agent(
        name="resume_agent",
        model=settings.GEMINI_MODEL,
        instruction=RESUME_AGENT_INSTRUCTION,
        output_schema=ResumeImprovementsOutput
    )

async def run_resume_agent(github_analysis_json: str) -> ResumeImprovementsOutput:
    """
    Runs the Resume Agent using the findings from the GitHub analysis.
    """
    logger.info("Running Resume Agent...")
    agent = create_resume_agent()
    runner = InMemoryRunner(agent=agent)
    runner.auto_create_session = True
    
    from google.genai import types
    
    prompt = f"Analyze the following GitHub evaluation findings and generate resume suggestions:\n{github_analysis_json}"
    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=prompt)]
    )
    
    raw_text = ""
    async for event in runner.run_async(
        user_id="system",
        session_id="resume_analysis_session",
        new_message=content
    ):
        if event.content and event.content.parts:
            if event.author != "user" and not event.partial:
                for part in event.content.parts:
                    if part.text:
                        raw_text = part.text
                        
    logger.info(f"Resume agent raw text length: {len(raw_text)}")
    
    cleaned_json = raw_text.strip()
    if cleaned_json.startswith("```"):
        cleaned_json = cleaned_json.split("\n", 1)[1]
    if cleaned_json.endswith("```"):
        cleaned_json = cleaned_json.rsplit("\n", 1)[0]
    cleaned_json = cleaned_json.strip()
    
    try:
        data = json.loads(cleaned_json)
        return ResumeImprovementsOutput(**data)
    except Exception as e:
        logger.error(f"Error parsing Resume agent response JSON: {e}. Raw: {raw_text}")
        return ResumeImprovementsOutput(
            general_improvements=["Use action verbs and quantify achievements"],
            ats_bullets=[]
        )
