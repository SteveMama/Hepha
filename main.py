import requests
import json

def parse_github_url(repo_url):
    parts = repo_url.strip().rstrip("/").split("/")
    owner, repo = parts[-2], parts[-1]
    return owner, repo


def get_commit_history(repo_url, access_token):
    owner, repo = parse_github_url(repo_url)

    commits_api_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = requests.get(commits_api_url,headers = headers)

    if response.status_code == 200:
        commits = response.json()
        for commit in commits:
            print(f"Commit: {commit['commit']['message']}, Author: {commit['commit']['author']['name']}")

    else:
        print(f"Error: Unable to fetch commits. Status Code: {response.status_code}")


    print(response.json())


def get_branches(repo_url, access_token):
    owner, repo = parse_github_url(repo_url)

    branches_api_url = f"https://api.github.com/repos/{owner}/{repo}/branches"
    headers = {
        "Authorization": f"token{access_token}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = requests.get(branches_api_url, headers = headers)

    if response.status_code == 200:
        branches = response.json()
        for branch in branches:
            print(f"Branch: {branch['name']}")
    else:
        print(f"Error: Unable to fetch branches. Status Code: {response.status_code()}")

    print(response.json())

def get_issues(repo_url, access_token):
    owner, repo = parse_github_url(repo_url)

    issues_api_url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    headers = {
        "Authorization": f"token{access_token}",
        "Accept" : "application/vnd.github.v3+json"
    }

    response = requests.get(issues_api_url, headers = headers)

    if response.status_code == 200:
        issues = response.json()
        for issue in issues:
            print(f"Issue: {issue['title']}, State: {issue['state']}")
    else:
        print(f"Error:Unable to fetch issues. Status Code: {response.status_code}")

    print(response.json())


if __name__ == "__main__":
    repo_url = input("Enter GitHub repository URL: ")
    access_token = input("Enter your GitHub personal access token: ")

    print("\nCommit History:")
    get_commit_history(repo_url, access_token)

    print("\nBranch Information:")
    get_branches(repo_url, access_token)

    print("\nRepository Issues:")
    get_issues(repo_url, access_token)