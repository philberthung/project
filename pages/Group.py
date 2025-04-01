import streamlit as st
import pandas as pd
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# MongoDB connection
uri = "mongodb+srv://nata:isd2025@isdcluster.jnn9ctb.mongodb.net/?appName=ISDcluster"
client = MongoClient(uri, server_api=ServerApi('1'))

# Check connection
try:
    client.admin.command('ping')
    st.success("Connected to MongoDB!")
except Exception as e:
    st.error(f"Could not connect to MongoDB: {e}")

# Access the database and collection
db = client.students_database
students_collection = db.students

# Load student data
students_data = list(students_collection.find({}))
students_df = pd.DataFrame(students_data)

# Initialize session state for selected students and group
if 'selected_students' not in st.session_state:
    st.session_state.selected_students = []
if 'group_number' not in st.session_state:
    st.session_state.group_number = None

# Check if the user is logged in
if 'logged_in' in st.session_state and st.session_state.logged_in:
    # Get user permission and role from session state
    permission = st.session_state.permission
    role = st.session_state.role

    # Check if the user has permission to access the page
    if permission != 'leader':
        st.error("You do not have permission to access this page.")
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

    # Streamlit UI
    st.title("Student Group Selection")

    # Group selection
    group_number = st.selectbox("Select Group Number", options=[1, 2, 3, 4])  # Example group numbers
    st.session_state.group_number = group_number

    # Filter students based on the selected group and permissions
    group_students = students_df[students_df['group'] == group_number]  # Get students already in the selected group
    # Exclude teachers and leaders from available students
    available_students = students_df[
        (~students_df['email'].isin(st.session_state.selected_students)) &  # Exclude already selected students
        (~students_df['permission'].isin(['teacher', 'leader'])) &  # Exclude teachers and leaders
        (students_df['group'] != group_number)  # Exclude students already in the selected group
    ]

    # Allow user to select students
    selected_students = st.multiselect(
        "Choose students (max 4)",
        options=available_students['email'].tolist(),  # Use email as the option
        default=[]
    )

    if st.button("Add Students"):
        selected_emails = available_students[available_students['email'].isin(selected_students)]['email'].tolist()  # Get selected emails
        
        # Check if selected students are already in the group
        already_in_group = group_students['email'].tolist()
        new_selections = [email for email in selected_emails if email not in already_in_group]
        
        # Select new students
        for email in new_selections:
            if email not in st.session_state.selected_students and len(st.session_state.selected_students) < 4:
                st.session_state.selected_students.append(email)

        # Remove the selected emails from available students
        for email in selected_emails:
            available_students = available_students[available_students['email'] != email]
        
        if not new_selections:
            st.warning("No new students were selected. All selected students are already in the group.")
        else:
            st.success(f"Invited students: {new_selections}")

    # Display selected students
    st.subheader("Selected Students")
    if st.session_state.selected_students:
        selected_names = [str(email) for email in st.session_state.selected_students]
        st.write(", ".join(selected_names))
    else:
        st.write("No students selected.")
else:
    st.error("You must be logged in to access this page.")