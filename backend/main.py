from fastapi import FastAPI, Request
from sse_starlette.sse import EventSourceResponse
import asyncio
from agent.core import run_agent_flow

app = FastAPI()

@app.post("/code")
async def code(request: Request):
    body = await request.json()
    repo_url = body["repoUrl"]
    prompt = body["prompt"]

    async def event_generator():
        async for event in run_agent_flow(repo_url, prompt):
            yield {"event": "update", "data": event}
    
    return EventSourceResponse(event_generator())