import os
from e2b_code_interpreter import Sandbox
from dotenv import load_dotenv
from typing import Dict

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

def read_codebase(sandbox: Sandbox) -> Dict[str, str]:
    print("🧾 Scanning codebase...")
    
    # First, let's see what's actually in the workspace
    check_contents_code = """
import os
print("=== Workspace structure ===")
for root, dirs, files in os.walk("/workspace"):
    level = root.replace("/workspace", "").count(os.sep)
    indent = " " * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = " " * 2 * (level + 1)
    for file in files:
        print(f"{subindent}{file}")
"""
    
    execution = sandbox.run_code(check_contents_code)
    if execution.logs and execution.logs.stdout:
        structure_output = "\n".join(execution.logs.stdout)
        print("📁 Repository structure:")
        print(structure_output)
    
    # List all files in the codebase with broader file extensions
    list_files_code = """
import os

# Common code file extensions
code_extensions = (
    '.ts', '.tsx', '.js', '.jsx', '.py', '.java', '.cpp', '.c', '.h', 
    '.cs', '.go', '.rs', '.php', '.rb', '.swift', '.kt', '.dart',
    '.html', '.htm', '.css', '.scss', '.sass', '.less', '.vue',
    '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg',
    '.md', '.txt', '.sh', '.bash', '.zsh', '.fish', '.ps1',
    '.sql', '.r', '.m', '.scala', '.clj', '.hs', '.ml', '.fs',
    '.dockerfile', '.gitignore', '.gitattributes', '.editorconfig'
)

# Common documentation files without extensions
doc_files = ('README', 'readme', 'CHANGELOG', 'changelog', 'LICENSE', 'license')

print("=== Code files found ===")
for dirpath, _, filenames in os.walk("/workspace"):
    for f in filenames:
        if f.endswith(code_extensions) or f in doc_files:
            full_path = os.path.join(dirpath, f)
            print(full_path)
"""
    
    execution = sandbox.run_code(list_files_code)
    raw_output = ""
    if execution.logs and execution.logs.stdout:
        raw_output = "\n".join(execution.logs.stdout)
    elif execution.text:
        raw_output = execution.text
    
    # Filter out the header line and get actual file paths
    lines = raw_output.splitlines()
    file_paths = []
    for line in lines:
        line = line.strip()
        if line and line.startswith('/workspace') and not line.startswith('==='):
            file_paths.append(line)
    
    print(f"📂 Found {len(file_paths)} code files.")
    
    if not file_paths:
        print("⚠️ No code files found in the repository.")
        return {}
    
    # Read all files using the E2B files.read() API
    code_map = {}
    
    for file_path in file_paths:
        try:
            print(f"📖 Reading {file_path}...")
            content = sandbox.files.read(file_path)
            code_map[file_path] = content
            print(f"✅ Read {file_path} ({len(content)} characters)")
        except Exception as e:
            print(f"⚠️ Error reading {file_path}: {str(e)}")
    
    print(f"✅ Successfully read {len(code_map)} files out of {len(file_paths)} found.")
    
    # Print summary of what was read
    if code_map:
        print("\n📋 Files successfully read:")
        for file_path in sorted(code_map.keys()):
            content_length = len(code_map[file_path])
            print(f"  - {file_path} ({content_length} chars)")
    
    return code_map

def write_file_to_sandbox(sandbox: Sandbox, full_path: str, content: str):
    """Write content to a file in the sandbox."""
    sandbox.files.write(full_path, content)

def delete_file_from_sandbox(sandbox: Sandbox, full_path: str):
    """Delete a file from the sandbox."""
    delete_code = f"""
import os
try:
    os.remove("{full_path}")
except FileNotFoundError:
    pass
"""
    sandbox.run_code(delete_code)