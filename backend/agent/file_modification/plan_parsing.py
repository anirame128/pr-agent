import re
from typing import List, Dict

def parse_plan(plan_text: str) -> List[Dict[str, str]]:

    steps = []

    # Extract raw steps from XML-style output
    raw_steps = re.findall(r"<step>(.*?)</step>", plan_text, re.DOTALL)

    for raw_step in raw_steps:
        # Extract action, file, and description from each step
        action_match = re.search(r"<action>(.*?)</action>", raw_step, re.DOTALL)
        file_match = re.search(r"<file>(.*?)</file>", raw_step, re.DOTALL)
        desc_match = re.search(r"<description>(.*?)</description>", raw_step, re.DOTALL)

        if action_match and file_match and desc_match:
            action = action_match.group(1).strip().lower()
            file = file_match.group(1).strip().lower()
            description = desc_match.group(1).strip()

            if action in {"create", "modify", "delete"}:
                steps.append({
                    "action": action,
                    "file": file,
                    "description": description
                })

    return steps