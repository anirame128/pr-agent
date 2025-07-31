import os
import re
import random
from groq import Groq
from dotenv import load_dotenv
from typing import Dict, List, Optional

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# List of available models to cycle through to avoid rate limits
# Only using models with high daily limits and good context windows
AVAILABLE_MODELS = [
    "moonshotai/kimi-k2-instruct", # 60 RPM, 1000 RPD, 10000 TPM, 300000 TPD
]

def get_next_model() -> str:
    """Get the next model to use, cycling through available models."""
    return random.choice(AVAILABLE_MODELS)

def call_groq_with_fallback(prompt: str, temperature: float = 0.3, max_retries: int = 3) -> str:
    """Call Groq API with fallback to different models if rate limited."""
    for attempt in range(max_retries):
        model = get_next_model()
        print(f"🔍 DEBUG: Using model {model} (attempt {attempt + 1}/{max_retries})")
        
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            result = completion.choices[0].message.content.strip()
            print(f"🔍 DEBUG: Success with model {model}")
            return result
        except Exception as e:
            error_msg = str(e)
            print(f"❌ DEBUG: Error with model {model}: {error_msg}")
            
            # If it's a rate limit error, try another model
            if "rate_limit" in error_msg.lower() or "429" in error_msg:
                if attempt < max_retries - 1:
                    print(f"🔄 DEBUG: Rate limited, trying another model...")
                    continue
                else:
                    print(f"❌ DEBUG: All models rate limited after {max_retries} attempts")
                    raise e
            else:
                # For non-rate-limit errors, raise immediately
                raise e
    
    raise RuntimeError("All models failed after maximum retries")

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

    # Call Groq LLM API with fallback
    return call_groq_with_fallback(filled_prompt, temperature=0.2)