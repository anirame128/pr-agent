import re
import os
from agent.llm_plan.llm import call_groq_with_fallback
from agent.e2b_sandboxing.sandbox import write_file_to_sandbox, delete_file_from_sandbox
from typing import Dict, List


def load_prompt_template(template_name: str) -> str:
    """Load a prompt template from the prompts directory."""
    template_path = os.path.join(os.path.dirname(__file__), "prompts", f"{template_name}.md")
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Prompt template not found: {template_path}")


def parse_plan_generalized(plan_text: str) -> List[Dict[str, str]]:
    """Parse the XML-style plan format into actionable steps."""
    steps = []
    raw_steps = re.findall(r"<step>(.*?)</step>", plan_text, re.DOTALL)

    for raw_step in raw_steps:
        action = re.search(r"<action>(.*?)</action>", raw_step, re.DOTALL)
        file_path = re.search(r"<file>(.*?)</file>", raw_step, re.DOTALL)
        description = re.search(r"<description>(.*?)</description>", raw_step, re.DOTALL)

        if action and file_path and description:
            steps.append({
                "action": action.group(1).strip().lower(),
                "file": file_path.group(1).strip(),
                "description": description.group(1).strip()
            })
    return steps


def apply_llm_plan_to_code(sandbox, steps: List[Dict[str, str]], current_code: Dict[str, str]) -> Dict[str, str]:
    """
    Applies parsed plan steps to the sandbox codebase using the LLM for code generation.

    Returns a dictionary of {relative_file_path: new_content}
    """
    modified_files = {}

    for step in steps:
        action = step["action"]
        file_path = step["file"]
        description = step["description"]
        full_path = f"/workspace/{file_path}"
        original_code = current_code.get(full_path, "")

        # Format prompt
        if action == "create":
            template = load_prompt_template("create_file")
            # Use safe string replacement to avoid conflicts with curly braces in content
            prompt = template.replace("{file_path}", file_path).replace("{description}", description)
        elif action == "modify":
            template = load_prompt_template("modify_file")
            # Use safe string replacement to avoid conflicts with curly braces in content
            prompt = template.replace("{file_path}", file_path).replace("{description}", description).replace("{original_code}", original_code)
        elif action == "delete":
            print(f"🗑️ Deleting file: {file_path}")
            delete_file_from_sandbox(sandbox, full_path)
            continue
        else:
            print(f"⚠️ Unknown action '{action}' for file '{file_path}'")
            continue

        # Call the model
        try:
            new_code = call_groq_with_fallback(prompt, temperature=0.2)
            # Strip markdown formatting if present
            if "```" in new_code:
                new_code = re.sub(r"```[a-z]*", "", new_code).replace("```", "").strip()

            print(f"✅ Applying changes to: {file_path}")
            write_file_to_sandbox(sandbox, full_path, new_code)
            modified_files[file_path] = new_code
        except Exception as e:
            print(f"❌ Failed to apply change to {file_path}: {e}")

    return modified_files