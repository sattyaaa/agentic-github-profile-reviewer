import asyncio
import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.agents.coordinator import run_coordinator_flow

async def verify():
    print("==================================================")
    print("Verifying Backend Agent Workflow...")
    print("==================================================")
    
    github_url = "https://github.com/octocat"
    print(f"Submitting test profile: {github_url}\n")
    
    count = 0
    final_result = None
    
    async for event in run_coordinator_flow(github_url):
        status = event.get("status")
        message = event.get("message")
        print(f"Step [{status.upper()}]: {message}")
        count += 1
        if status == "completed":
            final_result = event.get("result")
            
    print("\n--------------------------------------------------")
    print(f"Workflow finished after {count} events.")
    
    if final_result:
        print("SUCCESS: Received a valid FinalPortfolioReviewReport!")
        print(f"Username: {final_result.get('username')}")
        print(f"Score: {final_result.get('github_analysis', {}).get('portfolio_score')}")
        print(f"Summary preview: {final_result.get('summary')[:100]}...")
        return True
    else:
        print("ERROR: Workflow did not yield a completed status event or final result.")
        return False

if __name__ == "__main__":
    success = asyncio.run(verify())
    sys.exit(0 if success else 1)
