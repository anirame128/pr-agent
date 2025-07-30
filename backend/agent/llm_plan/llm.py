import os
import re
from groq import Groq
from dotenv import load_dotenv
from typing import Dict, List, Optional

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

def generate_code_for_step(context: str, step: Dict[str, str]) -> str:
    """Use LLM to generate real code for a single plan step."""
    print(f"🔍 DEBUG: Starting generate_code_for_step for {step['file']}")
    print(f"🔍 DEBUG: Action: {step['action']}, Description: {step['description']}")
    
    prompt = f"""
You are modifying a codebase with the following context:

{context[:12000]}

Your task is to implement the following change:

- Action: {step['action']}
- File: {step['file']}
- Description: {step['description']}

Respond with complete code for the file `{step['file']}`.
"""

    print(f"🔍 DEBUG: About to call Groq API for {step['file']}")
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        print(f"🔍 DEBUG: Groq API call completed for {step['file']}")
        result = completion.choices[0].message.content.strip()
        print(f"🔍 DEBUG: Generated {len(result)} characters for {step['file']}")
        return result
    except Exception as e:
        print(f"❌ DEBUG: Error in generate_code_for_step for {step['file']}: {str(e)}")
        raise e

def self_review_code(
    original_context: str,
    step: Dict[str, str],
    generated_code: str,
    file_extension: Optional[str] = None
) -> Dict[str, any]:
    """
    Use LLM to self-review generated code for quality, correctness, and improvements.
    
    Returns a dictionary with:
    - score: 1-10 rating
    - issues: list of problems found
    - suggestions: list of improvements
    - confidence: high/medium/low confidence in the review
    - should_regenerate: boolean indicating if code should be regenerated
    """
    print(f"🔍 DEBUG: Starting self-review for {step['file']}")
    
    # Determine file type for better review
    file_type = file_extension or step['file'].split('.')[-1] if '.' in step['file'] else 'unknown'
    
    prompt = f"""
You are a senior software engineer conducting a code review. Review the following generated code:

**Context:**
{original_context[:8000]}

**Task:**
- Action: {step['action']}
- File: {step['file']} (Type: {file_type})
- Description: {step['description']}

**Generated Code:**
```{file_type}
{generated_code}
```

Please provide a comprehensive review in the following JSON format:

{{
    "score": <1-10 rating>,
    "issues": [
        {{
            "severity": "critical|high|medium|low",
            "description": "description of the issue",
            "line_numbers": [optional line numbers if applicable]
        }}
    ],
    "suggestions": [
        {{
            "type": "improvement|optimization|best_practice",
            "description": "description of the suggestion"
        }}
    ],
    "confidence": "high|medium|low",
    "should_regenerate": <true|false>,
    "summary": "brief summary of the review"
}}

Focus on:
1. Code correctness and functionality
2. Adherence to best practices
3. Security considerations
4. Performance implications
5. Maintainability and readability
6. Whether the code actually addresses the original task

Respond with valid JSON only.
"""

    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,  # Lower temperature for more consistent reviews
        )
        
        review_text = completion.choices[0].message.content.strip()
        print(f"🔍 DEBUG: Self-review completed for {step['file']}")
        
        # Parse JSON response
        import json
        try:
            review_data = json.loads(review_text)
            print(f"🔍 DEBUG: Review score: {review_data.get('score', 'N/A')}/10")
            return review_data
        except json.JSONDecodeError as e:
            print(f"❌ DEBUG: Failed to parse review JSON: {str(e)}")
            # Fallback to a basic review structure
            return {
                "score": 5,
                "issues": [{"severity": "medium", "description": "Failed to parse review response"}],
                "suggestions": [],
                "confidence": "low",
                "should_regenerate": False,
                "summary": "Review parsing failed"
            }
            
    except Exception as e:
        print(f"❌ DEBUG: Error in self_review_code for {step['file']}: {str(e)}")
        return {
            "score": 1,
            "issues": [{"severity": "critical", "description": f"Review failed: {str(e)}"}],
            "suggestions": [],
            "confidence": "low",
            "should_regenerate": True,
            "summary": "Review process failed"
        }

def format_review_as_markdown(review_data: Dict[str, any], filename: str) -> str:
    """Convert review data to a readable markdown format."""
    score = review_data.get('score', 0)
    confidence = review_data.get('confidence', 'unknown')
    should_regenerate = review_data.get('should_regenerate', False)
    
    # Score emoji
    score_emoji = "🟢" if score >= 8 else "🟡" if score >= 6 else "🔴"
    confidence_emoji = "🟢" if confidence == "high" else "🟡" if confidence == "medium" else "🔴"
    regenerate_emoji = "⚠️" if should_regenerate else "✅"
    
    markdown_lines = [
        f"### 🔍 Self-Review: `{filename}`",
        f"",
        f"**Score:** {score_emoji} {score}/10",
        f"**Confidence:** {confidence_emoji} {confidence}",
        f"**Regenerate:** {regenerate_emoji} {'Yes' if should_regenerate else 'No'}",
        f"",
        f"**Summary:** {review_data.get('summary', 'No summary provided')}",
        f""
    ]
    
    # Issues section
    issues = review_data.get('issues', [])
    if issues:
        markdown_lines.append("#### 🚨 Issues Found:")
        for issue in issues:
            severity_emoji = {
                "critical": "🔴",
                "high": "🟠", 
                "medium": "🟡",
                "low": "🟢"
            }.get(issue.get('severity', 'medium'), "🟡")
            
            line_nums = issue.get('line_numbers', [])
            line_info = f" (lines {', '.join(map(str, line_nums))})" if line_nums else ""
            
            markdown_lines.append(
                f"- {severity_emoji} **{issue.get('severity', 'unknown').title()}**: "
                f"{issue.get('description', 'No description')}{line_info}"
            )
        markdown_lines.append("")
    
    # Suggestions section
    suggestions = review_data.get('suggestions', [])
    if suggestions:
        markdown_lines.append("#### 💡 Suggestions:")
        for suggestion in suggestions:
            type_emoji = {
                "improvement": "✨",
                "optimization": "⚡",
                "best_practice": "📚"
            }.get(suggestion.get('type', 'improvement'), "💡")
            
            markdown_lines.append(
                f"- {type_emoji} **{suggestion.get('type', 'improvement').title()}**: "
                f"{suggestion.get('description', 'No description')}"
            )
        markdown_lines.append("")
    
    return "\n".join(markdown_lines)

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