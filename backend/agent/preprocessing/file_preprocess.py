import os
import re
from typing import Dict, List

# Optional import for accurate token counting
try:
    import tiktoken
    tokenizer = tiktoken.encoding_for_model("gpt-4")
except ImportError:
    tokenizer = None

# Constants
MAX_FILE_LENGTH = 50000  # Fallback char-based skip
MAX_TOKENS_PER_FILE = 3000
IMPORTANT_EXTENSIONS = {
    '.ts', '.tsx', '.js', '.jsx', '.py', '.java', '.go', '.json', '.md'
}
IGNORE_PATTERNS = [
    '.test.', '__mocks__', 'mock', 'node_modules', 'dist', 'build', '.next'
]

PRIORITY_ORDER = [
    "API Route",
    "Authentication",
    "Dashboard Page",
    "Login Page",
    "Visualization",
    "Utilities",
    "Middleware",
    "Configuration",
    "Source Code",
    "Stylesheet",
    "Git Hook",
    "Test File",
    "Documentation"
]

def get_priority_score(path: str) -> int:
    """Return the priority score of the file type for sorting."""
    label = classify_file(path)
    try:
        return PRIORITY_ORDER.index(label)
    except ValueError:
        return len(PRIORITY_ORDER)
    
def classify_file(path: str) -> str:
    path_lower = path.lower()
    if "test" in path_lower or ".test." in path_lower or "_test" in path_lower:
        return "Test File"
    if "login" in path_lower:
        return "Login Page"
    if "dashboard" in path_lower:
        return "Dashboard Page"
    if "api" in path_lower:
        return "API Route"
    if "auth" in path_lower:
        return "Authentication"
    if "hooks/" in path_lower:
        return "Git Hook"
    if "charts/" in path_lower:
        return "Visualization"
    if path.endswith(('.env', '.env.local', '.env.production')):
        return "Configuration"
    if path.endswith(('.json', '.config.js', '.config.ts')):
        return "Configuration"
    if path.endswith(('.css', '.scss')):
        return "Stylesheet"
    if path.endswith('.md'):
        return "Documentation"
    if "utils" in path_lower or "helper" in path_lower:
        return "Utilities"
    if "middleware" in path_lower:
        return "Middleware"
    return "Source Code"

def extract_summary(code: str, max_lines: int = 20) -> str:
    lines = code.strip().splitlines()
    summary_lines = []
    in_multiline_comment = False
    
    for i, line in enumerate(lines[:max_lines]):
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            continue
            
        # Check for multiline comment start/end
        if '/**' in stripped or '/*' in stripped:
            in_multiline_comment = True
            summary_lines.append(line.strip())
            continue
            
        if '*/' in stripped and in_multiline_comment:
            in_multiline_comment = False
            summary_lines.append(line.strip())
            continue
            
        # If in multiline comment, include the line
        if in_multiline_comment:
            summary_lines.append(line.strip())
            continue
            
        # Check for single-line comments
        if stripped.startswith(('//', '#', '"""', "'''")):
            summary_lines.append(line.strip())
        # Check for JSDoc-style comments
        elif stripped.startswith('*') and any(tag in stripped for tag in ['@param', '@returns', '@description', '@example']):
            summary_lines.append(line.strip())
        # Check for function/class docstrings (first occurrence)
        elif stripped.startswith('def ') or stripped.startswith('class ') or stripped.startswith('function ') or stripped.startswith('export '):
            # Look for docstring in the next few lines
            for j in range(i+1, min(i+5, len(lines))):
                doc_line = lines[j].strip()
                if doc_line.startswith('"""') or doc_line.startswith("'''") or doc_line.startswith('//'):
                    summary_lines.append(f"// {doc_line}")
                    break
            break
        else:
            # Stop at first non-comment code
            break
            
    return '\n'.join(summary_lines).strip()

def extract_imports(path: str, content: str) -> List[str]:
    """Parse import statements to find local file dependencies."""
    imports = []
    ext = os.path.splitext(path)[-1]
    if ext not in {'.ts', '.tsx', '.js', '.jsx', '.py'}:
        return imports

    for line in content.splitlines():
        line = line.strip()
        if line.startswith("import") or line.startswith("from"):
            match = re.search(r'(?:from|import)\s+[\'"](.+?)[\'"]', line)
            if match:
                import_path = match.group(1)
                if import_path.startswith("."):
                    imports.append(import_path)  # Will resolve later
    return imports

