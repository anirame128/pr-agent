import re
import os
from typing import List, Dict, Set, Optional
from collections import defaultdict

class ProjectPatternAnalyzer:
    """Analyzes project structure and patterns from codebase context."""
    
    def __init__(self, codebase_context: str):
        self.codebase_context = codebase_context
        self.directory_patterns = self._extract_directory_patterns()
        self.naming_conventions = self._detect_naming_conventions()
        self.technology_patterns = self._detect_technology_patterns()
        self.package_managers = self._detect_package_managers()
    
    def _extract_directory_patterns(self) -> Dict[str, List[str]]:
        """Extract directory patterns from codebase context."""
        patterns = {
            'component_dirs': [],
            'source_dirs': [],
            'test_dirs': [],
            'config_dirs': [],
            'asset_dirs': []
        }
        
        # Extract file paths from context
        file_paths = re.findall(r'`([^`]+)`', self.codebase_context)
        file_paths.extend(re.findall(r'Path: ([^\n]+)', self.codebase_context))
        
        for path in file_paths:
            path_lower = path.lower().replace('\\', '/')
            parts = path_lower.split('/')
            
            # Detect component directories
            if any(part in ['components', 'component', 'ui', 'widgets'] for part in parts):
                patterns['component_dirs'].append(path)
            
            # Detect source directories
            if any(part in ['src', 'source', 'app', 'lib'] for part in parts):
                patterns['source_dirs'].append(path)
            
            # Detect test directories
            if any(part in ['test', 'tests', '__tests__', 'spec'] for part in parts):
                patterns['test_dirs'].append(path)
            
            # Detect config directories
            if any(part in ['config', 'conf', 'settings'] for part in parts):
                patterns['config_dirs'].append(path)
            
            # Detect asset directories
            if any(part in ['assets', 'static', 'public', 'images', 'styles'] for part in parts):
                patterns['asset_dirs'].append(path)
        
        return patterns
    
    def _detect_naming_conventions(self) -> Dict[str, str]:
        """Detect naming conventions from existing files."""
        conventions = {
            'components': 'unknown',
            'files': 'unknown',
            'directories': 'unknown'
        }
        
        # Extract filenames from context
        filenames = re.findall(r'([^/\\]+\.(?:tsx?|jsx?|py|java|go))', self.codebase_context)
        
        if not filenames:
            return conventions
        
        # Analyze component naming
        component_files = [f for f in filenames if any(ext in f for ext in ['.tsx', '.jsx', '.vue'])]
        if component_files:
            conventions['components'] = self._analyze_naming_pattern(component_files)
        
        # Analyze general file naming
        conventions['files'] = self._analyze_naming_pattern(filenames)
        
        # Analyze directory naming
        dirs = re.findall(r'([^/\\]+)/[^/\\]+\.', self.codebase_context)
        if dirs:
            conventions['directories'] = self._analyze_naming_pattern(dirs)
        
        return conventions
    
    def _analyze_naming_pattern(self, names: List[str]) -> str:
        """Analyze naming pattern from a list of names."""
        if not names:
            return 'unknown'
        
        patterns = {
            'pascal_case': 0,  # ComponentName
            'camel_case': 0,   # componentName
            'kebab_case': 0,   # component-name
            'snake_case': 0,   # component_name
            'lowercase': 0     # componentname
        }
        
        for name in names:
            clean_name = os.path.splitext(name)[0]  # Remove extension
            
            if clean_name[0].isupper() and '_' not in clean_name and '-' not in clean_name:
                patterns['pascal_case'] += 1
            elif clean_name[0].islower() and '_' not in clean_name and '-' not in clean_name:
                patterns['camel_case'] += 1
            elif '-' in clean_name:
                patterns['kebab_case'] += 1
            elif '_' in clean_name:
                patterns['snake_case'] += 1
            else:
                patterns['lowercase'] += 1
        
        # Return the most common pattern
        return max(patterns, key=patterns.get)
    
    def _detect_technology_patterns(self) -> Dict[str, Set[str]]:
        """Detect technology patterns from codebase context."""
        patterns = {
            'frameworks': set(),
            'libraries': set(),
            'build_tools': set(),
            'databases': set(),
            'apis': set()
        }
        
        context_lower = self.codebase_context.lower()
        
        # Framework detection
        framework_keywords = {
            'react': ['react', 'jsx', 'tsx', 'useState', 'useEffect'],
            'vue': ['vue', 'vuex', 'nuxt'],
            'angular': ['angular', 'ng-', '@angular'],
            'next': ['next', 'nextjs', 'next.js'],
            'svelte': ['svelte', 'sveltekit'],
            'express': ['express', 'expressjs'],
            'fastapi': ['fastapi', 'uvicorn'],
            'django': ['django', 'djangorest'],
            'flask': ['flask', 'flask-restful']
        }
        
        for framework, keywords in framework_keywords.items():
            if any(keyword in context_lower for keyword in keywords):
                patterns['frameworks'].add(framework)
        
        # Library detection
        library_keywords = {
            'axios': ['axios', 'http.get', 'http.post'],
            'fetch': ['fetch(', 'fetch('],
            'cheerio': ['cheerio', 'cheerio.load'],
            'puppeteer': ['puppeteer', 'page.goto'],
            'lodash': ['lodash', '_'],
            'moment': ['moment', 'moment('],
            'date-fns': ['date-fns'],
            'tailwind': ['tailwind', 'class="'],
            'bootstrap': ['bootstrap', 'btn-'],
            'material-ui': ['@mui', 'material-ui'],
            'antd': ['antd', 'ant-design']
        }
        
        for library, keywords in library_keywords.items():
            if any(keyword in context_lower for keyword in keywords):
                patterns['libraries'].add(library)
        
        # Build tool detection
        build_keywords = {
            'webpack': ['webpack', 'webpack.config'],
            'vite': ['vite', 'vite.config'],
            'rollup': ['rollup', 'rollup.config'],
            'parcel': ['parcel'],
            'esbuild': ['esbuild']
        }
        
        for tool, keywords in build_keywords.items():
            if any(keyword in context_lower for keyword in keywords):
                patterns['build_tools'].add(tool)
        
        # Database detection
        db_keywords = {
            'postgresql': ['postgres', 'postgresql', 'pg'],
            'mysql': ['mysql'],
            'sqlite': ['sqlite'],
            'mongodb': ['mongodb', 'mongoose'],
            'redis': ['redis'],
            'supabase': ['supabase'],
            'firebase': ['firebase']
        }
        
        for db, keywords in db_keywords.items():
            if any(keyword in context_lower for keyword in keywords):
                patterns['databases'].add(db)
        
        return patterns
    
    def _detect_package_managers(self) -> Set[str]:
        """Detect package managers from codebase context."""
        managers = set()
        context_lower = self.codebase_context.lower()
        
        manager_patterns = {
            'npm': ['package.json', 'npm install', 'npm run'],
            'yarn': ['yarn.lock', 'yarn add', 'yarn install'],
            'pnpm': ['pnpm-lock.yaml', 'pnpm add', 'pnpm install'],
            'pip': ['requirements.txt', 'pip install'],
            'poetry': ['pyproject.toml', 'poetry add'],
            'cargo': ['Cargo.toml', 'cargo add'],
            'go': ['go.mod', 'go get']
        }
        
        for manager, patterns in manager_patterns.items():
            if any(pattern in context_lower for pattern in patterns):
                managers.add(manager)
        
        return managers

