import streamlit as st
import requests
import os
import json
from dotenv import load_dotenv
from datetime import datetime, time
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# Load environment variables
load_dotenv()

# MongoDB connection
uri = os.getenv("MONGODB_URI", "mongodb+srv://nata:isd2025@isdcluster.jnn9ctb.mongodb.net/?appName=ISDcluster")
client = MongoClient(uri, server_api=ServerApi('1'))
db = client.students_database

# GitHub Classroom setup
CLASSROOM_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"Bearer {CLASSROOM_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

# GitHub Organization
GITHUB_ORG = "COMP3122-Group18"  # Configure this or get from user input

def safe_api_call(url, description="data"):
    """Generic safe API call handler"""
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

def list_classrooms():
    """Fetch list of classrooms from GitHub Classroom API"""
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

def list_assignments(classroom_id):
    """Fetch assignments for a specific classroom with robust error handling"""
    if not classroom_id:
        st.error("No classroom ID provided")
        return None

    assignments = safe_api_call(
        f"https://api.github.com/classrooms/{classroom_id}/assignments",
        f"assignments for classroom {classroom_id}"
    )

    if assignments:
        for assignment in assignments:
            assignment.setdefault('title', 'Untitled Assignment')
            assignment.setdefault('id', '')
            assignment.setdefault('created_at', 'Unknown')
            assignment.setdefault('deadline', 'Not set')
            assignment.setdefault('invite_link', '#')
            assignment.setdefault('repo_url', 'Not available')
            assignment.setdefault('slug', 'No slug available')
        return assignments
    return None

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
        details.setdefault('id', assignment_id)
        details.setdefault('invite_link', '#')
        details.setdefault('created_at', 'Unknown')
        return details
    return None

def check_all_classroom_assignments():

    with st.spinner("Fetching all classrooms and assignments..."):
        classrooms = list_classrooms()
        if not classrooms:
            st.warning("No classrooms found")
            return

        for classroom in classrooms:
            with st.expander(f"Classroom: {classroom['name']} (ID: {classroom['id']})"):
                assignments = list_assignments(classroom['id'])
                if not assignments:
                    st.info("No assignments in this classroom")
                    continue

                st.write(f"**Total Assignments:** {len(assignments)}")
                for assignment in assignments:
                    st.markdown(f"""
                    - **Title:** {assignment['title']}
                    - **ID:** {assignment['id']}
                    - **Created At:** {assignment['created_at']}
                    - **Deadline:** {assignment['deadline']}
                    - **Repo URL:** {assignment['repo_url']}
                    - **Invite Link:** [Student Link]({assignment['invite_link']})
                    - **Slug:** {assignment['slug']}
                    """)
                    st.divider()

def display_filtered_issues(issues):
    with st.container():
        for issue in issues:
            created_at = datetime.fromisoformat(issue['created_at'].replace("Z", "+00:00")).date()
            updated_at = datetime.fromisoformat(issue['updated_at'].replace("Z", "+00:00")).date()
            st.markdown(f"""
                <div style="border: 1px solid #ccc; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4 style="margin: 0;">{issue['title']}</h4>
                        <a href="{issue['url']}" style="text-decoration: none;">
                            <button style="background-color: #4CAF50; color: white; border: none; border-radius: 5px; padding: 5px 10px;">
                                View Issue
                            </button>
                        </a>
                    </div>
                    <strong>Created:</strong> {created_at} |
                    <strong>Updated:</strong> {updated_at}<br><br>
                    <h6>Description:</h6>
                    {issue['body']}
                </div>
                """, unsafe_allow_html=True)
        st.write("---")

