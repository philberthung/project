import streamlit as st
import time
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
import requests
import pandas as pd

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

# Fetch user info from session state
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("Please log in first.")
    st.switch_page("Login_Page.py")
    st.stop()

netid = st.session_state.get("netid", None)
role = st.session_state.role
permission = st.session_state.permission

# GitHub API setup
GITHUB_TOKEN = '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'  # Replace with your token
REPO = 'philberthung/project'  # Replace with your repository
headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json',
}

# Get GitHub milestones list
def get_github_milestones():
    url = f'https://api.github.com/repos/{REPO}/milestones'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return {milestone['number']: milestone for milestone in response.json()}
    else:
        st.error(f"Failed to retrieve GitHub milestones: {response.status_code} - {response.text}")
        return {}

# Sync and delete milestones removed from GitHub
def sync_milestones():
    github_milestones = get_github_milestones()
    mongo_milestones = list(milestones_collection.find({"github_id": {"$exists": True}}))
    
    for mongo_milestone in mongo_milestones:
        github_id = mongo_milestone.get("github_id")
        if github_id is not None and github_id not in github_milestones:
            milestones_collection.delete_one({"_id": mongo_milestone["_id"]})
            st.success(f"Deleted milestone '{mongo_milestone['title']}' from MongoDB as it no longer exists on GitHub.")

# Perform synchronization (e.g., check every 60 seconds)
if 'last_sync' not in st.session_state:
    st.session_state.last_sync = datetime.now()
if (datetime.now() - st.session_state.last_sync).total_seconds() > 60:
    sync_milestones()
    st.session_state.last_sync = datetime.now()

# Milestones page
st.title("Milestones")

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

# --- Teacher Functions ---
if role == "teacher":
    st.subheader("Manage Milestones")
    with st.form("milestone_form", clear_on_submit=True):
        title = st.text_input("Milestone Name")
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
            milestones_collection.insert_one(milestone)
            st.success("Milestone added successfully!")
            time.sleep(1)
            st.rerun()

# --- Display Milestones List ---
st.subheader("All Milestones")
# Sort by due_date (ascending, nearest at top), with timestamp as secondary sort, then separate no-date milestones
milestones = list(milestones_collection.find().sort([("due_date", 1), ("timestamp", 1)]))
# Filter milestones with a due date
milestones_with_date = [m for m in milestones if m.get("due_date")]
# Filter milestones without a due date
milestones_without_date = [m for m in milestones if not m.get("due_date")]

# Combine lists: milestones with dates (near to far), followed by those without dates
sorted_milestones = milestones_with_date + milestones_without_date

if not sorted_milestones:
    st.write("No milestones available at the moment.")
else:
    for milestone in sorted_milestones:
        st.write(f"**{milestone['title']}** (Due Date: {milestone['due_date'] if milestone['due_date'] else 'Not set'})")
        st.write(f"Description: {milestone['description'] if milestone['description'] else 'No description'}")
        st.write(f"Created by: {milestone['created_by']} ({milestone['timestamp'].strftime('%Y-%m-%d %H:%M:%S')})")
        if 'github_id' in milestone:
            st.write(f"GitHub Milestone ID: {milestone['github_id']}")

        # Student completion marking
        if role == "student":
            completed = milestone["completions"].get(netid, False)
            if st.checkbox(f"Mark as Completed (by {netid})", value=completed, key=f"complete_{milestone['_id']}"):
                if not completed:
                    milestones_collection.update_one(
                        {"_id": milestone["_id"]},
                        {"$set": {f"completions.{netid}": True}}
                    )
                    st.success("Marked as completed!")
                    time.sleep(1)
                    st.rerun()
            elif completed:
                if st.button(f"Unmark Completion (by {netid})", key=f"uncomplete_{milestone['_id']}"):
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
                        new_title = st.text_input("New Name", value=milestone["title"])
                        new_due_date = st.date_input("New Due Date", value=datetime.strptime(milestone["due_date"], "%Y-%m-%d") if milestone["due_date"] else None)
                        new_description = st.text_area("New Description", value=milestone["description"])
                        if st.form_submit_button("Save Changes"):
                            milestones_collection.update_one(
                                {"_id": milestone["_id"]},
                                {"$set": {"title": new_title, "due_date": new_due_date.strftime("%Y-%m-%d") if new_due_date else None, "description": new_description}}
                            )
                            st.success("Milestone updated!")
                            time.sleep(1)
                            st.rerun()
            with col2:
                if st.button("Delete", key=f"delete_{milestone['_id']}"):
                    milestones_collection.delete_one({"_id": milestone["_id"]})
                    st.success("Milestone deleted!")
                    time.sleep(1)
                    st.rerun()

        # Display completion status (visible to teachers only)
        if role == "teacher":
            completed_users = [user for user, status in milestone["completions"].items() if status]
            st.write(f"Completed by: {', '.join(completed_users) if completed_users else 'No one has completed'}")

        st.divider()