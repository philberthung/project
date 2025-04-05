import streamlit as st
import requests
from datetime import datetime
import os

# Your GitHub personal access token
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
# Fixed list of repositories
REPOSITORIES = [
    "COMP3122-Group18/github-classroom-project-team-1",
    "COMP3122-Group18/github-classroom-project-team-2",
    "COMP3122-Group18/github-classroom-project-team-3"
]

# Set up headers for GitHub API requests
headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json',
}

# Function to create a pull request
def create_pull_request(title, body, selected_repo, head, base):
    url = f'https://api.github.com/repos/{selected_repo}/pulls'
    pr_data = {
        'title': title,
        'body': body,
        'head': head,  # Specify the source branch
        'base': base,  # Specify the target branch
    }
    response = requests.post(url, json=pr_data, headers=headers)
    
    # Detailed debugging output
    print("Request Data:", pr_data)  # Show the data being sent
    print("Response Status Code:", response.status_code)
    print("Response JSON:", response.json())  # Show the response content
    return response.json()

# Function to create a GitHub issue
def create_issue(title, body, selected_repo):
    url = f'https://api.github.com/repos/{selected_repo}/issues'
    issue_data = {
        'title': title,
        'body': body,
    }
    response = requests.post(url, json=issue_data, headers=headers)
    
    # Debugging output
    print("Request URL:", url)
    print("Request Headers:", headers)
    print("Request Data:", issue_data)
    print("Response Status Code:", response.status_code)
    print("Response JSON:", response.json())
    
    return response.json()

# Function to create a milestone
def create_milestone(title, description, due_date, selected_repo):
    url = f'https://api.github.com/repos/{selected_repo}/milestones'
    milestone_data = {
        'title': title,
        'description': description,
        'due_on': due_date.isoformat() + 'T00:00:00Z' if due_date else None,
        'state': 'open',
    }
    response = requests.post(url, json=milestone_data, headers=headers)
    return response.json()

# Streamlit UI
st.title('Activity Creation')

# Dropdown for selecting activity type
activity_type = st.selectbox(
    "Select Activity Type",
    ("Create Issue","Create Milestone","Create a Pull Request")
)

if activity_type == "Create Issue":
    st.header('Create an Issue')
    issue_title = st.text_input('Issue Title', key='issue_title')
    issue_body = st.text_area('Issue Body', key='issue_body')
    selected_repo_issue = st.selectbox("Select Repository", REPOSITORIES, index=0, key="issue_repo")
    if st.button('Create Issue'):
        if issue_title:
            result = create_issue(issue_title, issue_body, selected_repo_issue)
            if 'html_url' in result:
                st.success(f"Issue created for {selected_repo_issue}: {result['html_url']}")
            else:
                st.error(f"Error creating Issue: {result.get('message', 'Unknown error')}")
        else:
            st.error('Please enter an issue title.')

elif activity_type == "Create Milestone":
    st.header('Create a Milestone')
    milestone_title = st.text_input('Milestone Title')
    milestone_description = st.text_area('Milestone Description')
    milestone_due_date = st.date_input('Due Date', value=None)  # Default value is None
    selected_repo_milestone = st.selectbox("Select Repository", REPOSITORIES, index=0, key="milestone_repo")
    if st.button('Create Milestone'):
        if milestone_title:
            result = create_milestone(milestone_title, milestone_description, milestone_due_date, selected_repo_milestone)
            if 'url' in result:
                st.success(f"Milestone created for {selected_repo_milestone}: {result['url']}")
            else:
                st.error(f"Error creating Milestone: {result.get('message', 'Unknown error')}")
        else:
            st.error('Please enter a milestone title.')

elif activity_type =='Create a Pull Request':
    st.header('Create a Pull Request')
    pr_title = st.text_input('Pull Request Title', key='pr_title')
    pr_body = st.text_area('Pull Request Body', key='pr_body')
    selected_repo_pr = st.selectbox("Select Repository", REPOSITORIES, index=0, key="pr_repo")
    head_branch = st.text_input("Source Branch (head)", value="feature-branch")
    base_branch = st.text_input("Target Branch (base)", value="main")
    if st.button('Create Pull Request'):
        if pr_title:
            result = create_pull_request(pr_title, pr_body, selected_repo_pr, head_branch, base_branch)
            if 'html_url' in result:
                st.success(f"Pull Request created for {selected_repo_pr}: {result['html_url']}")
            else:
                st.error(f"Error creating Pull Request: {result.get('message', 'Unknown error')}")
        else:
            st.error('Please enter a pull request title.')

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.role = None  # Reset role
    st.rerun()  # Rerun to go back to the login page