def display_filtered_prs(prs):
    for pr in prs:
        created_at = datetime.fromisoformat(pr['created_at'].replace("Z", "+00:00")).date()
        updated_at = datetime.fromisoformat(pr['updated_at'].replace("Z", "+00:00")).date()
        st.markdown(f"""
            <div style="border: 1px solid #ccc; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h4 style="margin: 0;">{pr['title']}</h4>
                    <div style="display: flex; align-items: center;">
                        <span style="border: 1px solid #4CAF50; border-radius: 12px; padding: 3px 8px; color: #4CAF50; font-weight: bold; margin-right: 10px;">
                            {pr['state']}
                        </span>
                        <a href="{pr['url']}" style="text-decoration: none;">
                            <button style="background-color: #4CAF50; color: white; border: none; border-radius: 5px; padding: 5px 10px;">
                                View Pull Request
                            </button>
                        </a>
                    </div>
                </div>
                <strong>Created:</strong> {created_at} |
                <strong>Updated:</strong> {updated_at}<br>
                <div style="border: 1px solid #ccc; padding: 10px; border-radius: 5px; margin-top: 10px;">
                    <h6>Description:</h6>
                    <p>{pr['body'] or 'None'}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.write("---")

def display_filter_milestone(milestones):
    for title, details in milestones.items():
        due_on = datetime.fromisoformat(details['due_on'].replace("Z", "+00:00")).date() if details['due_on'] else "No due date"
        st.markdown(f"""
            <div style="border: 1px solid #ccc; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h4 style="margin: 0;">{title}</h4>
                    <div style="display: flex; align-items: center;">
                        <span style="border: 1px solid #4CAF50; border-radius: 12px; padding: 3px 8px; color: #4CAF50; font-weight: bold; margin-right: 10px;">
                            {details['state']}
                        </span>
                        <a href="{details['url']}" style="text-decoration: none;">
                            <button style="background-color: #4CAF50; color: white; border: none; border-radius: 5px; padding: 5px 10px;">
                                View Milestone
                            </button>
                        </a>
                    </div>
                </div>
                <strong>Due date:</strong> {due_on}<br>
                <div style="border: 1px solid #ccc; padding: 10px; border-radius: 5px; margin-top: 10px;">
                    <h6>Description:</h6>
                    <p>{details['description']}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.write("---")

def display_sorted_issues(issues):
    with st.container():
        for issue in issues:
            created_at = datetime.fromisoformat(issue['created_at'].replace("Z", "+00:00")).date()
            updated_at = datetime.fromisoformat(issue['updated_at'].replace("Z", "+00:00")).date()
            st.markdown(f"""
                <div style="border: 1px solid #ccc; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4 style="margin: 0;">{issue['title']}</h4>
                        <a href="{issue['url']}" style="text-decoration: none;">
                            <button style="background-color: #4CAF50; color: white; border: none; border-radius: 5px; padding: 5px 10px;">
                                View Issue
                            </button>
                        </a>
                    </div>
                    <strong>User:</strong> {issue['user']}<br>
                    <strong>Created:</strong> {created_at} |
                    <strong>Updated:</strong> {updated_at}<br>
                    <div style="border: 1px solid #ccc; padding: 10px; border-radius: 5px; margin-top: 10px;">
                        <h6>Description:</h6>
                        <p>{issue['body'] or 'None'}</p>
                    </div>
                </div>""", unsafe_allow_html=True)
            st.write("---")

def display_sorted_pr(prs):
    for pr in prs:
        created_at = datetime.fromisoformat(pr['created_at'].replace("Z", "+00:00")).date()
        updated_at = datetime.fromisoformat(pr['updated_at'].replace("Z", "+00:00")).date()
        st.markdown(f"""
            <div style="border: 1px solid #ccc; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h4 style="margin: 0;">{pr['title']}</h4>
                    <div style="display: flex; align-items: center;">
                        <span style="border: 1px solid #4CAF50; border-radius: 12px; padding: 3px 8px; color: #4CAF50; font-weight: bold; margin-right: 10px;">
                            {pr['state']}
                        </span>
                        <a href="{pr['url']}" style="text-decoration: none;">
                            <button style="background-color: #4CAF50; color: white; border: none; border-radius: 5px; padding: 5px 10px;">
                                View Pull Request
                            </button>
                        </a>
                    </div>
                </div>
                <strong>User:</strong> {pr['user']}<br>
                <strong>Created:</strong> {created_at} |
                <strong>Updated:</strong> {updated_at}<br>
                <div style="border: 1px solid #ccc; padding: 10px; border-radius: 5px; margin-top: 10px;">
                    <h6>Description:</h6>
                    <p>{pr['body'] or 'None'}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.write("---")

def display_sorted_milestones(milestones):
    for title, details in milestones.items():
        due_on = datetime.fromisoformat(details['due_on'].replace("Z", "+00:00")).date() if details['due_on'] else "No due date"
        st.markdown(f"""
            <div style="border: 1px solid #ccc; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h4 style="margin: 0;">{title}</h4>
                    <div style="display: flex; align-items: center;">
                        <span style="border: 1px solid #4CAF50; border-radius: 12px; padding: 3px 8px; color: #4CAF50; font-weight: bold; margin-right: 10px;">
                            {details['state']}
                        </span>
                        <a href="{details['url']}" style="text-decoration: none;">
                            <button style="background-color: #4CAF50; color: white; border: none; border-radius: 5px; padding: 5px 10px;">
                                View Milestone
                            </button>
                        </a>
                    </div>
                </div>
                <div style="margin-top: 10px;">
                    <strong>Creator:</strong> {details['creator']}<br>
                    <strong>Due date:</strong> {due_on}<br>
                    <div style="border: 1px solid #ccc; padding: 10px; border-radius: 5px; margin-top: 10px;">
                        <h6>Description:</h6>
                        <p>{details['description']}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        st.write("---")

def fetch_and_display_repo_data(org_name, repos_headers, assignment_slug):
    """Fetches and displays repository data (issues, PRs, milestones), filtering by assignment_slug."""
    try:
        repos_url = f"https://api.github.com/orgs/{org_name}/repos"
        repos_response = requests.get(repos_url, headers=repos_headers)
        repos_response.raise_for_status()  # Raise HTTPError for bad responses
        repositories = repos_response.json()

        if repositories:
            issues_details = []
            pr_details = []
            milestone_details = {}

            # Filter repositories based on assignment_slug
            repo_names = [repo['name'] for repo in repositories if repo['name'].startswith(assignment_slug)]
            selected_repos = st.selectbox("Select a group", ["Select a group"] + repo_names)

            if selected_repos != "Select a group":
                # Fetch issues, PRs, and milestones
                issues_url = f"https://api.github.com/repos/{org_name}/{selected_repos}/issues"
                issues_response = requests.get(issues_url, headers=repos_headers)
                issues_response.raise_for_status()
                issues = issues_response.json()

                for issue in issues:
                    if 'pull_request' in issue:
                        pr_details.append({
                            "title": issue['title'],
                            "body": issue.get('body', 'No description provided'),
                            "user": issue['user']['login'],
                            "state": issue['state'],
                            "created_at": issue['created_at'],
                            "updated_at": issue['updated_at'],
                            "url": issue['html_url'],
                            "files_changed": []
                        })
                    else:
                        issues_details.append({
                            "title": issue['title'],
                            "body": issue.get('body', 'No description provided'),
                            "user": issue['user']['login'],
                            "created_at": issue['created_at'],
                            "updated_at": issue['updated_at'],
                            "url": issue['html_url']
                        })

                milestones_url = f"https://api.github.com/repos/{org_name}/{selected_repos}/milestones"
                milestones_response = requests.get(milestones_url, headers=repos_headers)
                milestones_response.raise_for_status()
                milestones = milestones_response.json()

                for milestone in milestones:
                    milestone_title = milestone['title']
                    milestone_details[milestone_title] = {
                        "state": milestone['state'],
                        "due_on": milestone['due_on'],
                        "url": milestone['html_url'],
                        "creator": milestone['creator']['login'],
                        "description": milestone.get('description', 'No description provided.'),
                        "users": [issue['user']['login'] for issue in issues if issue.get('milestone') and issue['milestone']['title'] == milestone_title]
                    }

                # Sort all contents with username
                sorted_issues = sorted(issues_details, key=lambda x: x['user'])
                sorted_prs = sorted(pr_details, key=lambda x: x['user'])
                sorted_milestones = sorted(milestone_details.items(), key=lambda x: x[1]['creator'])

                select_user = st.selectbox("Select a user", ["All"] + sorted(set(issue['user'] for issue in issues_details + pr_details)))

                if select_user != "All":
                    filtered_issues = [issue for issue in sorted_issues if issue['user'] == select_user]
                    filtered_prs = [pr for pr in sorted_prs if pr['user'] == select_user]
                    filtered_milestones = {title: details for title, details in sorted_milestones if details['creator'] == select_user}
                else:
                    filtered_issues = sorted_issues
                    filtered_prs = sorted_prs
                    filtered_milestones = milestone_details

                # Add a radio button to select the content type
                content_type = st.radio(
                    "Select content to view",
                    ("All", "Issues", "Pull Requests", "Milestones"),
                    horizontal=True
                )

                # Display content based on selection
                if content_type == "All":
                    display_issues = True
                    display_prs = True
                    display_milestones = True

                elif content_type == "Issues":
                    display_issues = True
                    display_prs = False
                    display_milestones = False

                elif content_type == "Pull Requests":
                    display_issues = False
                    display_prs = True
                    display_milestones = False

                elif content_type == "Milestones":
                    display_issues = False
                    display_prs = False
                    display_milestones = True

                # Display issues, pull requests, and milestones with selected user
                if select_user != "All":
                    if display_issues:
                        st.write(f"### Issues by {select_user}:")
                        if filtered_issues:
                            display_filtered_issues(filtered_issues)
                        else:
                            st.write("No issues found for this user.")
                            st.write("---")

                    if display_prs:
                        st.write(f"### Pull Requests by {select_user}:")
                        if filtered_prs:
                            display_filtered_prs(filtered_prs)
                        else:
                            st.write("No pull requests found for this user.")
                            st.write("---")

                    if display_milestones:
                        st.write(f"### Milestones by {select_user}:")
                        if filtered_milestones:
                            display_filter_milestone(filtered_milestones)
                        else:
                            st.write("No milestones found for this user.")
                            st.write("---")

                else:
                    if display_issues:
                        st.write("### All Issues:")
                        if sorted_issues:
                            display_sorted_issues(sorted_issues)
                        else:
                            st.write("No issues found.")
                            st.write("---")

                    if display_prs:
                        st.write("### All Pull Requests:")
                        if sorted_prs:
                            display_sorted_pr(sorted_prs)
                        else:
                            st.write("No pull requests found.")
                            st.write("---")

                    if display_milestones:
                        st.write("### All Milestones:")
                        if sorted_milestones:
                            display_sorted_milestones(sorted_milestones)
                        else:
                            st.write("No milestones found.")
                            st.write("---")
        else:
            st.write("No repositories found for this organization.")

    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching repositories or issues: {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")

def teacher_view():
    st.title("View Activities")

    # Display user info
    if "username" not in st.session_state:
        st.session_state.username = ""  # Initialize username
    st.sidebar.write(f"Logged in as: {st.session_state.username}")
    st.sidebar.write(f"Role: Teacher")

    # Fetch classrooms and assignments immediately
    with st.spinner("Loading classrooms..."):
        classrooms = list_classrooms()
        if classrooms:
            st.session_state.classrooms = classrooms

        else:
            st.error("Failed to fetch classrooms")

    if 'classrooms' in st.session_state:
        classroom_options = {c['name']: c for c in st.session_state.classrooms}
        selected_classroom = st.selectbox(
            "Select Classroom",
            options=list(classroom_options.keys())
        )
        classroom_id = classroom_options[selected_classroom]['id']

        # Fetch assignments immediately after classroom selection
        with st.spinner("Loading assignments..."):
            assignments = list_assignments(classroom_id)
            if assignments:
                st.session_state.assignments = assignments
            else:
                st.error("No assignments found or failed to fetch")

    # Allow selection of assignments
    if 'assignments' in st.session_state and isinstance(st.session_state.assignments, list):
        assignment_titles = [a['title'] for a in st.session_state.assignments]

        if assignment_titles:
            selected_title = st.selectbox(
                "Choose an assignment",
                options=assignment_titles
            )

            # Find the selected assignment based on title
            selected_assignment = next((a for a in st.session_state.assignments if a['title'] == selected_title), None)


            # Use st.write to display the selected assignments
            if selected_assignment:
                # GitHub Repository Data
                repos_headers = {"Authorization": f"token {CLASSROOM_TOKEN}"}
                fetch_and_display_repo_data(GITHUB_ORG, repos_headers, selected_assignment['slug'])

            else:
                st.info("No assignment found with that title.")
        else:
            st.info("No assignments available to select.")
    else:
        st.info("No assignments fetched yet.")

    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.username = None
        st.switch_page("Login.py")

def student_view():
    st.title("You have not permission!")

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