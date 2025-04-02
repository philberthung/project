import streamlit as st
import time
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import requests
import pandas as pd
import os

# MongoDB connection
uri = "mongodb+srv://nata:isd2025@isdcluster.jnn9ctb.mongodb.net/?appName=ISDcluster"
client = MongoClient(uri, server_api=ServerApi('1'))

# Check connection
try:
    client.admin.command('ping')
except Exception as e:
    st.error(f"Could not connect to MongoDB: {e}")
    st.stop()

# Access database and collections
db = client.students_database
milestones_collection = db.milestones
students_collection = db.students

# Get user info from session state
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("Please log in first.")
    st.switch_page("Login_Page.py")
    st.stop()

netid = st.session_state.get("netid", None)
role = st.session_state.role
permission = st.session_state.permission

# GitHub API setup using environment variable
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    st.error("GitHub Token not configured. Please set it in system environment variables.")
    st.stop()

# Sidebar to display role and navigation
st.sidebar.title("User Role")
st.sidebar.write(f"Role: {st.session_state.role}")

# Logout button
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.permission = None
    st.session_state.netid = None
    st.switch_page("Login_Page.py")

# Get GitHub milestones list
def get_github_milestones(repo):
    url = f'https://api.github.com/repos/{repo}/milestones'
    response = requests.get(url, headers={'Authorization': f'token {GITHUB_TOKEN}', 'Accept': 'application/vnd.github.v3+json'})
    if response.status_code == 200:
        return {milestone['number']: milestone for milestone in response.json()}
    else:
        st.error(f"Failed to get GitHub milestones for {repo}: {response.status_code} - {response.text}")
        return {}

# Sync and delete milestones removed from GitHub
def sync_milestones():
    repo = "philberthung/project"  # Hardcoded repository
    github_milestones = get_github_milestones(repo)
    mongo_milestones = list(milestones_collection.find({"github_id": {"$exists": True}}))
    
    for mongo_milestone in mongo_milestones:
        github_id = mongo_milestone.get("github_id")
        if github_id is not None and github_id not in github_milestones:
            milestones_collection.delete_one({"_id": mongo_milestone["_id"]})
            st.success(f"Deleted milestone '{mongo_milestone['title']}' from MongoDB as it no longer exists on GitHub.")

# Execute sync
if 'last_sync' not in st.session_state:
    st.session_state.last_sync = datetime.now()
if (datetime.now() - st.session_state.last_sync).total_seconds() > 60:
    sync_milestones()
    st.session_state.last_sync = datetime.now()

# Milestones page
st.title("Milestones")

# --- Teacher Functionality ---
if role == "teacher":
    st.subheader("Manage Milestones")
    with st.form("milestone_form", clear_on_submit=True):
        title = st.text_input("Milestone Title")
        due_date = st.date_input("Due Date")
        description = st.text_area("Description")
        submit_milestone = st.form_submit_button("Add Milestone")

        if submit_milestone and title and due_date:
            milestone = {
                "title": title,
                "due_date": due_date.strftime("%Y-%m-%d"),
                "description": description,
                "created_by": netid,
                "timestamp": datetime.now(),
                "completions": {}
            }
            # Create milestone on GitHub
            repo = "philberthung/project"  # Hardcoded repository
            url = f'https://api.github.com/repos/{repo}/milestones'
            milestone_data = {
                'title': title,
                'description': description,
                'due_on': due_date.isoformat() + 'T00:00:00Z',
                'state': 'open',
            }
            response = requests.post(url, json=milestone_data, headers={'Authorization': f'token {GITHUB_TOKEN}', 'Accept': 'application/vnd.github.v3+json'})
            if response.status_code == 201:
                github_milestone = response.json()
                milestone["github_id"] = github_milestone.get("number")
                milestones_collection.insert_one(milestone)
                st.success(f"Created milestone on GitHub and MongoDB: {github_milestone['html_url']}")
            else:
                st.error(f"Failed to create milestone on GitHub: {response.text}")
            time.sleep(1)
            st.rerun()

# --- Display Milestones List ---
st.subheader("All Milestones")
milestones = list(milestones_collection.find().sort([("due_date", 1), ("timestamp", 1)]))
milestones_with_date = [m for m in milestones if m.get("due_date")]
milestones_without_date = [m for m in milestones if not m.get("due_date")]
sorted_milestones = milestones_with_date + milestones_without_date

if not sorted_milestones:
    st.write("No milestones available.")
else:
    for milestone in sorted_milestones:
        st.write(f"**{milestone['title']}** (Due: {milestone['due_date'] if milestone['due_date'] else 'Not set'}):")
        st.write(f"Description: {milestone['description'] if milestone['description'] else 'No description'}")
        st.write(f"Created by: {milestone['created_by']} ({milestone['timestamp'].strftime('%Y-%m-%d %H:%M:%S')})")
        if 'github_id' in milestone:
            st.write(f"GitHub Milestone ID: {milestone['github_id']}")

        # Student completion marking
        if role == "student":
            completed = milestone["completions"].get(netid, False)
            if st.checkbox(f"Mark as completed (by {netid})", value=completed, key=f"complete_{milestone['_id']}"):
                if not completed:
                    milestones_collection.update_one(
                        {"_id": milestone["_id"]},
                        {"$set": {f"completions.{netid}": True}}
                    )
                    st.success("Marked as completed!")
                    time.sleep(1)
                    st.rerun()
            elif completed:
                if st.button(f"Unmark completion (by {netid})", key=f"uncomplete_{milestone['_id']}"):
                    milestones_collection.update_one(
                        {"_id": milestone["_id"]},
                        {"$set": {f"completions.{netid}": False}}
                    )
                    st.success("Completion status removed!")
                    time.sleep(1)
                    st.rerun()

        # Teacher edit and delete options
        if role == "teacher":
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Edit", key=f"edit_{milestone['_id']}"):
                    with st.form(f"edit_form_{milestone['_id']}", clear_on_submit=True):
                        new_title = st.text_input("New title", value=milestone["title"])
                        new_due_date = st.date_input("New due date", value=datetime.strptime(milestone["due_date"], "%Y-%m-%d") if milestone["due_date"] else None)
                        new_description = st.text_area("New description", value=milestone["description"])
                        if st.form_submit_button("Save changes"):
                            milestones_collection.update_one(
                                {"_id": milestone["_id"]},
                                {"$set": {"title": new_title, "due_date": new_due_date.strftime("%Y-%m-%d") if new_due_date else None, "description": new_description}}
                            )
                            st.success("Milestone updated!")
                            time.sleep(1)
                            st.rerun()
            with col2:
                if st.button("Delete", key=f"delete_{milestone['_id']}"):
                    # Delete from GitHub if exists
                    if 'github_id' in milestone:
                        delete_url = f'https://api.github.com/repos/philberthung/project/milestones/{milestone["github_id"]}'
                        requests.delete(delete_url, headers={'Authorization': f'token {GITHUB_TOKEN}', 'Accept': 'application/vnd.github.v3+json'})
                    milestones_collection.delete_one({"_id": milestone["_id"]})
                    st.success("Milestone deleted!")
                    time.sleep(1)
                    st.rerun()

        # Show completion status (visible only to teachers)
        if role == "teacher":
            completed_users = [user for user, status in milestone["completions"].items() if status]
            st.write(f"Completed by: {', '.join(completed_users) if completed_users else 'No one'}")

        st.divider()