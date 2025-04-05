import streamlit as st
import requests
import os
import json
from dotenv import load_dotenv
from datetime import datetime, time
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import pandas as pd

# Load environment variables
load_dotenv()

# MongoDB connection
uri = "mongodb+srv://nata:isd2025@isdcluster.jnn9ctb.mongodb.net/?appName=ISDcluster"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client.students_database

# GitHub Classroom setup
CLASSROOM_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"Bearer {CLASSROOM_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

# generic function to handle API calls
def safe_api_call(url, description="data"):
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.HTTPError as errh:
        st.error(f"HTTP Error ({description}): {errh}")
    except requests.exceptions.ConnectionError as errc:
        st.error(f"Connection Error ({description}): {errc}")
    except requests.exceptions.Timeout as errt:
        st.error(f"Timeout Error ({description}): {errt}")
    except requests.exceptions.RequestException as err:
        st.error(f"Request Error ({description}): {err}")
    except Exception as e:
        st.error(f"Unexpected error fetching {description}: {str(e)}")
    return None

# Fetch list of classrooms from GitHub Classroom API
def list_classrooms():
    classrooms = safe_api_call(
        "https://api.github.com/classrooms",
        "classrooms"
    )
    if classrooms:
        for classroom in classrooms:
            classroom.setdefault('name', 'Unnamed Classroom')
            classroom.setdefault('id', '')
        return classrooms
    
    return None

# Fetch assignments for a specific classroom
def list_assignments(classroom_id):
    if classroom_id:
        assignments = safe_api_call(
            f"https://api.github.com/classrooms/{classroom_id}/assignments",
            f"assignments for classroom {classroom_id}"
        )
        
        if assignments:
            print("\n", assignments)
            for assignment in assignments:
                assignment.setdefault('title', 'Untitled Assignment')
                assignment.setdefault('id', '')
                assignment.setdefault('deadline', 'No deadline')
                assignment['classroom'].get('url', '#')
                assignment.setdefault('invite_link', '#')
        
    else:
        st.error("No classroom ID provided")
        
    if assignments:
        return assignments
    else:
        st.error("No assignments found")

def get_assignment_details(assignment_id):
    """Get details for a specific assignment with error handling"""
    if not assignment_id:
        st.error("No assignment ID provided")
        return None
        
    details = safe_api_call(
        f"https://api.github.com/assignments/{assignment_id}",
        f"details for assignment {assignment_id}"
    )
    
    if details:
        details.setdefault('title', 'Untitled Assignment')
        details.setdefault('description', 'No description')
        details.setdefault('deadline', 'No deadline')
        details.setdefault('id', '') 
        return details
    return None

