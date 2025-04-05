import streamlit as st
import webbrowser
import requests
import urllib.parse
from streamlit.web.server import Server
import time
import matplotlib.pyplot as plt
import json
from datetime import datetime

# OAuth settings
client_id = "Ov23liTxryC5DAIzStP8"
client_secret = "bf372b10e0e6064de4bf1c99db9f60deb02376a3"
redirect_uri = "http://localhost:8501"  # Streamlit's default port
token_url = "https://github.com/login/oauth/access_token"
auth_url = f"https://github.com/login/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}"

# Streamlit app
st.title("GitHub Classroom Activity")

# Initialize session state
if "auth_code" not in st.session_state:
    st.session_state.auth_code = None
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "query_params" not in st.session_state:
    st.session_state.query_params = None

# Function to get query parameters from URL
def get_query_params():
    try:
        query_params = st.query_params
        return query_params
    except:
        return None
    
# Step 3: Exchange code for access token
if st.session_state.auth_code and not st.session_state.access_token:
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": st.session_state.auth_code,
        "redirect_uri": redirect_uri
    }
    headers = {"Accept": "application/json"}

    try:
        response = requests.post(token_url, data=payload, headers=headers)
        token_data = response.json()
        access_token = token_data.get("access_token")
        st.session_state.access_token = access_token
    except Exception as e:
        st.error(f"Error fetching token: {e}")

def display_filtered_issues(issues):
    with st.container():
        for issue in issues:
            created_at = datetime.fromisoformat(issue['created_at'].replace("Z", "+00:00")).date()
            updated_at = datetime.fromisoformat(issue['updated_at'].replace("Z", "+00:00")).date()

            st.markdown(
                f"""
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
                """, unsafe_allow_html=True
            )
        st.write("---")

def display_filtered_prs(prs):
    for pr in prs:
        created_at = datetime.fromisoformat(pr['created_at'].replace("Z", "+00:00")).date()
        updated_at = datetime.fromisoformat(pr['updated_at'].replace("Z", "+00:00")).date()

        st.markdown(
            f"""
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
            """, unsafe_allow_html=True
        )
        st.write("---")

def display_filter_milestone(milestones):
    for title, details in milestones.items():
        due_on = datetime.fromisoformat(details['due_on'].replace("Z", "+00:00")).date() if details['due_on'] else "No due date"
        st.markdown(
            f"""
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
            """, unsafe_allow_html=True
        )
        st.write("---")
        
def display_sorted_issues(issues):
    with st.container():
        for issue in issues:
            created_at = datetime.fromisoformat(issue['created_at'].replace("Z", "+00:00")).date()
            updated_at = datetime.fromisoformat(issue['updated_at'].replace("Z", "+00:00")).date()

            st.markdown(
                f"""
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
                </div>""", unsafe_allow_html=True
            )
            st.write("---")
        
def display_sorted_pr(prs):
    for pr in prs:
        created_at = datetime.fromisoformat(pr['created_at'].replace("Z", "+00:00")).date()
        updated_at = datetime.fromisoformat(pr['updated_at'].replace("Z", "+00:00")).date()

        st.markdown(
            f"""
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
            """, unsafe_allow_html=True
        )
        st.write("---")

def display_sorted_milestones(milestones):
    for title, details in milestones:
        due_on = datetime.fromisoformat(details['due_on'].replace("Z", "+00:00")).date() if details['due_on'] else "No due date"
        st.markdown(
            f"""
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
            """, unsafe_allow_html=True
        )
        st.write("---")