class GeneralizedPlanParser:
    """Generalized plan parser that adapts to project patterns."""
    
    def __init__(self, codebase_context: str = ""):
        self.analyzer = ProjectPatternAnalyzer(codebase_context) if codebase_context else None
    
    def is_component_file(self, file_path: str) -> bool:
        """Determine if file is component based on project patterns."""
        if not self.analyzer:
            # No fallback - return False for truly generalized approach
            return False
        
        file_lower = file_path.lower().replace('\\', '/')
        
        # Check against discovered component directories
        for component_dir in self.analyzer.directory_patterns['component_dirs']:
            if component_dir.lower() in file_lower:
                return True
        
        # Check file extension and naming patterns
        if file_path.endswith(('.tsx', '.jsx', '.vue')):
            filename = os.path.basename(file_path)
            # Check if filename follows component naming convention
            if self.analyzer.naming_conventions['components'] == 'pascal_case':
                return filename[0].isupper() and '_' not in filename and '-' not in filename
            elif self.analyzer.naming_conventions['components'] == 'kebab_case':
                return '-' in filename and filename[0].islower()
        
        return False
    
    def validate_naming(self, filename: str, file_type: str = 'file') -> tuple[bool, str]:
        """Validate naming against discovered conventions."""
        if not self.analyzer:
            return True, ""
        
        clean_name = os.path.splitext(filename)[0]
        convention = self.analyzer.naming_conventions.get(file_type, 'unknown')
        
        if convention == 'unknown':
            return True, ""
        
        is_valid = False
        suggestion = ""
        
        if convention == 'pascal_case':
            is_valid = clean_name[0].isupper() and '_' not in clean_name and '-' not in clean_name
            if not is_valid:
                suggestion = f"Use PascalCase: {clean_name.title().replace('_', '').replace('-', '')}"
        elif convention == 'camel_case':
            is_valid = clean_name[0].islower() and '_' not in clean_name and '-' not in clean_name
            if not is_valid:
                suggestion = f"Use camelCase: {clean_name.lower().replace('_', '').replace('-', '')}"
        elif convention == 'kebab_case':
            is_valid = '-' in clean_name and clean_name[0].islower()
            if not is_valid:
                suggestion = f"Use kebab-case: {clean_name.lower().replace('_', '-')}"
        elif convention == 'snake_case':
            is_valid = '_' in clean_name and clean_name[0].islower()
            if not is_valid:
                suggestion = f"Use snake_case: {clean_name.lower().replace('-', '_')}"
        
        return is_valid, suggestion
    
    def detect_technologies(self, description: str) -> List[str]:
        """Detect technologies mentioned in description."""
        if not self.analyzer:
            # No fallback - return empty list for truly generalized approach
            return []
        
        detected_technologies = []
        description_lower = description.lower()
        
        # Check against all detected technology patterns
        for category, techs in self.analyzer.technology_patterns.items():
            for tech in techs:
                if tech.lower() in description_lower:
                    detected_technologies.append(tech)
        
        return detected_technologies
    
    def detect_dependencies(self, description: str) -> List[str]:
        """Detect dependency installation patterns."""
        if not self.analyzer:
            # No fallback - return empty list for truly generalized approach
            return []
        
        detected_deps = []
        description_lower = description.lower()
        
        # Check against detected package managers
        for manager in self.analyzer.package_managers:
            if manager in description_lower:
                detected_deps.append(f"{manager}_install")
        
        # Check for common dependency patterns
        if any(pattern in description_lower for pattern in ['install', 'add', 'require']):
            detected_deps.append('dependency_install')
        
        return detected_deps
    
    def generate_warnings(self, file_path: str, action: str, description: str) -> List[str]:
        """Generate context-aware warnings based on project patterns."""
        warnings = []
        
        if not self.analyzer:
            return warnings
        
        filename = os.path.basename(file_path)
        
        # Naming convention warnings
        is_valid, suggestion = self.validate_naming(filename, 'components' if self.is_component_file(file_path) else 'files')
        if not is_valid and suggestion:
            warnings.append(f"⚠️ Naming convention: {suggestion}")
        
        # Directory structure warnings
        if self.is_component_file(file_path):
            # Check if component is in appropriate directory
            file_lower = file_path.lower().replace('\\', '/')
            in_component_dir = any(dir_pattern.lower() in file_lower 
                                 for dir_pattern in self.analyzer.directory_patterns['component_dirs'])
            
            if not in_component_dir:
                warnings.append("⚠️ Consider placing components in a dedicated components directory")
        
        # Technology stack warnings
        detected_techs = self.detect_technologies(description)
        if detected_techs:
            # Check if detected technologies are consistent with project stack
            project_techs = set()
            for techs in self.analyzer.technology_patterns.values():
                project_techs.update(techs)
            
            for tech in detected_techs:
                if tech not in project_techs:
                    warnings.append(f"⚠️ Technology '{tech}' not detected in current project stack")
        
        return warnings