def display_assignment_details(assignments):
    for assignment in assignments:
                    deadline = datetime.fromisoformat(assignment['deadline'].replace("Z", "+00:00")).date() if assignment['deadline'] else "No deadline"
                    st.markdown(f"""
                           <div style="border: 1px solid #ccc; padding: 10px; border-radius: 5px; margin-top: 10px;">
                                <div style="display: flex; align-items: center;" margin-bottom: 10px;">
                                    <span style="border: 1px solid #4CAF50; border-radius: 12px; padding: 3px 8px; color: #4CAF50; font-weight: bold; margin-right: 5px;">
                                        {assignment['id']}
                                    </span>
                                    <span style="border: 1px; border-radius: 12px; padding: 3px 8px; font-weight: bold; font-size: 24px; color: #333;">
                                        {assignment['title']}
                                    </span>
                                </div>
                                <div style="margin-bottom: 10px;">
                                    <p style="margin: 0;"><strong>Deadline:</strong> {deadline}</p>
                                </div>
                                <div style="margin-bottom: 10px;">
                                    <a href="{assignment['classroom']['url']}" style="text-decoration: none;">
                                        <button style="background-color: #4CAF50; color: white; border: none; border-radius: 5px; padding: 5px 10px; margin-right: 10px;">
                                            Classroom Repository
                                        </button> 
                                    </a>
                                    <a href="{assignment['invite_link']}" style="text-decoration: none;">
                                        <button style="background-color: #008CBA; color: white; border: none; border-radius: 5px; padding: 5px 10px;">
                                            Invite to Classroom
                                        </button>
                                    </a>
                                </div>
                            </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f"---")
                    
def check_all_classroom_assignments():
    """Display all assignments across all classrooms with safe field access"""
    st.subheader("All Classroom Assignments")
    
    with st.spinner("Fetching all classrooms and assignments..."):
        classrooms = list_classrooms()
        if classrooms:
            st.success(f"Found {len(classrooms)} classrooms!")
            for classroom in classrooms:
                with st.expander(f"[ID: {classroom['id']}] {classroom['name']}"):
                    assignments = list_assignments(classroom['id'])
                    if assignments:
                        st.markdown(f"""<div style="border: 1px; padding: 10px; border-radius: 5px; font-weight: bold; margin-top: 10px; font-size: 24px;">
                                            Total Assignments: {len(assignments)}
                                            </div>""", unsafe_allow_html=True)
                        
                        display_assignment_details(assignments)
                    else:
                        st.error("No assignments found or failed to fetch")
        else:
            st.error("No classrooms found or failed to fetch")

def teacher_view():
    st.title("Classroom Management")

    # Display user info
    if "username" not in st.session_state:
        st.session_state.username = ""  # Initialize username
    st.sidebar.write(f"Logged in as: {st.session_state.username}")
    st.sidebar.write(f"Role: Teacher")
    
    tab1, tab2 = st.tabs(["View Assignments", "View Classrooms"])
    
    with tab1:
        st.header("View Assignments")
        
        if st.button("Serach Classrooms"):
            with st.spinner("Loading classrooms..."):
                classrooms = list_classrooms()
                if classrooms:
                    st.session_state.classrooms = classrooms
                    st.success(f"Found {len(classrooms)} classrooms!")
                else:
                    st.error("Failed to fetch classrooms")

        if 'classrooms' in st.session_state:
            classroom_options = {c['name']: c for c in st.session_state.classrooms}
            selected_classroom = st.selectbox(
                "Select Classroom",
                options=list(classroom_options.keys())
            )
            classroom_id = classroom_options[selected_classroom]['id']

            if classroom_id:
                with st.spinner("Loading assignments..."):
                    assignments = list_assignments(classroom_id)
                    if assignments:
                        st.session_state.assignments = assignments
                        st.success(f"Found {len(assignments)} assignments!")
                    else:
                        st.error("No assignments found or failed to fetch")

        if 'assignments' in st.session_state and isinstance(st.session_state.assignments, list):
            assignment_options = {
                assignment['title']: assignment for assignment in st.session_state.assignments
            }
            selected_assignment = st.selectbox(
                "Select Assignment",
                options=list(assignment_options.keys())
            )
            selected_assignment_data = assignment_options[selected_assignment]
            
            if selected_assignment_data:
                st.success(f"Found assignment: {selected_assignment_data['title']}")
                display_assignment_details([selected_assignment_data])
            else:
                st.error("No assignment data available")
        # else:
        #     st.info("No assignments available yet")
    
    with tab2:
        check_all_classroom_assignments()  # <-- Only this remains (removed the linked assignments section)

    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.username = None
        st.switch_page("Login.py")
        
    # cannot logout if not logged in
    if st.session_state.get("logged_in") is False:
        st.warning("Please login first")
        st.sidebar.button("Login", on_click=lambda: st.session_state.switch_page("Login.py"))
        
def student_view():
    st.title("View Classrooms")
    
    # Display user info
    if "username" not in st.session_state:
        st.session_state.username = ""  # Initialize username
    st.sidebar.write(f"Logged in as: {st.session_state.username}")
    st.sidebar.write(f"Role: Student")
    
    if 'permission' in st.session_state:
        st.sidebar.write(f"Permission: {st.session_state.permission.capitalize()}")
    
    try:
        assignments = list(db.assignments.find({"status": "active"}))
        
        if assignments:
            for assignment in assignments:
                due_date = assignment.get('deadline')
                display_date = due_date.strftime("%Y-%m-%d") if due_date else "No deadline"
                
                with st.expander(f"{assignment.get('title', 'Untitled Assignment')} - Due: {display_date}"):
                    st.markdown(f"""
                    **Instructions:**  
                    {assignment.get('additional_notes', 'No additional instructions')}
                    
                    **Invite Link:** [Accept Assignment]({assignment.get('invite_link', '#')})  
                    **Deadline:** {display_date}
                    """)
                    
                    if assignment.get('deadline') and assignment['deadline'] < datetime.now():
                        st.warning("This assignment is past its deadline")
        # else:
        #     st.info("No assignments available yet")
            
    except Exception as e:
        st.error(f"Error loading assignments: {str(e)}")
        

    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.username = None
        st.switch_page("Login.py")

def main():
    # Check if user is logged in
    if not st.session_state.get("logged_in"):
        st.warning("Please login first")
        st.switch_page("Login.py")
        return
    
    # Show appropriate view based on role
    if st.session_state.get("role") == "teacher":
        teacher_view()
    elif st.session_state.get("role") == "student":
        student_view()
    else:
        st.error("Unauthorized access")
        st.switch_page("Login.py")

if __name__ == "__main__":
    main()