def estimate_tokens(text: str) -> int:
    if tokenizer:
        return len(tokenizer.encode(text))
    else:
        # Fallback: average 4 characters per token (rough for English/code)
        return int(len(text) / 4)

def should_include_file(path: str, content: str) -> bool:
    if any(p in path for p in IGNORE_PATTERNS):
        return False
    if len(content) > MAX_FILE_LENGTH:
        return False
    if estimate_tokens(content) > MAX_TOKENS_PER_FILE:
        return False
    # Optionally skip test files to reduce context size
    if classify_file(path) == "Test File":
        return False
    ext = os.path.splitext(path)[-1]
    return ext in IMPORTANT_EXTENSIONS

def extract_dependencies(content: str) -> List[str]:
    """Extract all import statements to show file dependencies."""
    dependencies = re.findall(r'(?:import|from)\s+([a-zA-Z0-9_\.]+)', content)
    # Remove duplicates and sort
    return sorted(list(set(dependencies)))

def build_file_block(path: str, content: str) -> str:
    label = classify_file(path)
    summary = extract_summary(content)
    symbols = extract_code_symbols(path, content)
    dependencies = extract_dependencies(content)
    rel_path = path.replace('/workspace/', '')
    ext = os.path.splitext(path)[-1][1:] or "txt"
    block = f"📁 FILE: {rel_path}\n🏷️ TYPE: {label}"
    if summary:
        block += f"\n📝 SUMMARY:\n{summary}"
    if symbols:
        symbol_catalog_text = "\n".join(f"  - {s}" for s in symbols)
        block += f"\n🔣 SYMBOLS:\n{symbol_catalog_text}"
    if dependencies:
        deps_text = "\n".join(f"  - {dep}" for dep in dependencies)
        block += f"\n🌐 DEPENDENCIES:\n{deps_text}"
    block += f"\n🔢 TOKENS: {estimate_tokens(content)}"
    block += f"\n📄 CONTENT:\n```{ext}\n{content.strip()}\n```\n"
    return block

def extract_route_map(code_map: Dict[str, str]) -> List[str]:
    """Extract route mappings from app and API file paths."""
    routes = []
    for path in code_map:
        if "/app/" in path:
            route_path = path.split("/app/")[-1]
            route_path = re.sub(r"/page\.(tsx|ts|jsx|js)$", "", route_path)
            route_path = re.sub(r"/route\.(ts|js)$", "", route_path)
            if route_path == "":
                route_path = "/"
            else:
                route_path = "/" + route_path.replace("/page", "").replace("/route", "")
            routes.append(f"{route_path} → {path.replace('/workspace/', '')}")
    return sorted(routes)

def extract_code_symbols(path: str, content: str) -> List[str]:
    """Extract key symbols like functions, components, classes."""
    symbols = []
    ext = os.path.splitext(path)[-1]
    lines = content.splitlines()

    for i, line in enumerate(lines):
        line = line.strip()
        if ext in ['.ts', '.tsx', '.js', '.jsx']:
            if re.match(r'^export (function|const|async function) ', line):
                name_match = re.search(r'(function|const)\s+(\w+)', line)
                if name_match:
                    symbols.append(f"function {name_match.group(2)}(...)")
            elif re.match(r'^export default function ', line):
                symbols.append("function default(...)")
            elif 'interface ' in line and 'export' in line:
                name_match = re.search(r'interface (\w+)', line)
                if name_match:
                    symbols.append(f"interface {name_match.group(1)}")
            elif re.match(r'^const \w+ = \(', line) and '=>' in lines[i+1] if i+1 < len(lines) else '':
                name_match = re.search(r'const (\w+)', line)
                if name_match:
                    symbols.append(f"function {name_match.group(1)}")
        elif ext == '.py':
            if line.startswith("def ") or line.startswith("class "):
                symbols.append(line)

    return symbols

