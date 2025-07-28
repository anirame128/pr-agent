import os
from e2b_code_interpreter import Sandbox
from dotenv import load_dotenv

load_dotenv()
E2B_API_KEY = os.getenv("E2B_API_KEY")

def clone_repo_in_sandbox(repo_url: str) -> Sandbox:
    print("🔐 Launching E2B Sandbox...")
    sandbox = Sandbox(api_key=E2B_API_KEY)
    print(f"📁 Cloning repo into /workspace: {repo_url}")
    execution = sandbox.run_code(f"git clone {repo_url} /workspace")
    if execution.text or execution.logs.stdout:
        # optional log the output
        print("✅ Clone output:", execution.text or execution.logs.stdout)
    return sandbox
