import asyncio
import json
from typing import AsyncGenerator
from .sandbox import clone_repo_in_sandbox, read_codebase

async def run_agent_flow(repo_url: str, prompt: str, enable_modifications: bool = False):
    """Main agent flow - simplified to use only sandbox functions"""
    
    try:
        # Step 1: Launch sandbox and clone repo
        yield "🔄 Cloning repository..."
        sandbox = clone_repo_in_sandbox(repo_url)
        yield "✅ Repo cloned into sandbox"
        
        # Step 2: Read and analyze codebase
        yield "🧾 Reading codebase..."
        code_files = read_codebase(sandbox)
        yield f"✅ Read {len(code_files)} files from codebase"
        
        # Step 3: Basic analysis (just return file info for now)
        yield "📋 **CODEBASE SUMMARY:**"
        yield f"Total files: {len(code_files)}"
        
        if code_files:
            yield "\n**Files found:**"
            for file_path in sorted(code_files.keys()):
                content_length = len(code_files[file_path])
                yield f"- {file_path} ({content_length} characters)"
        
        # Step 4: Simple prompt response (placeholder)
        yield f"\n**User Prompt:** {prompt}"
        yield "🤖 Analysis complete! (Using simplified sandbox-only flow)"
        
        # Note: Sandbox cleanup is handled automatically by E2B
        yield "🧹 Sandbox cleanup handled automatically"
            
    except Exception as e:
        yield f"❌ Error in agent flow: {str(e)}"
        print(f"Agent flow error: {str(e)}")
