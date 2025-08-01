import os
from e2b_code_interpreter import Sandbox
from dotenv import load_dotenv
from typing import Dict, List

load_dotenv()

def clone_repo_in_sandbox(repo_url: str) -> Sandbox:

    print("🔐 Launching E2B Sandbox...")
    
    # Create sandbox with extended timeout (30 minutes)
    sandbox = Sandbox(timeout=1800)  # 30 minutes in seconds
    
    print(f"📁 Cloning repo into /workspace: {repo_url}")
    
    # First, create the workspace directory
    sandbox.run_code("import os; os.makedirs('/workspace', exist_ok=True)")
    
    # Clone the repository using git command
    execution = sandbox.run_code(f"import subprocess; result = subprocess.run(['git', 'clone', '{repo_url}', '/workspace'], capture_output=True, text=True); print('STDOUT:', result.stdout); print('STDERR:', result.stderr); print('Return code:', result.returncode)")
    
    # Check execution results
    if execution.error:
        print(f"❌ Execution error: {execution.error}")
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
        raise RuntimeError(f"Git clone failed: {output}")
    
    # Verify the clone by listing the workspace directory
    verification = sandbox.run_code("import os; print('Contents of /workspace:'); print(os.listdir('/workspace') if os.path.exists('/workspace') else 'Directory not found')")
    
    if verification.logs and verification.logs.stdout:
        verification_output = "\n".join(verification.logs.stdout)
        print("📋 Workspace contents:", verification_output)
    
    return sandbox

def get_file_tree(sandbox: Sandbox) -> List[str]:
    """Extract the file tree from the sandbox."""
    print("🌳 Extracting file tree...")
    
    # Use the original working method that was finding 37 files
    code = """
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
            # Strip /workspace prefix only
            rel_path = full_path.replace("/workspace/", "")
            print(rel_path)
"""
    execution = sandbox.run_code(code)
    files = []
    
    if execution.logs and execution.logs.stdout:
        # Split properly
        raw_lines = "\n".join(execution.logs.stdout).split("\n")
        for line in raw_lines:
            clean_line = line.strip()
            if clean_line and not clean_line.startswith("==="):
                files.append(clean_line)
    
    print(f"📂 Found {len(files)} files in repository")
    if files:
        print(f"🔍 Debug - First few lines: {files[:5]}")
    return files

def get_relevant_files_from_prompt(prompt: str, file_tree: List[str]) -> List[str]:
    """Use LLM to determine which files are relevant to the task."""
    print("🤖 Determining relevant files...")
    
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from agent.llm_plan.llm import call_groq_with_fallback
    import re
    
    joined_tree = "\n".join(file_tree)
    llm_prompt = f"""
You are helping an AI developer decide which files are relevant to a task in a codebase.

# Task
{prompt}

# File Tree
The following files exist in the codebase. Use exact matches only:
{joined_tree}

IMPORTANT:
- Do not hallucinate or invent paths.
- Only return exact paths from the list above.
- The project is nested under a root folder like 'user-profile-app/', so you MUST include that prefix.

Respond with a plain list of relevant file paths, one per line.
"""
    response = call_groq_with_fallback(llm_prompt)
    
    print(f"🤖 LLM Response (full):")
    print(response)
    
    # Extract file paths with more robust patterns
    # Look for file paths in the response
    lines = response.split('\n')
    relevant_files = []
    
    for line in lines:
        line = line.strip()
        # Remove common prefixes like "- ", "* ", "• " etc.
        line = re.sub(r'^[\s\-*•]+', '', line)
        
        # Check if this line matches any file in our tree
        if line in file_tree:
            relevant_files.append(line)
        else:
            # Try to find partial matches
            for file_path in file_tree:
                if line in file_path or file_path.endswith(line):
                    if file_path not in relevant_files:
                        relevant_files.append(file_path)
    
    # If still no files found, try regex pattern
    if not relevant_files:
        # Split by common delimiters and try each part
        parts = re.split(r'[\s\n,]+', response)
        for part in parts:
            part = part.strip()
            if part in file_tree:
                relevant_files.append(part)
    
    # Remove duplicates and ensure we have valid file paths
    relevant_files = list(set(relevant_files))
    relevant_files = [f for f in relevant_files if f in file_tree]
    
    # Add fallback if LLM still fails
    if not relevant_files:
        print("⚠️ No relevant files detected — falling back to top 5 code files.")
        relevant_files = file_tree[:5]
    
    # Debug: Show what we found
    print(f"🔍 Debug - LLM response lines: {len(lines)}")
    print(f"🔍 Debug - File tree size: {len(file_tree)}")
    print(f"🔍 Debug - Relevant files found: {len(relevant_files)}")
    if relevant_files:
        print(f"🔍 Debug - First few relevant files: {relevant_files[:3]}")
    
    print(f"🎯 LLM selected {len(relevant_files)} relevant files")
    for file in relevant_files:
        print(f"  - {file}")
    
    return relevant_files

