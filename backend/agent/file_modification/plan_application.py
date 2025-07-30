from typing import List, Dict
from e2b_code_interpreter import Sandbox
from agent.e2b_sandboxing.sandbox import write_file_to_sandbox, delete_file_from_sandbox
from agent.llm_plan.llm import generate_code_for_step

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
                code = generate_code_for_step(preprocessed_context, step)
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
