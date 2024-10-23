import requests
import json


class GithubRepo:
    def __init__(self, repo_url, access_token):
        self.repo_url = repo_url.strip().rstrip("/")
        self.access_token = access_token
        self.owner, self.repo = self._parse_github_url()
        self.headers = {
            "Authorization": f"token {self.access_token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def _parse_github_url(self):
        parts = self.repo_url.split("/")
        owner, repo = parts[-2], parts[-1]
        return owner, repo

    def get_commit_history(self):
        commits_api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/commits"
        response = requests.get(commits_api_url, headers=self.headers)

        if response.status_code == 200:
            commits = response.json()
            for commit in commits:
                print(f"Commit: {commit['commit']['message']}, Author: {commit['commit']['author']['name']}")
        else:
            print(f"Error: Unable to fetch commits. Status Code: {response.status_code}")

    def get_branches(self):
        branches_api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/branches"
        response = requests.get(branches_api_url, headers=self.headers)

        if response.status_code == 200:
            branches = response.json()
            for branch in branches:
                print(f"Branch: {branch['name']}")
        else:
            print(f"Error: Unable to fetch branches. Status Code: {response.status_code}")

    def get_issues(self):
        issues_api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/issues"
        response = requests.get(issues_api_url, headers=self.headers)

        if response.status_code == 200:
            issues = response.json()
            for issue in issues:
                print(f"Issue: {issue['title']}, State: {issue['state']}")
        else:
            print(f"Error: Unable to fetch issues. Status Code: {response.status_code}")

if __name__ == "__main__":
    repo_url = input("Enter GitHub repository URL: ")
    access_token = input("Enter your GitHub personal access token: ")

    github_repo = GithubRepo(repo_url, access_token)

    print("\nCommit History:")
    github_repo.get_commit_history(repo_url, access_token)

    print("\nBranch Information:")
    github_repo.get_branches(repo_url, access_token)

    print("\nRepository Issues:")
    github_repo.get_issues(repo_url, access_token)