import streamlit as st
import requests
from datetime import datetime
from pymongo import MongoClient
from pymongo.server_api import ServerApi

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

# GitHub API setup
GITHUB_TOKEN = ''  # Replace with your token
REPO = 'philberthung/project'  # Replace with your repository
headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json',
}

# Function to create a GitHub milestone and sync with MongoDB
def create_milestone(title, description, due_date):
    url = f'https://api.github.com/repos/{REPO}/milestones'
    milestone_data = {
        'title': title,
        'description': description,
        'due_on': due_date.isoformat() + 'T00:00:00Z' if due_date else None,
        'state': 'open',
    }
    response = requests.post(url, json=milestone_data, headers=headers)
    
    if response.status_code == 201:  # Successfully created
        github_milestone = response.json()
        # Sync with MongoDB
        mongo_milestone = {
            "title": title,
            "due_date": due_date.strftime("%Y-%m-%d") if due_date else None,
            "description": description,
            "created_by": netid,
            "timestamp": datetime.now(),
            "completions": {},
            "github_id": github_milestone.get("number")  # Store GitHub milestone ID for reference
        }
        milestones_collection.insert_one(mongo_milestone)
        return {"success": True, "url": github_milestone["html_url"]}
    else:
        return {"success": False, "message": response.json().get("message", "Unknown error")}

# Function to create a GitHub issue (copied from GIt_Function.py)
def create_issue(title, body):
    url = f'https://api.github.com/repos/{REPO}/issues'
    issue_data = {
        'title': title,
        'body': body,
    }
    response = requests.post(url, json=issue_data, headers=headers)
    return response.json()

# Streamlit UI
st.title("GitHub Project Management")

# Create a Milestone section
st.header("Create a Milestone")
milestone_title = st.text_input("Milestone Title")
milestone_description = st.text_area("Milestone Description")
milestone_due_date = st.date_input("Due Date", value=None)  # Default value is None
if st.button("Create Milestone"):
    if milestone_title:
        result = create_milestone(milestone_title, milestone_description, milestone_due_date)
        if result["success"]:
            st.success(f"Milestone created on GitHub and synced to MongoDB: {result['url']}")
        else:
            st.error(f"Error creating Milestone: {result['message']}")
    else:
        st.error("Please enter a milestone title.")

st.markdown("---")  # Separator line

# Create an Issue section (added from GIt_Function.py)
st.header("Create an Issue")
issue_title = st.text_input("Issue Title", key='issue_title')
issue_body = st.text_area("Issue Body", key='issue_body')
if st.button("Create Issue"):
    if issue_title:
        result = create_issue(issue_title, issue_body)
        if 'html_url' in result:
            st.success(f"Issue created: {result['html_url']}")
        else:
            st.error(f"Error creating Issue: {result.get('message', 'Unknown error')}")
    else:
        st.error("Please enter an issue title.")

# Sidebar logout
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.permission = None
    st.session_state.netid = None
    st.switch_page("Login_Page.py")