def parse_plan_generalized(plan_text: str, codebase_context: str = "") -> List[Dict[str, str]]:
    """Generalized plan parser that adapts to project patterns."""
    
    parser = GeneralizedPlanParser(codebase_context)
    steps = []
    
    raw_steps = re.findall(r"<step>(.*?)</step>", plan_text, re.DOTALL)
    
    for raw_step in raw_steps:
        action_match = re.search(r"<action>(.*?)</action>", raw_step, re.DOTALL)
        file_match = re.search(r"<file>(.*?)</file>", raw_step, re.DOTALL)
        desc_match = re.search(r"<description>(.*?)</description>", raw_step, re.DOTALL)
        
        if not (action_match and file_match and desc_match):
            continue
        
        action = action_match.group(1).strip().lower()
        file_path = file_match.group(1).strip()
        description = desc_match.group(1).strip()
        
        if action not in {"create", "modify", "delete"}:
            continue
        
        # Use generalized detection methods
        is_component = parser.is_component_file(file_path)
        technologies = parser.detect_technologies(description)
        dependencies = parser.detect_dependencies(description)
        warnings = parser.generate_warnings(file_path, action, description)
        
        steps.append({
            "action": action,
            "file": file_path,
            "description": description,
            "is_component": is_component,
            "technologies": technologies,
            "dependencies": dependencies,
            "warnings": warnings
        })
    
    return steps

