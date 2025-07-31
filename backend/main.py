import os
from fastapi import FastAPI, Request
from sse_starlette.sse import EventSourceResponse
import asyncio
from agent.agent_flow import run_agent_flow
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

@app.post("/code")
async def code(request: Request):
    body = await request.json()
    repo_url = body["repoUrl"]
    prompt = body["prompt"]
    enable_modifications = body.get("enable_modifications", False)
    # Get GitHub token from environment variables instead of request body
    github_token = os.getenv("GITHUB_TOKEN")

    async def event_generator():
        async for event in run_agent_flow(repo_url, prompt, enable_modifications=enable_modifications, github_token=github_token):      
            yield {"event": "update", "data": event}
    
    return EventSourceResponse(event_generator())
    