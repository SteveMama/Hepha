import pandas as pd
import requests
import json
from requests.exceptions import RequestException

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

    def safe_request(self, url):
        try:
           response = requests.get(url, headers = self.headers)
           response.raise_for_status()
           return response
        except RequestException as e:
            print(f"Error occured: {e}")
            return None

    def get_commit_history(self):
        commits_api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/commits"
        response = requests.get(commits_api_url, headers=self.headers)

        if response.status_code == 200:
            commits = response.json()
            commit_data = []
            for commit in commits:
                commit_data.append({
                    "Message": commit['commit']['message'],
                    "Author": commit['commit']['author']['name'],
                    "Date": commit['commit']['author']['date'],
                    "SHA": commit['sha']
                })
            return pd.DataFrame(commit_data)
        return pd.DataFrame()

    def get_commit_diff(self, commit_sha):
        diff_api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/commits/{commit_sha}"
        response = self.safe_request(diff_api_url)

        if response:
            commit = response.json()
            if 'files' in commit:
                diffs =[]
                for file in commit['files']:
                    diffs.append({
                        "filename": file['filename'],
                        "patch": file.get('patch', "No Changes Available")
                    })
                    return diffs
        return []

    def get_branches(self):
        branches_api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/branches"
        response = requests.get(branches_api_url, headers=self.headers)

        if response.status_code == 200:
            branches = response.json()
            branch_data = [branch['name'] for branch in branches]
            return branch_data
        return []


    def get_issues(self):
        issues_api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/issues"
        response = self.safe_request(issues_api_url)

        if response:
            issues = response.json()
            issue_data = []
            for issue in issues:
                labels = [label['name'] for label in issue['labels']]
                issue_data.append({
                    "Title": issue['title'],
                    "State": issue['state'],
                    "Labels": ', '.join(labels),
                    "Author": issue['user']['login']
                })
            return pd.DataFrame(issue_data)
        return pd.DataFrame()

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