import os
import subprocess
import tempfile
import shutil
import uuid
import httpx
from typing import Dict

def extract_modified_files(sandbox, steps) -> Dict[str, str]:
    """
    Pulls all files that were created or modified in the sandbox.
    """
    modified = {}
    for step in steps:
        if step["action"] in ("create", "modify"):
            sandbox_path = f"/workspace/{step['file']}"
            try:
                content = sandbox.files.read(sandbox_path)
                modified[step["file"]] = content
            except Exception as e:
                print(f"⚠️ Failed to read modified file: {sandbox_path}\n{e}")
    return modified


def get_default_branch(repo_url: str, github_token: str) -> str:
    """Get the default branch for a repository using GitHub API."""
    owner, repo = repo_url.rstrip("/").split("/")[-2:]
    repo = repo.removesuffix(".git")
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json"
    }
    resp = httpx.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()["default_branch"]


def sync_and_commit_from_sandbox(
    repo_url: str,
    modified_files: Dict[str, str],
    branch_name: str,
    commit_message: str,
    github_token: str,
) -> str:
    """
    Clone the repo locally, apply modified files, commit and push to GitHub.
    Returns the local path to the synced repo.
    """
    temp_dir = tempfile.mkdtemp()
    print(f"📁 Cloning repo to temp dir: {temp_dir}")
    cwd = os.getcwd()

    try:
        authed_url = repo_url.replace("https://", f"https://{github_token}@")
        subprocess.run(["git", "clone", authed_url, temp_dir], check=True)

        os.chdir(temp_dir)
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)

        for rel_path, content in modified_files.items():
            full_path = os.path.join(temp_dir, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w") as f:
                f.write(content)

        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "push", "-u", "origin", branch_name], check=True)

        print("✅ Files committed and pushed")
        return temp_dir  # optionally return None and delete later
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"❌ Git command failed: {e}")
    finally:
        os.chdir(cwd)


async def create_pull_request(
    repo_url: str,
    branch_name: str,
    base_branch: str,
    pr_title: str,
    pr_body: str,
    github_token: str,
) -> str:
    """
    Create a pull request from the new branch using GitHub API.
    """
    owner, repo = repo_url.rstrip("/").split("/")[-2:]
    repo = repo.removesuffix(".git")

    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    payload = {
        "title": pr_title,
        "head": branch_name,
        "base": base_branch,
        "body": pr_body,
        "draft": False
    }

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(api_url, headers=headers, json=payload, timeout=30.0)
            resp.raise_for_status()
            return resp.json()["html_url"]
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            print(f"❌ PR creation failed with status {e.response.status_code}: {error_detail}")
            
            # Check if PR already exists
            if e.response.status_code == 422 and "already exists" in error_detail.lower():
                # Try to find existing PR
                list_url = f"{api_url}?head={owner}:{branch_name}&base={base_branch}"
                list_response = await client.get(list_url, headers=headers)
                if list_response.status_code == 200 and list_response.json():
                    existing_pr = list_response.json()[0]
                    pr_url = existing_pr["html_url"]
                    print(f"✅ Found existing PR: {pr_url}")
                    return pr_url
            
            raise RuntimeError(f"Failed to create pull request: {error_detail}")
        except Exception as e:
            print(f"❌ Unexpected error creating PR: {e}")
            raise 