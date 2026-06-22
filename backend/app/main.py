import json
import asyncio
import logging
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.config import settings
from app.agents.coordinator import run_coordinator_flow
from app.agents.types import FinalPortfolioReviewReport

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Multi-agent portfolio evaluation backend using Google ADK & Gemini"
)

# Set up CORS middleware to allow calls from Next.js (port 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ReviewRequest(BaseModel):
    github_url: str

@app.get("/")
def read_root():
    return {"message": f"Welcome to the {settings.PROJECT_NAME} Backend API!"}

@app.post("/api/review")
async def review_portfolio(request: ReviewRequest):
    """
    Synchronous endpoint that runs the entire multi-agent flow
    and returns the final synthesized review.
    """
    logger.info(f"Received review request for: {request.github_url}")
    
    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY environment variable is missing on the server. Please set it."
        )
        
    last_event = None
    try:
        async for event in run_coordinator_flow(request.github_url):
            last_event = event
            if event["status"] == "failed":
                raise HTTPException(status_code=500, detail=event["message"])
                
        if last_event and last_event["status"] == "completed":
            return last_event["result"]
        else:
            raise HTTPException(status_code=500, detail="Flow completed without returning a result.")
            
    except Exception as e:
        logger.error(f"Error in review_portfolio: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/review/stream")
async def review_portfolio_stream(github_url: str = Query(..., description="The GitHub profile URL to review")):
    """
    Server-Sent Events (SSE) streaming endpoint.
    Streams progress states (scraping, analyzing, resume bullets, career roadmap)
    and ends with the final serialized report.
    """
    logger.info(f"Received streaming review request for: {github_url}")
    
    if not settings.GEMINI_API_KEY:
        async def error_generator():
            yield f"data: {json.dumps({'status': 'failed', 'message': 'GEMINI_API_KEY environment variable is missing on the server.'})}\n\n"
        return StreamingResponse(error_generator(), media_type="text/event-stream")

    async def event_generator():
        try:
            async for event in run_coordinator_flow(github_url):
                # Format as Server-Sent Event data
                yield f"data: {json.dumps(event)}\n\n"
                # Small pause to prevent overloading network buffer and ensure smooth UI updates
                await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Error in event_generator: {e}")
            yield f"data: {json.dumps({'status': 'failed', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "X-Accel-Buffering": "no"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
