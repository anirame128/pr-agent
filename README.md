# pr-agent
An AI agent that clones a Github repository and creates PRs based on natural language prompts

## Overview

PR Agent is an AI-powered tool that can:
- Clone any GitHub repository
- Analyze the codebase using AI
- Generate and apply code changes based on natural language prompts
- Create pull requests with the changes

## Prerequisites

Before running the agent locally, you'll need:

**API Keys** for the following services:
   - **E2B API Key** - For sandboxed code execution
   - **GitHub Token** - For repository access and PR creation
   - **Groq API Key** - For AI model inference

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/anirame128/pr-agent.git
```

### 2. Set Up Python Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory with the following variables:

```bash
# Required API Keys
E2B_API_KEY=your_e2b_api_key_here
GITHUB_TOKEN=your_github_token_here
GROQ_API_KEY=your_groq_api_key_here
```

#### Getting API Keys:

- **E2B API Key**: Sign up at [e2b.dev](https://e2b.dev) and get your API key
- **GitHub Token**: Create a personal access token at [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens) with `repo` permissions
- **Groq API Key**: Sign up at [groq.com](https://groq.com) and get your API key

### 4. Start the Server

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will start on `http://localhost:8000`

## Usage

### API Endpoint

The agent exposes a single endpoint:

**POST** `/code`

**Request Body:**
```json
{
  "repoUrl": "https://github.com/username/repository",
  "prompt": "Add a new feature that...",
  "enable_modifications": true
}
```

**Parameters:**
- `repoUrl` (required): The GitHub repository URL to clone and modify
- `prompt` (required): Natural language description of the changes you want
- `enable_modifications` (optional): Set to `true` to actually apply changes and create PRs

### Example Usage

```bash
curl -X POST http://localhost:8000/code \
  -H "Content-Type: application/json" \
  -d '{
    "repoUrl": "https://github.com/username/my-project",
    "prompt": "Add error handling to the login function",
    "enable_modifications": true
  }'
```

### Response

The API returns Server-Sent Events (SSE) with real-time updates:

```
event: update
data: 🔄 Cloning repository...

event: update
data: ✅ Repo cloned into sandbox

event: update
data: 🌳 Extracting file tree...

event: update
data: ✅ Found 45 files in repository

event: update
data: 🤖 Determining relevant files...

event: update
data: ✅ LLM selected 8 relevant files

event: update
data: 📖 Reading selected files...

event: update
data: ✅ Read 8 relevant files

event: update
data: 🔄 Lightly preprocessing files...

event: update
data: ✅ Lightly preprocessed files

event: update
data: 🤖 Generating plan...

event: update
data: ✅ Plan generated

event: update
data: 🔍 Parsing plan...

event: update
data: ✅ Parsed 3 steps from plan

event: update
data: 🔧 Applying plan steps...

event: update
data: ✅ Applied 2 changes

event: update
data: 📁 Downloading modified files for inspection...

event: update
data: ✅ Downloaded modified files to: ./downloads

event: update
data: 🔄 Syncing changes to repository...

event: update
data: ✅ Changes committed to branch: agent-changes-a1b2c3d4

event: update
data: 🔄 Creating pull request...

event: update
data: ✅ Pull request created: https://github.com/username/my-project/pull/123
```

## How It Works

1. **Repository Cloning**: The agent clones the target repository into an E2B sandbox
2. **Code Analysis**: It analyzes the codebase structure and identifies relevant files
3. **AI Planning**: Uses Groq AI to generate a detailed plan for the requested changes
4. **Code Modification**: Applies the changes in the sandbox environment
5. **Git Operations**: Creates a new branch, commits changes, and creates a pull request
6. **Cleanup**: Terminates the sandbox to reduce costs

## Development

### Project Structure

```
pr-agent/
├── backend/
│   ├── agent/
│   │   ├── agent_flow.py          # Main agent orchestration
│   │   ├── e2b_sandboxing/        # Sandbox management
│   │   ├── file_modification/      # Code modification logic
│   │   ├── git_commands/          # Git operations
│   │   ├── llm_plan/              # AI planning
│   │   └── preprocessing/          # Code preprocessing
│   ├── debug_output/              # Debug logs
│   ├── downloads/                 # Downloaded modified files
│   ├── main.py                    # FastAPI server
│   └── requirements.txt           # Python dependencies
└── frontend/                      # (Future frontend)
```

### Debug Output

The agent creates debug files in `backend/debug_output/`:
- `lightly_preprocessed_files.txt`: Processed codebase context
- `raw_plan.txt`: Raw AI-generated plan

Modified files are downloaded to `backend/downloads/` for inspection.

## Troubleshooting

### Common Issues

1. **E2B API Key Error**: Ensure your E2B API key is valid and has sufficient credits
2. **GitHub Token Error**: Verify your GitHub token has `repo` permissions
3. **Groq API Error**: Check your Groq API key and ensure you have sufficient quota
4. **Repository Access**: Ensure the repository is public or your GitHub token has access

### Logs

Check the console output for detailed logs. The agent provides real-time updates via SSE events.

## Security Notes

- Never commit your `.env` file to version control
- Use environment-specific API keys for development vs production
- The agent runs code in sandboxed environments, but always review generated changes
- GitHub tokens should have minimal required permissions
