import base64
import re
import logging
from typing import Dict, List, Any, Optional
import httpx
from app.config import settings

logger = logging.getLogger("github_service")
logging.basicConfig(level=logging.INFO)

class GitHubService:
    def __init__(self):
        self.headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "Agentic-GitHub-Portfolio-Reviewer"
        }
        token = settings.GITHUB_TOKEN.strip() if settings.GITHUB_TOKEN else ""
        if token and not token.startswith("YOUR_") and token != "YOUR_GITHUB_TOKEN_HERE":
            self.headers["Authorization"] = f"Bearer {token}"

    def extract_username(self, url_or_username: str) -> str:
        """
        Extracts the github username from a URL or returns the username itself.
        e.g., 'https://github.com/google' -> 'google'
        e.g., 'octocat' -> 'octocat'
        """
        cleaned = url_or_username.strip()
        # Regex to match github.com/<username> or just username
        match = re.search(r"(?:https?://)?(?:www\.)?github\.com/([^/]+)", cleaned)
        if match:
            return match.group(1)
        # Fallback if it's just the username (alphanumeric and dashes, up to 39 characters)
        return cleaned.split('/')[-1]

    async def fetch_portfolio_data(self, github_url: str) -> Dict[str, Any]:
        """
        Fetches all necessary data from GitHub API for a given profile URL.
        """
        username = self.extract_username(github_url)
        logger.info(f"Fetching GitHub data for user: {username}")
        
        async with httpx.AsyncClient(headers=self.headers, timeout=15.0) as client:
            # 1. Fetch Profile
            profile_url = f"https://api.github.com/users/{username}"
            profile_res = await client.get(profile_url)
            
            if profile_res.status_code == 404:
                raise ValueError(f"GitHub user '{username}' not found.")
            elif profile_res.status_code == 403:
                # Rate limited or forbidden
                limit_remaining = profile_res.headers.get("X-RateLimit-Remaining")
                if limit_remaining == "0":
                    raise Exception("GitHub API rate limit exceeded. Please configure GITHUB_TOKEN in your environment.")
                raise Exception(f"GitHub API returned 403: {profile_res.text}")
            elif profile_res.status_code != 200:
                raise Exception(f"Failed to fetch GitHub profile for {username}. Status code: {profile_res.status_code}")
                
            profile_data = profile_res.json()
            
            # 2. Fetch Repos
            repos_url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated"
            repos_res = await client.get(repos_url)
            repos_data = []
            if repos_res.status_code == 200:
                repos_data = repos_res.json()
            else:
                logger.warning(f"Failed to fetch repos for {username}. Code: {repos_res.status_code}")
            
            # Sort repos by popularity (stars + forks) to find top repositories for deep analysis
            sorted_repos = sorted(
                repos_data,
                key=lambda x: (x.get("stargazers_count", 0) + x.get("forks_count", 0)),
                reverse=True
            )
            
            # Select top 4 repos for detailed review
            top_repos = sorted_repos[:4]
            detailed_repos = []
            
            for repo in repos_data:
                repo_name = repo.get("name")
                is_top = repo in top_repos
                repo_info = {
                    "name": repo_name,
                    "description": repo.get("description"),
                    "html_url": repo.get("html_url"),
                    "stars": repo.get("stargazers_count", 0),
                    "forks": repo.get("forks_count", 0),
                    "language": repo.get("language"),
                    "size": repo.get("size", 0),
                    "created_at": repo.get("created_at"),
                    "updated_at": repo.get("updated_at"),
                    "is_top_repo": is_top,
                    "readme": "",
                    "recent_commits": []
                }
                
                # If it's a top repo, fetch README and commits
                if is_top:
                    # Fetch README
                    readme_url = f"https://api.github.com/repos/{username}/{repo_name}/readme"
                    readme_res = await client.get(readme_url)
                    if readme_res.status_code == 200:
                        readme_json = readme_res.json()
                        encoding = readme_json.get("encoding", "")
                        content_b64 = readme_json.get("content", "")
                        if encoding == "base64" and content_b64:
                            try:
                                # Clean up newlines in base64 before decoding
                                cleaned_content = content_b64.replace("\n", "").replace("\r", "")
                                decoded_readme = base64.b64decode(cleaned_content).decode("utf-8", errors="ignore")
                                # Truncate README if it is too long to prevent token issues
                                repo_info["readme"] = decoded_readme[:4000]
                            except Exception as e:
                                logger.error(f"Error decoding README for {repo_name}: {e}")
                                
                    # Fetch recent commits (last 5)
                    commits_url = f"https://api.github.com/repos/{username}/{repo_name}/commits?per_page=5"
                    commits_res = await client.get(commits_url)
                    if commits_res.status_code == 200:
                        commits_json = commits_res.json()
                        commits_list = []
                        for commit in commits_json:
                            commit_msg = commit.get("commit", {}).get("message", "")
                            commit_date = commit.get("commit", {}).get("author", {}).get("date", "")
                            commits_list.append({
                                "message": commit_msg,
                                "date": commit_date
                            })
                        repo_info["recent_commits"] = commits_list
                
                detailed_repos.append(repo_info)
                
            return {
                "username": username,
                "name": profile_data.get("name"),
                "bio": profile_data.get("bio"),
                "company": profile_data.get("company"),
                "blog": profile_data.get("blog"),
                "location": profile_data.get("location"),
                "followers": profile_data.get("followers", 0),
                "following": profile_data.get("following", 0),
                "public_repos_count": profile_data.get("public_repos", 0),
                "avatar_url": profile_data.get("avatar_url"),
                "html_url": profile_data.get("html_url"),
                "repositories": detailed_repos
            }

github_service = GitHubService()
