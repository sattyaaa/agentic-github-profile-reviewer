import json
import logging
from typing import Dict, Any
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from app.agents.types import GitHubAnalysisOutput
from app.config import settings

logger = logging.getLogger("github_agent")

GITHUB_AGENT_INSTRUCTION = """
You are a senior technical interviewer and portfolio evaluator. 
Your goal is to perform a deep analysis of a candidate's GitHub profile and repositories.

Given the JSON payload containing the user's profile and repositories (including READMEs and commits for the top repositories), you must:
1. Identify their primary tech stack (languages, frameworks, libraries).
2. Evaluate their repositories one by one, rating project quality (0 to 100) based on complexity, architecture, README clarity, and commits. The review_comments for each repository MUST be concise and to the point (at most 2-3 sentences).
3. Determine their core portfolio score (0 to 100).
4. Highlight major strengths (clean code, use of modern frameworks, tests, well-written READMEs, consistent commits).
5. Highlight weaknesses (poor documentation, empty repos, lack of complexity, lack of testing).

Your output MUST conform exactly to the response schema. Keep comments constructive, professional, and technical.
"""

def create_github_agent() -> Agent:
    return Agent(
        name="github_analysis_agent",
        model=settings.GEMINI_MODEL,
        instruction=GITHUB_AGENT_INSTRUCTION,
        output_schema=GitHubAnalysisOutput
    )

async def run_github_agent(github_data: Dict[str, Any]) -> GitHubAnalysisOutput:
    """
    Runs the GitHub Analysis Agent to evaluate the candidate's portfolio.
    """
    logger.info("Running GitHub Analysis Agent...")
    agent = create_github_agent()
    runner = InMemoryRunner(agent=agent)
    runner.auto_create_session = True
    
    from google.genai import types
    
    # We serialize the github_data to JSON to feed it to the agent
    prompt = f"Analyze the following GitHub data:\n{json.dumps(github_data, indent=2)}"
    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=prompt)]
    )
    
    raw_text = ""
    async for event in runner.run_async(
        user_id="system",
        session_id="github_analysis_session",
        new_message=content
    ):
        if event.content and event.content.parts:
            if event.author != "user" and not event.partial:
                for part in event.content.parts:
                    if part.text:
                        raw_text = part.text
                        
    logger.info(f"GitHub agent raw text length: {len(raw_text)}")
    
    # Clean markdown code block wraps if present (e.g. ```json ... ```)
    cleaned_json = raw_text.strip()
    if cleaned_json.startswith("```"):
        cleaned_json = cleaned_json.split("\n", 1)[1]
    if cleaned_json.endswith("```"):
        cleaned_json = cleaned_json.rsplit("\n", 1)[0]
    cleaned_json = cleaned_json.strip()
    
    try:
        data = json.loads(cleaned_json)
        return GitHubAnalysisOutput(**data)
    except Exception as e:
        logger.error(f"Error parsing GitHub agent response JSON: {e}. Raw: {raw_text}")
        # Return fallback output to make it resilient
        return GitHubAnalysisOutput(
            portfolio_score=50,
            strengths=["Determined and active developer"],
            weaknesses=["Unable to extract detailed review due to JSON parsing error"],
            repository_reviews=[],
            primary_tech_stack=[]
        )
