import os
from .e2b_sandboxing.sandbox import clone_repo_in_sandbox, read_codebase
from .preprocessing.file_preprocess import preprocess_codebase_with_context
from .llm_plan.llm import generate_plan
from .file_modification.plan_parsing import parse_plan_generalized
from .file_modification.plan_application import apply_plan_steps
from .git_commands.git_sync import (
    extract_modified_files,
    get_default_branch,
    sync_and_commit_from_sandbox,
    create_pull_request
)
import os

async def run_agent_flow(repo_url: str, prompt: str, enable_modifications: bool = False, github_token: str = None):
    """Main agent flow - simplified to use only sandbox functions"""
    
    sandbox = None
    try:
        # Step 1: Launch sandbox and clone repo
        yield "🔄 Cloning repository..."
        sandbox = clone_repo_in_sandbox(repo_url)
        yield "✅ Repo cloned into sandbox"
        
        # Step 2: Read and analyze codebase
        yield "🧾 Reading codebase..."
        code_files = read_codebase(sandbox)
        yield f"✅ Read {len(code_files)} files from codebase"
        
        # Step 4: Preprocess codebase with external context injection
        yield "🔄 Preprocessing codebase with external context..."
        codebase_context = preprocess_codebase_with_context(code_files, prompt)

        # output_dir = "debug_output"
        # os.makedirs(output_dir, exist_ok=True)
        # codebase_context_file = os.path.join(output_dir, "codebase_context.txt")
        # with open(codebase_context_file, "w", encoding="utf-8") as f:
        #     f.write(codebase_context)
        # print(f"📁 Codebase context saved to: {codebase_context_file}")
        
        # Step 5: Generate plan
        yield "🤖 Generating plan..."
        raw_plan = generate_plan(codebase_context, prompt)
        
        # Save raw plan to a file for analysis
        # output_dir = "debug_output"
        # os.makedirs(output_dir, exist_ok=True)
        # plan_file = os.path.join(output_dir, "raw_plan.txt")
        # with open(plan_file, "w", encoding="utf-8") as f:
        #     f.write(f"PROMPT: {prompt}\n\n")
        #     f.write(f"PLAN LENGTH: {len(raw_plan)} characters\n\n")
        #     f.write("RAW PLAN:\n")
        #     f.write(raw_plan)
        # print(f"📁 Raw plan saved to: {plan_file}")
        
        # yield "✅ Plan generated"
        
        # Step 6: Parse plan into structured steps
        yield "🔍 Parsing plan..."
        parsed_steps = parse_plan_generalized(raw_plan, codebase_context)
        yield f"✅ Parsed {len(parsed_steps)} steps from plan"
                    
        # Step 7: Apply the plan steps
        yield "🔧 Applying plan steps..."
        application_logs = apply_plan_steps(sandbox, parsed_steps, codebase_context)
        for log in application_logs:
            yield log
        yield "✅ Plan application completed"
        
        # Step 8: Git sync and create pull request
        if github_token:
            yield "\n🔄 Syncing changes to repository..."
            try:
                # Extract modified files from sandbox
                modified_files = extract_modified_files(sandbox, parsed_steps)
                yield f"📁 Extracted {len(modified_files)} modified files"
                
                if modified_files:
                    # Get default branch
                    default_branch = get_default_branch(repo_url, github_token)
                    yield f"🌿 Default branch: {default_branch}"
                    
                    # Generate branch name and commit message
                    import uuid
                    branch_name = f"agent-changes-{uuid.uuid4().hex[:8]}"
                    commit_message = f"Apply agent changes: {prompt[:100]}..."
                    
                    # Sync and commit changes
                    temp_dir = sync_and_commit_from_sandbox(
                        repo_url=repo_url,
                        modified_files=modified_files,
                        branch_name=branch_name,
                        commit_message=commit_message,
                        github_token=github_token
                    )
                    yield f"✅ Changes committed to branch: {branch_name}"
                    
                    # Create pull request
                    yield "🔄 Creating pull request..."
                    pr_title = f"🤖 Agent Changes: {prompt[:50]}..."
                    pr_body = f"""
## Agent Changes

**Prompt:** {prompt}

**Changes Applied:**
{chr(10).join([f"- {action.title()} `{file}`: {desc}" for action, file, desc in [(s['action'], s['file'], s['description']) for s in parsed_steps]])}

**Modified Files:** {len(modified_files)} files
"""
                    
                    pr_url = await create_pull_request(
                        repo_url=repo_url,
                        branch_name=branch_name,
                        base_branch=default_branch,
                        pr_title=pr_title,
                        pr_body=pr_body,
                        github_token=github_token
                    )
                    yield f"✅ Pull request created: {pr_url}"
                    
                else:
                    yield "⚠️ No files were modified, skipping Git sync"
                    
            except Exception as e:
                yield f"❌ Git sync failed: {str(e)}"
                print(f"Git sync error: {str(e)}")
        else:
            yield "\n⚠️ No GitHub token provided - skipping Git sync"
            yield "Provide github_token parameter to enable automatic PR creation"
            
        if not enable_modifications and parsed_steps:
            yield "\n⚠️ Modifications disabled - plan would create/modify/delete files"
            yield "Enable modifications to apply changes"
        elif not parsed_steps:
            yield "\n⚠️ No steps to apply"
        
    except Exception as e:
        yield f"❌ Error in agent flow: {str(e)}"
        print(f"Agent flow error: {str(e)}")
    finally:
        # Clean up sandbox to reduce costs
        if sandbox:
            try:
                yield "🧹 Cleaning up sandbox..."
                sandbox.kill()
                yield "✅ Sandbox terminated"
            except Exception as e:
                yield f"⚠️ Error terminating sandbox: {str(e)}"
                print(f"Sandbox cleanup error: {str(e)}")