def read_selected_files(sandbox: Sandbox, file_paths: List[str]) -> Dict[str, str]:
    """Read only the selected files from the sandbox."""
    print("📖 Reading selected files...")
    
    code_map = {}
    for path in file_paths:
        full_path = f"/workspace/{path}"
        try:
            content = sandbox.files.read(full_path)
            code_map[full_path] = content
            print(f"✅ Read {path} ({len(content)} chars)")
        except Exception as e:
            print(f"❌ Could not read {full_path}: {e}")
    
    print(f"📚 Successfully read {len(code_map)} files")
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


def download_modified_files_from_sandbox(sandbox: Sandbox, modified_files: Dict[str, str], output_dir: str = "./downloads") -> str:
    """
    Download modified files from sandbox to local filesystem.
    
    Args:
        sandbox: The E2B sandbox instance
        modified_files: Dictionary mapping relative paths to file contents
        output_dir: Local directory to save files to (default: ./downloads)
    
    Returns:
        Path to the output directory containing downloaded files
    """
    import os
    import uuid
    from datetime import datetime
    
    # Create unique output directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_output_dir = os.path.join(output_dir, f"modified_files_{timestamp}")
    os.makedirs(full_output_dir, exist_ok=True)
    
    print(f"📁 Downloading {len(modified_files)} modified files to: {full_output_dir}")
    
    downloaded_files = []
    
    for relative_path, content in modified_files.items():
        try:
            # Create the local file path
            local_file_path = os.path.join(full_output_dir, relative_path)
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
            
            # Write the file content
            with open(local_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            downloaded_files.append(relative_path)
            print(f"✅ Downloaded: {relative_path}")
            
        except Exception as e:
            print(f"⚠️ Error downloading {relative_path}: {str(e)}")
    
    print(f"📦 Successfully downloaded {len(downloaded_files)} files to: {full_output_dir}")
    
    # Create a summary file
    summary_path = os.path.join(full_output_dir, "DOWNLOAD_SUMMARY.txt")
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(f"Modified Files Download Summary\n")
        f.write(f"==============================\n\n")
        f.write(f"Total files downloaded: {len(downloaded_files)}\n")
        f.write(f"Download timestamp: {timestamp}\n")
        f.write(f"Download location: {full_output_dir}\n\n")
        f.write("Files:\n")
        for file_path in downloaded_files:
            f.write(f"- {file_path}\n")
    
    return full_output_dir


def download_single_file_from_sandbox(sandbox: Sandbox, sandbox_path: str, local_path: str) -> bool:
    """
    Download a single file from sandbox to local filesystem.
    
    Args:
        sandbox: The E2B sandbox instance
        sandbox_path: Path to file in sandbox
        local_path: Local path to save the file
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Read file from sandbox
        content = sandbox.files.read(sandbox_path)
        
        # Ensure the directory exists
        import os
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        # Write file to local filesystem
        with open(local_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
        print(f"✅ Downloaded single file: {sandbox_path} -> {local_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error downloading {sandbox_path}: {str(e)}")
        return False


def get_sandbox_file_content(sandbox: Sandbox, file_path: str) -> str:
    """
    Get the content of a file from the sandbox.
    
    Args:
        sandbox: The E2B sandbox instance
        file_path: Path to file in sandbox
    
    Returns:
        File content as string
    """
    try:
        content = sandbox.files.read(file_path)
        return content
    except Exception as e:
        print(f"❌ Error reading {file_path}: {str(e)}")
        return ""