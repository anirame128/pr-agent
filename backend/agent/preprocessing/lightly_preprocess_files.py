import re
from typing import Dict

def lightly_preprocess_files(code_files: Dict[str, str]) -> str:
    """
    Preprocess code files to produce a readable, trimmed markdown-formatted context string.
    Focuses on exports, main components, functions, and class definitions.
    """
    processed_sections = []

    for full_path, code in code_files.items():
        # Normalize path to relative form
        rel_path = full_path.replace("/workspace/", "")

        # Extract main symbols (functions, classes, components, exports)
        important_lines = []
        for line in code.splitlines():
            line = line.strip()
            if (
                line.startswith("export ") or
                line.startswith("def ") or
                line.startswith("class ") or
                line.startswith("function ") or
                line.startswith("const ") or
                "useState(" in line or
                "useEffect(" in line or
                line.startswith("return (")
            ):
                important_lines.append(line)

        # Fallback if no symbols found
        if not important_lines:
            important_lines = code.splitlines()[:20]

        snippet = "\n".join(important_lines[:30])  # Max 30 lines

        # Build markdown section
        markdown = f"""### FILE: {rel_path}
```tsx
{snippet}
```
"""
        processed_sections.append(markdown)

    return "\n\n".join(processed_sections)
