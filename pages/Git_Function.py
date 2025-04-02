import streamlit as st
import requests
from datetime import datetime
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os

# MongoDB connection
uri = "mongodb+srv://nata:isd2025@isdcluster.jnn9ctb.mongodb.net/?appName=ISDcluster"
client = MongoClient(uri, server_api=ServerApi('1'))

# Check MongoDB connection
try:
    client.admin.command('ping')
except Exception as e:
    st.error(f"Could not connect to MongoDB: {e}")
    st.stop()

# Access MongoDB collection
db = client.students_database
milestones_collection = db.milestones

# Fetch user info from session state
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("Please log in first.")
    st.switch_page("Login_Page.py")
    st.stop()

netid = st.session_state.get("netid", None)
role = st.session_state.role

# GitHub API setup using system environment variable
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Get token from system environment variable
if not GITHUB_TOKEN:
    st.error("GitHub Token is not set. Please configure it in your system environment variables.")
    st.stop()

# Fixed list of team private repositories (replace with your team private repositories)
team_repositories = [
    "COMP3122-Group18/group-project-1-1743529716",  # Example team private repository 1
    "philberthung/project"  # Example team private repository 2 or individual repo
    # Add more team private repository names as needed
]

# Sidebar user role and logout
st.sidebar.title("User Role")
st.sidebar.write(f"Role: {st.session_state.role}")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.permission = None
    st.session_state.netid = None
    st.switch_page("Login_Page.py")

# Function to create a GitHub milestone and sync with MongoDB
def create_milestone(title, description, due_date, selected_repo):
    if not GITHUB_TOKEN:
        st.error("GitHub Token is not set. Please configure it in your system environment variables.")
        st.stop()
    
    url = f'https://api.github.com/repos/{selected_repo}/milestones'
    milestone_data = {
        'title': title,
        'description': description,
        'due_on': due_date.isoformat() + 'T00:00:00Z' if due_date else None,
        'state': 'open',
    }
    response = requests.post(url, json=milestone_data, headers={
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
    })
    
    if response.status_code == 201:  # Successfully created
        github_milestone = response.json()
        # Sync with MongoDB only if GitHub creation succeeds
        mongo_milestone = {
            "title": title,
            "due_date": due_date.strftime("%Y-%m-%d") if due_date else None,
            "description": description,
            "created_by": netid,
            "timestamp": datetime.now(),
            "completions": {},
            "github_id": github_milestone.get("number"),  # Store GitHub milestone ID for reference
            "repository": selected_repo
        }
        milestones_collection.insert_one(mongo_milestone)
        return {"success": True, "url": github_milestone["html_url"]}
    else:
        st.error(f"GitHub API Error: {response.status_code} - {response.text}")
        return {"success": False, "message": response.json().get("message", "Unknown error")}

# Function to create a GitHub issue
def create_issue(title, body, selected_repo):
    if not GITHUB_TOKEN:
        st.error("GitHub Token is not set. Please configure it in your system environment variables.")
        st.stop()
    
    url = f'https://api.github.com/repos/{selected_repo}/issues'
    issue_data = {
        'title': title,
        'body': body,
    }
    response = requests.post(url, json=issue_data, headers={
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
    })
    
    if response.status_code == 201:  # Successfully created
        return response.json()
    else:
        st.error(f"GitHub API Error: {response.status_code} - {response.text}")
        return {"message": response.json().get("message", "Unknown error")}

# Streamlit UI
st.title("GitHub Project Management")

# Create a Milestone section
st.header("Create a Milestone")
milestone_title = st.text_input("Milestone Title")
milestone_description = st.text_area("Milestone Description")
milestone_due_date = st.date_input("Due Date", value=None)  # Default value is None
selected_repo = st.selectbox("Select Repository", team_repositories, index=0, key="milestone_repo")
if st.button("Create Milestone"):
    if milestone_title:
        result = create_milestone(milestone_title, milestone_description, milestone_due_date, selected_repo)
        if result["success"]:
            st.success(f"Milestone created on GitHub and synced to MongoDB for {selected_repo}: {result['url']}")
        else:
            st.error(f"Failed to create Milestone: {result['message']}")
    else:
        st.error("Please enter a milestone title.")

st.markdown("---")  # Separator line

# Create an Issue section
st.header("Create an Issue")
issue_title = st.text_input("Issue Title", key='issue_title')
issue_body = st.text_area("Issue Body", key='issue_body')
selected_repo_issue = st.selectbox("Select Repository", team_repositories, index=0, key="issue_repo")
if st.button("Create Issue"):
    if issue_title:
        # Append the netid to the issue body to indicate the creator
        full_body = f"Created by: {netid}\n\n{issue_body}"
        result = create_issue(issue_title, full_body, selected_repo_issue)
        if 'html_url' in result:
            st.success(f"Issue created for {selected_repo_issue}: {result['html_url']}")
        else:
            st.error(f"Failed to create Issue: {result['message']}")
    else:
        st.error("Please enter an issue title.")