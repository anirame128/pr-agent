import os
import re
from typing import Generator, List, Dict
from agent.llm_plan.llm import call_groq_with_fallback
from agent.e2b_sandboxing.sandbox import write_file_to_sandbox, delete_file_from_sandbox

def extract_api_routes(context: str) -> str:
    """Extract API route information from codebase context"""
    if not context:
        return "No API routes found in context"
    
    # Look for API route patterns in the context
    api_routes = []
    
    # Common patterns for API routes
    patterns = [
        r'/api/[^/\s]+/route\.ts',
        r'/api/[^/\s]+/[^/\s]+/route\.ts',
        r'route\.ts',
        r'api/[^/\s]+',
    ]
    
    for pattern in patterns:
        import re
        matches = re.findall(pattern, context, re.IGNORECASE)
        for match in matches:
            if match not in api_routes:
                api_routes.append(match)
    
    if api_routes:
        return "Available API routes:\n" + "\n".join([f"- {route}" for route in api_routes])
    else:
        return "No API routes found in context"

def apply_plan_steps(sandbox, parsed_steps: List[Dict], codebase_context: str = None) -> Generator[str, None, None]:
    yield f"🔧 Applying {len(parsed_steps)} plan steps...\n"

    for idx, step in enumerate(parsed_steps):
        action = step["action"]
        relative_path = step["file"]
        file_path = f"/workspace/{relative_path}"
        description = step["description"]

        yield f"🔧 Step {idx + 1}/{len(parsed_steps)}: {action.upper()} `{file_path}` — {description}"

        try:
            if action == "create":
                # Extract API routes for context
                api_routes_info = extract_api_routes(codebase_context)
                
                prompt = (
                    f"Create a new TypeScript file at `{relative_path}`.\n"
                    f"Task: {description}\n\n"
                    f"{api_routes_info}\n\n"
                    "Return ONLY the complete raw TypeScript code, no explanations or markdown formatting, no triple backticks."
                )
                code = call_groq_with_fallback(prompt)
                
                # Remove any triple backtick markdown wrapping
                if code.startswith("```"):
                    code = re.sub(r"^```[a-z]*\n", "", code)  # strip opening ```ts
                    code = re.sub(r"\n```$", "", code)        # strip closing ```
                
                write_file_to_sandbox(sandbox, file_path, code)
                yield f"✅ Created `{file_path}`"

            elif action == "modify":
                original_code = sandbox.files.read(file_path)
                
                # Extract API routes for context
                api_routes_info = extract_api_routes(codebase_context)
                
                prompt = (
                    f"You are modifying a TypeScript file:\n"
                    f"Path: {relative_path}\n\n"
                    f"Current content:\n{original_code}\n\n"
                    f"Task: {description}\n\n"
                    f"{api_routes_info}\n\n"
                    "Return ONLY the full modified file content. Do NOT include markdown syntax, triple backticks, or explanation."
                )
                code = call_groq_with_fallback(prompt)
                
                # Remove any triple backtick markdown wrapping
                if code.startswith("```"):
                    code = re.sub(r"^```[a-z]*\n", "", code)  # strip opening ```ts
                    code = re.sub(r"\n```$", "", code)        # strip closing ```
                
                write_file_to_sandbox(sandbox, file_path, code)
                yield f"✅ Modified `{file_path}`"

            elif action == "delete":
                delete_file_from_sandbox(sandbox, file_path)
                yield f"🗑️ Deleted `{file_path}`"

            else:
                yield f"⚠️ Unknown action `{action}` — skipping `{file_path}`"

        except Exception as e:
            yield f"❌ Failed to apply step to `{file_path}`: {e}"

    yield "\n✅ Plan application completed"
