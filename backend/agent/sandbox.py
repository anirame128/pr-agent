import os
from e2b_code_interpreter import Sandbox
from dotenv import load_dotenv

load_dotenv()

def clone_repo_in_sandbox(repo_url: str) -> Sandbox:
    
    print("🔐 Launching E2B Sandbox...")
    
    # Create sandbox using context manager for automatic cleanup
    sandbox = Sandbox()
    
    print(f"📁 Cloning repo into /workspace: {repo_url}")
    
    # First, create the workspace directory
    sandbox.run_code("import os; os.makedirs('/workspace', exist_ok=True)")
    
    # Clone the repository using git command
    execution = sandbox.run_code(f"import subprocess; result = subprocess.run(['git', 'clone', '{repo_url}', '/workspace'], capture_output=True, text=True); print('STDOUT:', result.stdout); print('STDERR:', result.stderr); print('Return code:', result.returncode)")
    
    # Check execution results
    if execution.error:
        print(f"❌ Execution error: {execution.error}")
        sandbox.close()
        raise RuntimeError(f"Git clone failed with execution error: {execution.error}")
    
    # Get the output from logs
    output = ""
    if execution.logs and execution.logs.stdout:
        output = "\n".join(execution.logs.stdout)
    elif execution.text:
        output = execution.text
    
    print("✅ Clone output:", output)
    
    # Check if clone was successful by looking for error indicators
    if "fatal" in output.lower() or "error" in output.lower():
        sandbox.close()
        raise RuntimeError(f"Git clone failed: {output}")
    
    # Verify the clone by listing the workspace directory
    verification = sandbox.run_code("import os; print('Contents of /workspace:'); print(os.listdir('/workspace') if os.path.exists('/workspace') else 'Directory not found')")
    
    if verification.logs and verification.logs.stdout:
        verification_output = "\n".join(verification.logs.stdout)
        print("📋 Workspace contents:", verification_output)
    
    return sandbox
