import requests
import json
import streamlit as st
from requests.exceptions import RequestException
import pandas as pd
from difflib import unified_diff

import requests
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

    def get_pull_requests(self):
        pr_api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/pulls"
        response = self.safe_request(pr_api_url)

        if response:
            pull_requests = response.json()
            pr_data = []
            for pr in pull_requests:
                pr_data.append({
                    "Title": pr['title'],
                    "State": pr['state'],
                    "Author": pr['user']['login']
                })
            return pd.DataFrame(pr_data)
        return pd.DataFrame()

    def get_contributors(self):
        contributors_api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/contributors"
        response = self.safe_request(contributors_api_url)

        if response:
            contributors = response.json()
            contributor_data = []
            for contributor in contributors:
                contributor_data.append({
                    "Contributor": contributor['login'],
                    "Contributions": contributor['contributions']
                })
            return pd.DataFrame(contributor_data)
        return pd.DataFrame()

st.title(" Hepha AI: Code Reviewer")
repo_url = st.text_input("Enter Github repo URL: ")
access_token= st.text_input("Enter your Github personal access token", type="password")

if repo_url and access_token:
    github_repo = GithubRepo(repo_url, access_token)
    st.header("Commit History")
    commit_df = github_repo.get_commit_history()
    if not commit_df.empty:
        st.dataframe(commit_df)
        st.write("Select commits to compare: ")
        selected_commits = st.multiselect("Select Commits by SHA: ", commit_df["SHA"].tolist())

        if len(selected_commits) == 2:
            st.write(f"compariing commits : {selected_commits[0]} and {selected_commits[1]}")
            commit_diffs_1 = github_repo.get_commit_diff(selected_commits[0])
            commit_diffs_2 = github_repo.get_commit_diff(selected_commits[1])

            for file1, file2 in zip(commit_diffs_1, commit_diffs_2):
                if file1['filename'] == file2['filename']:
                    st.write(f"### File: {file1['filename']}")
                    diff = unified_diff(
                        file1['patch'].splitlines(),
                        file2['patch'].splitlines(),
                        fromfile= f"{selected_commits[0]} - {file1['filename']}",
                        tofile=f"{selected_commits[1]} - {file2['filename']}",
                        lineterm=''
                    )
                    st.code('\n'.join(diff), language="diff")
        else:
            st.write("Please select exactly two commits to compare. ")
    else:
        st.write("No commits found. ")

    st.header("Branches")
    branches = github_repo.get_branches()
    if branches:
        st.write(branches)
    else:
        st.write("No branches found.")

    st.header("Issues")
    issues_df = github_repo.get_issues()
    if not issues_df.empty:
        st.dataframe(issues_df)
    else:
        st.write("No issues found.")

    st.header("Pull Requests")
    pr_df = github_repo.get_pull_requests()
    if not pr_df.empty:
        st.dataframe(pr_df)
    else:
        st.write("No pull requests found.")

    st.header("Contributors")
    contributors_df = github_repo.get_contributors()
    if not contributors_df.empty:
        st.dataframe(contributors_df)
    else:
        st.write("No contributors found.")