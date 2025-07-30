import os
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_plan(codebase_summary: str, user_prompt: str):
    # load prompt template
    with open("agent/llm_plan/prompts/generate_plan.md", "r") as f:
        template = f.read()

    # Inject context and request into prompt template
    filled_prompt = (
        template
        .replace("{CONTEXT}", codebase_summary[:12000])  # trim for token safety
        .replace("{REQUEST}", user_prompt)
    )

    # Call Groq LLM API
    completion = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "user", "content": filled_prompt}
        ],
        temperature=0.2,
    )

    return completion.choices[0].message.content.strip()

def format_plan_as_markdown(plan_text: str) -> str:
    """Convert XML-style <plan> output to a Markdown bullet list."""
    steps = re.findall(r"<step>(.*?)</step>", plan_text, re.DOTALL)

    if not steps:
        return "**⚠️ No valid steps found in plan.**"

    markdown_lines = ["### 🧠 Plan:\n"]
    for step in steps:
        action = re.search(r"<action>(.*?)</action>", step)
        file = re.search(r"<file>(.*?)</file>", step)
        desc = re.search(r"<description>(.*?)</description>", step)

        if not action or not file or not desc:
            continue

        action_emoji = {
            "create": "➕",
            "modify": "✏️",
            "delete": "🗑️"
        }.get(action.group(1).strip().lower(), "📄")

        line = f"- {action_emoji} **{action.group(1).strip()}** `{file.group(1).strip()}`: {desc.group(1).strip()}"
        markdown_lines.append(line)

    return "\n".join(markdown_lines)