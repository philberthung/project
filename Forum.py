import streamlit as st
import time
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime

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
forum_collection = db.forum_posts
students_collection = db.students

# Fetch user info from session state
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("Please log in first.")
    st.switch_page("Login_Page.py")
    st.stop()

netid = st.session_state.get("netid", None)
role = st.session_state.role
permission = st.session_state.permission
user_data = students_collection.find_one({"netid": netid})
group = str(user_data.get("group", " ")) if user_data else " "

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

# Forum page
st.title("Forum")

# Tabs for Public and Group forums
tab1, tab2 = st.tabs(["Public Forum", "Group Forum"])

# --- Public Forum ---
with tab1:
    st.subheader("Public Forum")
    st.write("All users can post messages and GitHub links here.")

    # Post a message
    with st.form("public_form", clear_on_submit=True):
        public_message = st.text_area("Your Message")
        public_github = st.text_input("GitHub Link (optional)")
        submit_public = st.form_submit_button("Post")

        if submit_public and public_message:
            post = {
                "type": "public",
                "group": "",
                "netid": netid,
                "message": public_message,
                "github_link": public_github if public_github else "",
                "timestamp": datetime.now()
            }
            forum_collection.insert_one(post)
            st.success("Posted to Public Forum!")
            time.sleep(1)
            st.rerun()

    # Display public posts
    public_posts = list(forum_collection.find({"type": "public"}).sort("timestamp", -1))
    for post in public_posts:
        st.write(f"**{post['netid']}** ({post['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}):")
        st.write(post["message"])
        if post["github_link"]:
            st.write(f"[GitHub Link]({post['github_link']})")
        st.divider()

# --- Group Forum ---
with tab2:
    st.subheader(f"Group Forum (Group {group})")
    if group.strip() == "":
        st.warning("You are not assigned to a group yet.")
    else:
        st.write(f"Only members of Group {group} can post here.")

        # Post a message
        with st.form("group_form", clear_on_submit=True):
            group_message = st.text_area("Your Message")
            group_github = st.text_input("GitHub Link (optional)")
            submit_group = st.form_submit_button("Post")

            if submit_group and group_message:
                post = {
                    "type": "group",
                    "group": group,
                    "netid": netid,
                    "message": f"[Group {group}] {group_message}",
                    "github_link": group_github if group_github else "",
                    "timestamp": datetime.now()
                }
                forum_collection.insert_one(post)
                st.success(f"Posted to Group {group} Forum!")
                time.sleep(1)
                st.rerun()

        # Display group posts (only for user's group)
        group_posts = list(forum_collection.find({"type": "group", "group": group}).sort("timestamp", -1))
        for post in group_posts:
            st.write(f"**{post['netid']}** ({post['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}):")
            st.write(post["message"])
            if post["github_link"]:
                st.write(f"[GitHub Link]({post['github_link']})")
            st.divider()