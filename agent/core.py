import asyncio
from agent.sandbox import clone_repo_in_sandbox, log_sandbox_metrics

async def run_agent_flow(repo_url: str, prompt: str):
    yield "🔄 Cloning repository..."
    try:
        sandbox = clone_repo_in_sandbox(repo_url)
        yield "✅ Repo cloned into sandbox"
    except Exception as e:
        yield f"❌ Failed to clone repo: {str(e)}"
        return
    yield "🌿 Creating branch..."
    await asyncio.sleep(1)
    yield "🧠 Generating plan..."
    await asyncio.sleep(1)
    yield f"✅ PR ready for: {prompt}"