from typing import List, Dict
from e2b_code_interpreter import Sandbox
from agent.e2b_sandboxing.sandbox import write_file_to_sandbox, delete_file_from_sandbox
from agent.llm_plan.llm import generate_code_for_step, self_review_code, format_review_as_markdown

async def apply_plan_steps(sandbox: Sandbox, steps: List[Dict[str, str]], preprocessed_context: str) -> List[str]:
    logs = []
    print(f"🔍 DEBUG: Starting apply_plan_steps with {len(steps)} steps")

    for i, step in enumerate(steps, 1):
        action = step["action"]
        file_path = f"/workspace/{step['file']}"
        description = step["description"]
        print(f"🔍 DEBUG: Processing step {i}/{len(steps)}: {action} {file_path}")
        logs.append(f"🔧 Step {i}: {action.upper()} `{file_path}` — {description}")

        try:
            if action in {"create", "modify"}:
                print(f"🔍 DEBUG: About to generate code for {file_path}")
                logs.append(f"🧠 Generating code for `{file_path}`...")
                
                # Generate code with self-review and potential regeneration
                code = await generate_code_with_review(preprocessed_context, step, logs)
                
                print(f"🔍 DEBUG: Code generated, about to write file {file_path}")
                write_file_to_sandbox(sandbox, file_path, code)
                print(f"🔍 DEBUG: File written successfully for {file_path}")
                logs.append(f"✅ {action.title()}d `{file_path}`")

            elif action == "delete":
                print(f"🔍 DEBUG: About to delete file {file_path}")
                delete_file_from_sandbox(sandbox, file_path)
                print(f"🔍 DEBUG: File deleted successfully for {file_path}")
                logs.append(f"✅ Deleted `{file_path}`")

        except Exception as e:
            print(f"❌ DEBUG: Error processing step {i}: {str(e)}")
            logs.append(f"❌ Error on `{file_path}`: {str(e)}")

    print(f"🔍 DEBUG: Completed apply_plan_steps, returning {len(logs)} logs")
    return logs

async def generate_code_with_review(context: str, step: Dict[str, str], logs: List[str], max_attempts: int = 3) -> str:
    """
    Generate code with self-review and potential regeneration.
    Returns the best code after review and potential regeneration attempts.
    """
    best_code = None
    best_score = 0
    
    for attempt in range(1, max_attempts + 1):
        logs.append(f"🔄 Attempt {attempt}/{max_attempts} for `{step['file']}`...")
        
        # Generate code
        code = generate_code_for_step(context, step)
        
        # Self-review the generated code
        logs.append(f"🔍 Self-reviewing generated code...")
        review = self_review_code(context, step, code)
        
        # Format review for logging
        review_markdown = format_review_as_markdown(review, step['file'])
        logs.append(f"\n{review_markdown}")
        
        current_score = review.get('score', 0)
        should_regenerate = review.get('should_regenerate', False)
        
        # Track the best code so far
        if current_score > best_score:
            best_code = code
            best_score = current_score
        
        # Log the review results
        logs.append(f"📊 Review Score: {current_score}/10")
        logs.append(f"🎯 Should Regenerate: {'Yes' if should_regenerate else 'No'}")
        
        # If review is good enough or we've reached max attempts, use this code
        if not should_regenerate or attempt == max_attempts:
            if attempt > 1:
                logs.append(f"✅ Using best code from {attempt} attempts (score: {best_score}/10)")
            else:
                logs.append(f"✅ Using generated code (score: {current_score}/10)")
            return best_code or code
        
        # If we should regenerate and have attempts left, continue
        if should_regenerate and attempt < max_attempts:
            logs.append(f"🔄 Regenerating code due to review feedback...")
            continue
    
    # Fallback: return the best code we have
    return best_code or code