# Step 4: Redirect to GitHub authorization page
if st.session_state.access_token:
    user_or_org = "COMP3122-Group18"  # Specify user or org
    repos_url = f"https://api.github.com/orgs/{user_or_org}/repos"
    repos_headers = {"Authorization": f"token {st.session_state.access_token}"}

    try:
        # Fetching all repositories
        repos_response = requests.get(repos_url, headers=repos_headers)
        repositories = repos_response.json()

        if repositories:
            issues_details = []
            pr_details = []
            milestone_details = {}

            # Store all repository names in a list
            repo_names = [repo['name'] for repo in repositories]
            selected_repos = st.selectbox("Select a repository", ["Select a group"] + repo_names)
            
            # Display selected repositories
            if selected_repos != "Select a group":
                repos_name = [selected_repos]  # Single repository as list
                
                issues_url = f"https://api.github.com/repos/{user_or_org}/{selected_repos}/issues"
                issues_response = requests.get(issues_url, headers=repos_headers)
                issues = issues_response.json()
                
                for issue in issues:
                    # Check if the issue is a pull request
                    if 'pull_request' in issue:
                        pr_details.append({"title": issue['title'],"body": issue.get('body', 'No description provided'), "user": issue['user']['login'], "state": issue['state'],
                                            "created_at": issue['created_at'], "updated_at": issue['updated_at'], "url": issue['html_url'], "files_changed": [] })
                    else:
                        issues_details.append({"title": issue['title'], "body": issue.get('body', 'No description provided'), "user": issue['user']['login'], 
                                               "created_at": issue['created_at'], "updated_at": issue['updated_at'], "url": issue['html_url']})
                
                milestones_url = f"https://api.github.com/repos/{user_or_org}/{selected_repos}/milestones"
                milestones_response = requests.get(milestones_url, headers=repos_headers)
                milestones = milestones_response.json()
                print(milestones)
                
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
                         
                # sorted all contents with username
                sorted_issues = sorted(issues_details, key=lambda x: x['user'])
                sorted_prs = sorted(pr_details, key=lambda x: x['user'])
                sorted_milestones = sorted(milestone_details.items(), key=lambda x: x[1]['creator'])
                print("\n", sorted_milestones)
                
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
                    "Select content to view:",
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
                        # Display pull requests of the selected user
                        st.write(f"### Pull Requests by {select_user}:")
                        if filtered_prs:
                            print("\n", filtered_prs)
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

    except Exception as e:
        st.error(f"Error fetching repositories or issues: {e}")

# Configuration
ORG = "your-org"  # Replace with your GitHub organization name

ASSIGNMENT_PREFIX = "assignment-name"  # Replace with your assignment prefix
BASE_URL = "https://api.github.com"

# Headers for authentication
headers = {
    "Authorization": f"Bearer {st.session_state.access_token}",
    "Accept": "application/vnd.github.v3+json"
}

def get_repos(org, prefix):
    """Fetch all repositories in the organization matching the prefix."""
    url = f"{BASE_URL}/orgs/{org}/repos"
    response = requests.get(url, headers=headers, params={"per_page": 100})
    if response.status_code != 200:
        print(f"Error fetching repos: {response.status_code} - {response.text}")
        return []
    
    repos = response.json()
    return [repo["name"] for repo in repos if repo["name"].startswith(prefix)]

def get_commit_count(org, repo):
    """Get the total number of commits in a repository."""
    url = f"{BASE_URL}/repos/{org}/{repo}/commits"
    # Use per_page=1 and check the 'Link' header for the last page
    response = requests.get(url, headers=headers, params={"per_page": 1})
    if response.status_code != 200:
        print(f"Error fetching commits for {repo}: {response.status_code}")
        return 0
    
    # Extract the last page number from the Link header
    link_header = response.headers.get("Link", "")
    if "last" in link_header:
        last_page = int(link_header.split("page=")[-1].split(">")[0])
        return last_page
    # If no pagination, count the commits directly (small repos)
    return len(response.json())

def get_activity_log(org, repo):
    """Get the activity log (commit details) for a repository."""
    url = f"{BASE_URL}/repos/{org}/{repo}/commits"
    response = requests.get(url, headers=headers, params={"per_page": 100})
    if response.status_code != 200:
        print(f"Error fetching activity for {repo}: {response.status_code}")
        return []
    
    commits = response.json()
    activity = []
    for commit in commits:
        author = commit["commit"]["author"]["name"]
        date = commit["commit"]["author"]["date"]
        message = commit["commit"]["message"]
        activity.append({
            "author": author,
            "date": datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S"),
            "message": message
        })
    return activity

def main():
    # Get all Classroom repositories
    print(f"Fetching repositories for {ORG} with prefix '{ASSIGNMENT_PREFIX}'...")
    repos = get_repos(ORG, ASSIGNMENT_PREFIX)
    if not repos:
        print("No repositories found or error occurred.")
        return

    # Process each repository
    for repo in repos:
        print(f"\nProcessing {repo}:")
        
        # Get commit count
        commit_count = get_commit_count(ORG, repo)
        print(f"Total Commits: {commit_count}")
        
        # Get activity log
        activity_log = get_activity_log(ORG, repo)
        if activity_log:
            print("Activity Log:")
            for entry in activity_log:
                print(f"- {entry['date']} | {entry['author']}: {entry['message']}")
        else:
            print("No activity found.")

if __name__ == "__main__":
    main()
