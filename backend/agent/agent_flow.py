from typing import AsyncGenerator
from .e2b_sandboxing.sandbox import clone_repo_in_sandbox, read_codebase
from .preprocessing.file_preprocess import preprocess_codebase
from .llm_plan.llm import generate_plan, format_plan_as_markdown
from .file_modification.plan_parsing import parse_plan

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
        # yield "📋 **CODEBASE SUMMARY:**"
        # yield f"Total files: {len(code_files)}"
        
        # if code_files:
        #     yield "\n**Files found:**"
        #     for file_path in sorted(code_files.keys()):
        #         content_length = len(code_files[file_path])
        #         yield f"- {file_path} ({content_length} characters)"
        
        # Step 4: Preprocess codebase
        yield "🔄 Preprocessing codebase..."
        codebase_context = preprocess_codebase(code_files)
        #print(len(codebase_context))
        #print(codebase_context[:8000])
        yield "✅ Codebase preprocessed"
        
        # Step 5: Generate plan
        yield "🤖 Generating plan..."
        raw_plan = generate_plan(codebase_context, prompt)
        yield "✅ Plan generated"

        # Stream pretty version
        pretty_plan = format_plan_as_markdown(raw_plan)
        #yield f"\n{pretty_plan}"
        
        # Step 6: Parse plan into structured steps
        yield "🔍 Parsing plan..."
        parsed_steps = parse_plan(raw_plan)
        yield f"✅ Parsed {len(parsed_steps)} steps from plan"
        
        # For now, just show the parsed steps (you can extend this later)
        if parsed_steps:
            yield "\n**Parsed Steps:**"
            for i, step in enumerate(parsed_steps, 1):
                yield f"{i}. **{step['action'].title()}** `{step['file']}`: {step['description']}"
        else:
            yield "⚠️ No valid steps found in plan"
            
    except Exception as e:
        yield f"❌ Error in agent flow: {str(e)}"
        print(f"Agent flow error: {str(e)}")