def infer_tech_stack(code_map: Dict[str, str]) -> List[str]:
    """Infer tech stack based on known file patterns and dependencies."""
    stack = set()

    # Analyze dependencies in package.json
    package_json = code_map.get('/workspace/user-profile-app/package.json') or code_map.get('package.json')
    if package_json:
        pkg = package_json.lower()
        if 'next' in pkg:
            stack.add('Next.js')
        if 'react' in pkg:
            stack.add('React')
        if 'tailwind' in pkg:
            stack.add('Tailwind CSS')
        if 'chart.js' in pkg:
            stack.add('Chart.js')
        if 'supabase' in pkg:
            stack.add('Supabase')

    # Analyze tsconfig for language
    tsconfig = code_map.get('/workspace/user-profile-app/tsconfig.json') or code_map.get('tsconfig.json')
    if tsconfig:
        stack.add('TypeScript')

    # Check README.md for keywords
    readme = code_map.get('/workspace/README.md') or code_map.get('README.md')
    if readme:
        content = readme.lower()
        if 'postgres' in content:
            stack.add('PostgreSQL')
        if 'forecast' in content or 'holt-winters' in content:
            stack.add('Holt-Winters Forecasting')
        if 'supabase' in content:
            stack.add('Supabase')
        if 'tailwind' in content:
            stack.add('Tailwind CSS')

    return sorted(stack)

def preprocess_codebase(code_map: Dict[str, str]) -> str:
    file_blocks: List[str] = []
    total_chars = 0
    total_tokens = 0
    skipped_files = []
    route_map = extract_route_map(code_map)
    route_summary = "🗺️ ROUTE MAP:\n" + "\n".join(f"- {r}" for r in route_map) + "\n"
    tech_stack = infer_tech_stack(code_map)
    tech_summary = "💻 TECH STACK:\n" + ", ".join(tech_stack) + "\n"
    
    # Create mapping of relative import paths to absolute file paths
    path_map = {path.replace('/workspace/', '').replace('\\', '/'): path for path in code_map}
    
    # Build the dependency graph
    dependency_graph: Dict[str, List[str]] = {}
    
    symbol_index: Dict[str, List[str]] = {}

    sorted_files = sorted(code_map.items(), key=lambda item: get_priority_score(item[0]))
    for path, content in sorted_files:
        if should_include_file(path, content):
            rel_path = path.replace('/workspace/', '').replace('\\', '/')
            
            # Resolve imports to known files
            raw_imports = extract_imports(path, content)
            resolved_imports = []

            for imp in raw_imports:
                base_path = os.path.dirname(rel_path)
                possible = os.path.normpath(os.path.join(base_path, imp)).replace('\\', '/')
                
                # Try adding .ts/.tsx/.js/.jsx/.py extension if missing
                for ext in ['.ts', '.tsx', '.js', '.jsx', '.py']:
                    full_path = f"{possible}{ext}"
                    if full_path in path_map:
                        resolved_imports.append(full_path)
                        break

            if resolved_imports:
                dependency_graph[rel_path] = resolved_imports
            
            # Extract symbols for summary
            symbols = extract_code_symbols(path, content)
            if symbols:
                symbol_index[path.replace("/workspace/", "")] = symbols
            
            block = build_file_block(path, content)
            file_blocks.append(block)
            total_chars += len(content)
            total_tokens += estimate_tokens(content)
        else:
            skipped_files.append(path)

    symbol_summary = "🧩 FUNCTION & INTERFACE INDEX:\n"
    for path, symbols in symbol_index.items():
        symbol_summary += f"- {path}:\n"
        for s in symbols:
            symbol_summary += f"    - {s}\n"

    dep_summary = "🔗 FILE DEPENDENCY GRAPH:\n"
    for src, deps in dependency_graph.items():
        dep_summary += f"- {src} → {', '.join(deps)}\n"

    summary = (
        f"📦 TOTAL FILES INCLUDED: {len(file_blocks)}\n"
        f"📄 TOTAL CHARACTERS: {total_chars}\n"
        f"🔢 TOTAL TOKENS: {total_tokens}\n"
        f"💻 TECH STACK: {', '.join(tech_stack)}\n"
        f"🚫 SKIPPED FILES: {len(skipped_files)}\n"
    )

    result = summary + "\n" + route_summary + "\n" + symbol_summary + "\n" + dep_summary + "\n---\n" + "\n---\n".join(file_blocks)
    return result
