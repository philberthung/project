import streamlit as st
import requests
from datetime import datetime

# Your GitHub personal access token
GITHUB_TOKEN=''
REPO = 'philberthung/project'  # Replace with your repository
BASE_BRANCH = 'main'  # The base branch for the pull request
HEAD_BRANCH = 'feature-branch'  # The branch you're merging from

# Set up headers for GitHub API requests
headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json',
}

# Function to create a pull request
def create_pull_request(title, body):
    url = f'https://api.github.com/repos/{REPO}/pulls'
    pr_data = {
        'title': title,
        'body': body,
        'head': HEAD_BRANCH,  # Specify the source branch
        'base': BASE_BRANCH,  # Specify the target branch
    }
    response = requests.post(url, json=pr_data, headers=headers)
    
    # Detailed debugging output
    print("Request Data:", pr_data)  # Show the data being sent
    print("Response Status Code:", response.status_code)
    print("Response JSON:", response.json())  # Show the response content
    return response.json()

# Function to create a GitHub issue
def create_issue(title, body):
    url = f'https://api.github.com/repos/{REPO}/issues'
    issue_data = {
        'title': title,
        'body': body,
    }
    response = requests.post(url, json=issue_data, headers=headers)
    return response.json()

# Function to create a milestone
def create_milestone(title, description, due_date):
    url = f'https://api.github.com/repos/{REPO}/milestones'
    milestone_data = {
        'title': title,
        'description': description,
        'due_on': due_date.isoformat() + 'T00:00:00Z' if due_date else None,
        'state': 'open',
    }
    response = requests.post(url, json=milestone_data, headers=headers)
    return response.json()

# Streamlit UI
st.title('GitHub Project Management')

st.header('Create a Milestone')
milestone_title = st.text_input('Milestone Title')
milestone_description = st.text_area('Milestone Description')
milestone_due_date = st.date_input('Due Date', value=None)  # Default value is None
if st.button('Create Milestone'):
    if milestone_title:
        result = create_milestone(milestone_title, milestone_description, milestone_due_date)
        if 'url' in result:
            st.success(f"Milestone created: {result['url']}")
        else:
            st.error(f"Error creating Milestone: {result.get('message', 'Unknown error')}")
    else:
        st.error('Please enter a milestone title.')

st.markdown("---")  # Separator line

st.header('Create an Issue')
issue_title = st.text_input('Issue Title', key='issue_title')
issue_body = st.text_area('Issue Body', key='issue_body')
if st.button('Create Issue'):
    if issue_title:
        result = create_issue(issue_title, issue_body)
        if 'html_url' in result:
            st.success(f"Issue created: {result['html_url']}")
        else:
            st.error(f"Error creating Issue: {result.get('message', 'Unknown error')}")
    else:
        st.error('Please enter an issue title.')

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.role = None  # Reset role
    st.rerun()  # Rerun to go back to the login page
