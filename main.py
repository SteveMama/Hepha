import requests
import json
import streamlit as st
from requests.exceptions import RequestException
import pandas as pd
from difflib import unified_diff
import base64
import openai
import os
import streamlit.components.v1 as components

openai.api_key = os.getenv("OPENAI_API_KEY")


class GitHubRepository:
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
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response
        except RequestException as e:
            st.error(f"Error occurred: {e}")
            return None

    def get_commit_history(self):
        commits_api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/commits"
        response = self.safe_request(commits_api_url)

        if response:
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

    def get_latest_commit_per_file(self):
        commits_api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/commits?per_page=100"
        response = self.safe_request(commits_api_url)

        if response:
            commits = response.json()
            file_commits = {}
            for commit in commits:
                sha = commit['sha']
                commit_details = self.safe_request(
                    f"https://api.github.com/repos/{self.owner}/{self.repo}/commits/{sha}")
                if commit_details:
                    commit_files = commit_details.json().get('files', [])
                    for file in commit_files:
                        filename = file['filename']
                        if filename not in file_commits:
                            file_commits[filename] = {
                                "sha": sha,
                                "message": commit['commit']['message'],
                                "patch": file.get('patch', 'No changes available')
                            }
            return file_commits
        return {}

    def get_file_content(self, file_path, commit_sha):
        file_api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/contents/{file_path}?ref={commit_sha}"
        response = self.safe_request(file_api_url)

        if response:
            file_data = response.json()
            if 'content' in file_data:
                return file_data['content'], file_data['encoding']
        return None, None

    def get_branches(self):
        branches_api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/branches"
        response = self.safe_request(branches_api_url)

        if response:
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

    def get_commit_diff(self, commit_sha):
        commit_api_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/commits/{commit_sha}"
        response = self.safe_request(commit_api_url)

        if response:
            commit_data = response.json()
            return commit_data.get('files', [])
        return []


def check_code(file_content):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert code reviewer and security analyst."},
            {"role": "user",
             "content": "Check the following code for missing docstrings, generate appropriate docstrings, and identify any vulnerabilities. "
                        "Return the updated code with docstrings. For vulnerabilities, return them in the following format at the end of the code:\n"
                        "\n# Vulnerabilities:\n"
                        "- Description of vulnerability 1\n"
                        "- Description of vulnerability 2\n\n" + file_content}
        ],
        temperature=0.2
    )
    return response['choices'][0]['message']['content']



def extract_vulnerability_details(updated_content):
    if "# Vulnerabilities:" in updated_content:
        vulnerabilities_section = updated_content.split("# Vulnerabilities:")[-1]
        vulnerabilities = vulnerabilities_section.strip().split("\n")
        vulnerabilities = [vuln.strip("- ") for vuln in vulnerabilities if vuln.strip()]
        return vulnerabilities
    return []



st.title("Hepha - The Github Blacksmith")
repo_url = st.text_input("Enter GitHub repository URL:")
access_token = st.text_input("Enter your GitHub personal access token:", type="password")

if 'repo' not in st.session_state:
    st.session_state['repo'] = None

if repo_url and access_token:
    if st.session_state['repo'] is None or st.session_state['repo'].repo_url != repo_url:
        st.session_state['repo'] = GitHubRepository(repo_url, access_token)

github_repo = st.session_state['repo']

if github_repo:
    tabs = st.tabs(
        ["Repo Evaluation", "Commit History & Comparison", "Branches", "Issues", "Pull Requests", "Contributors"])

    with tabs[0]:
        st.header("Repository Evaluation")
        file_commits = github_repo.get_latest_commit_per_file()
        if file_commits:
            selected_file = st.selectbox("Select a file to view latest commit:", list(file_commits.keys()))
            if selected_file:
                commit_info = file_commits[selected_file]
                st.write(f"**Latest Commit Message:** {commit_info['message']}")
                st.write(f"**Commit SHA:** {commit_info['sha']}")
                st.code(commit_info['patch'], language="diff")

                file_content, encoding = github_repo.get_file_content(selected_file, commit_info['sha'])
                if file_content:
                    st.write("### File Content:")
                    if encoding == 'base64':
                        file_content_decoded = base64.b64decode(file_content).decode('utf-8')

                        col1, col2 = st.columns(2)

                        with col1:
                            st.write("**Original File Content**")
                            st.code(file_content_decoded, language="python")

                        if st.button("Diagnose Code"):
                            updated_content = check_code(file_content_decoded)
                            with col2:
                                st.write("**Updated File with Docstrings**")
                                st.code(updated_content, language="python")

                            vulnerabilities = extract_vulnerability_details(updated_content)
                            if vulnerabilities:
                                st.write("### Identified Vulnerabilities:")
                                for vulnerability in vulnerabilities:
                                    st.write(vulnerability)
                            else:
                                st.write("No vulnerabilities identified.")
                else:
                    st.write("Unable to fetch file content.")
        else:
            st.write("No commits found.")

    with tabs[1]:
        st.header("Commit History")
        commit_df = github_repo.get_commit_history()
        if not commit_df.empty:
            st.dataframe(commit_df)
            st.write("Select commits to compare:")
            selected_commit_messages = st.multiselect("Select commits by message:", commit_df["Message"].tolist())
            if len(selected_commit_messages) == 2:
                selected_commits = commit_df[commit_df["Message"].isin(selected_commit_messages)]["SHA"].values.tolist()
                st.write(f"Comparing commits: {selected_commits[0]} and {selected_commits[1]}")
                commit_diffs_1 = github_repo.get_commit_diff(selected_commits[0])
                commit_diffs_2 = github_repo.get_commit_diff(selected_commits[1])

                files_to_compare = {file['filename']: file for file in commit_diffs_1}
                for file in commit_diffs_2:
                    if file['filename'] in files_to_compare:
                        st.write(f"### File: {file['filename']}")
                        patch_1 = files_to_compare[file['filename']]['patch']
                        patch_2 = file['patch']
                        diff = unified_diff(
                            patch_1.splitlines(),
                            patch_2.splitlines(),
                            fromfile=f"{selected_commits[0]} - {file['filename']}",
                            tofile=f"{selected_commits[1]} - {file['filename']}",
                            lineterm=''
                        )
                        diff_text = '\n'.join(diff)
                        st.code(diff_text, language="diff")
            else:
                st.write("Please select exactly two commits to compare.")
        else:
            st.write("No commits found.")

    with tabs[2]:
        st.header("Branches")
        branches = github_repo.get_branches()
        if branches:
            st.write(branches)
        else:
            st.write("No branches found.")

    with tabs[3]:
        st.header("Issues")
        issues_df = github_repo.get_issues()
        if not issues_df.empty:
            st.dataframe(issues_df)
        else:
            st.write("No issues found.")

    with tabs[4]:
        st.header("Pull Requests")
        pr_df = github_repo.get_pull_requests()
        if not pr_df.empty:
            st.dataframe(pr_df)
        else:
            st.write("No pull requests found.")

    with tabs[5]:
        st.header("Contributors")
        contributors_df = github_repo.get_contributors()
        if not contributors_df.empty:
            st.dataframe(contributors_df)
        else:
            st.write("No contributors found.")
