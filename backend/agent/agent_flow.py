import os
from .e2b_sandboxing.sandbox import (
    clone_repo_in_sandbox, 
    get_file_tree, 
    get_relevant_files_from_prompt, 
    read_selected_files,
    download_modified_files_from_sandbox,
    get_sandbox_file_content,
    write_file_to_sandbox
)
from .preprocessing.lightly_preprocess_files import lightly_preprocess_files
from .llm_plan.llm import generate_plan
from .file_modification.plan_file_application import parse_plan_generalized, apply_llm_plan_to_code
from .git_commands.git_sync import (
    extract_modified_files,
    get_default_branch,
    sync_and_commit_from_sandbox,
    create_pull_request
)

async def run_agent_flow(repo_url: str, prompt: str, enable_modifications: bool = False, github_token: str = None):
    """Main agent flow - simplified to use only sandbox functions"""
    
    sandbox = None
    try:
        # Step 1: Launch sandbox and clone repo
        yield "🔄 Cloning repository..."
        sandbox = clone_repo_in_sandbox(repo_url)
        yield "✅ Repo cloned into sandbox"
        
        # Step 2: Extract file tree
        yield "🌳 Extracting file tree..."
        file_tree = get_file_tree(sandbox)
        yield f"✅ Found {len(file_tree)} files in repository"
        
        yield "📦 Generating stack knowledge file..."
        try:
            # Dynamically find package.json in the file tree
            pkg_path = next((f for f in file_tree if f.endswith("package.json")), None)
            if not pkg_path:
                raise FileNotFoundError("package.json not found in file tree")

            package_json = get_sandbox_file_content(sandbox, f"/workspace/{pkg_path}")
            from agent.preprocessing.stack_knowledge import detect_stack_from_package_json, generate_stack_knowledge_md
            stack = detect_stack_from_package_json(package_json)
            knowledge_md = generate_stack_knowledge_md(stack)

            # Write STACK_KNOWLEDGE.md next to the package.json
            sandbox_dir = os.path.dirname(pkg_path)
            write_file_to_sandbox(sandbox, f"/workspace/{sandbox_dir}/STACK_KNOWLEDGE.md", knowledge_md)

            yield f"✅ Stack knowledge file written ({len(stack)} libs)"
        except Exception as e:
            yield f"⚠️ Failed to generate stack knowledge file: {e}"
            
        # Step 3: Determine relevant files using LLM
        yield "🤖 Determining relevant files..."
        relevant_files = get_relevant_files_from_prompt(prompt, file_tree)
        yield f"✅ LLM selected {len(relevant_files)} relevant files"
        
        # Step 4: Read only relevant files
        yield "📖 Reading selected files..."
        code_files = read_selected_files(sandbox, relevant_files)
        yield f"✅ Read {len(code_files)} relevant files"
        
        # Step 5: Lightly preprocess files
        yield "🔄 Lightly preprocessing files..."
        codebase_context = lightly_preprocess_files(code_files)
        os.makedirs("debug_output", exist_ok=True)
        with open("debug_output/lightly_preprocessed_files.txt", "w", encoding="utf-8") as f:
            f.write(codebase_context)
        yield "✅ Lightly preprocessed files"
        
        try:
            # Try to read STACK_KNOWLEDGE.md from the same directory as package.json
            pkg_path = next((f for f in file_tree if f.endswith("package.json")), None)
            if pkg_path:
                sandbox_dir = os.path.dirname(pkg_path)
                stack_md_path = f"/workspace/{sandbox_dir}/STACK_KNOWLEDGE.md"
                stack_context = get_sandbox_file_content(sandbox, stack_md_path)
            else:
                stack_context = ""
        except Exception:
            stack_context = ""
        combined_context = (stack_context + "\n\n" + codebase_context)
        # Step 6: Generate plan
        yield "🤖 Generating plan..."
        raw_plan = generate_plan(combined_context, prompt)
        os.makedirs("debug_output", exist_ok=True)
        with open("debug_output/raw_plan.txt", "w", encoding="utf-8") as f:
            f.write(raw_plan)
        yield "✅ Plan generated"
        
        # Step 7: Parse plan
        yield "🔍 Parsing plan..."
        parsed_steps = parse_plan_generalized(raw_plan)
        yield f"✅ Parsed {len(parsed_steps)} steps from plan"

        # Step 8: Apply the plan steps
        yield "🔧 Applying plan steps..."
        modified_files = apply_llm_plan_to_code(sandbox, parsed_steps, code_files)
        yield f"✅ Applied {len(modified_files)} changes"

        # Step 9: Download modified files for inspection
        if modified_files:
            yield "📁 Downloading modified files for inspection..."
            try:
                output_dir = download_modified_files_from_sandbox(sandbox, modified_files)
                yield f"✅ Downloaded modified files to: {output_dir}"
                yield f"📋 Summary: {len(modified_files)} files modified and downloaded"
            except Exception as e:
                yield f"⚠️ Error downloading files: {str(e)}"
        else:
            yield "ℹ️ No files were modified"

        # Step 10: Git sync and create pull request
        if github_token and modified_files:
            yield "\n🔄 Syncing changes to repository..."
            try:
                # Extract modified files from sandbox
                extracted_files = extract_modified_files(sandbox, parsed_steps)
                yield f"📁 Extracted {len(extracted_files)} modified files"
                
                if extracted_files:
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
                        modified_files=extracted_files,
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

**Modified Files:** {len(extracted_files)} files
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
        elif github_token and not modified_files:
            yield "\n⚠️ No files were modified, skipping Git sync"
        elif not github_token:
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
