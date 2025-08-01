import json
from typing import List

STACK_RULES = {
    "next": [
        "Do not access `localStorage` or `window` directly outside `useEffect`.",
        "Use `'use client'` in top-level files that use client-only state or effects.",
        "Prevent hydration mismatches using `suppressHydrationWarning` where needed."
    ],
    "tailwindcss": [
        "Use `dark:` variants for dark mode styling.",
        "Ensure responsive design using Tailwind's mobile-first utilities."
    ],
    "zustand": [
        "Zustand stores must be initialized outside React components.",
        "Use shallow comparison to avoid re-renders when subscribing to store slices."
    ],
    "react": [
        "Always use hooks inside function components or custom hooks.",
        "Avoid SSR-incompatible hooks or global state directly in root layout files."
    ]
}

def detect_stack_from_package_json(json_str: str) -> List[str]:
    pkg = json.loads(json_str)
    deps = pkg.get("dependencies", {})
    dev_deps = pkg.get("devDependencies", {})
    all_deps = {**deps, **dev_deps}
    return sorted([
        dep.lower() for dep in all_deps
        if any(core in dep for core in STACK_RULES.keys())
    ])

def generate_stack_knowledge_md(stack: List[str]) -> str:
    content = "# 📚 STACK_KNOWLEDGE.md\n\n"
    content += "This outlines tech-specific rules for this codebase.\n\n"
    for lib in stack:
        if lib in STACK_RULES:
            content += f"## 🧠 {lib}\n"
            for rule in STACK_RULES[lib]:
                content += f"- {rule}\n"
            content += "\n"
    return content
