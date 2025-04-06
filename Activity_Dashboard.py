import streamlit as st
import requests
import os
import json
from dotenv import load_dotenv
import re
import webbrowser
import plotly.express as px
import plotly.graph_objects as go
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import datetime

# Set page configuration
st.set_page_config(page_title="Login", page_icon="💂", layout="wide", initial_sidebar_state="collapsed")

# Load environment variables
load_dotenv()

# MongoDB connection (optional, only if you're using it)
uri = "mongodb+srv://nata:isd2025@isdcluster.jnn9ctb.mongodb.net/?appName=ISDcluster"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client.students_database

# GitHub Setup
CLASSROOM_TOKEN = os.getenv("GITHUB_TOKEN")
CLIENT_ID = "Iv1.41f399f782698a77"
CLIENT_SECRET = "9728a5445b332b6379847000a196e37b79203965"
REDIRECT_URI = "http://localhost:8501"
TOKEN_URL = "https://github.com/login/oauth/access_token"
AUTH_URL = f"https://github.com/login/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
ORG_NAME = "COMP3122-Group18"

HEADERS = {
    "Authorization": f"Bearer {CLASSROOM_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

# API Helper Functions (unchanged)
def safe_api_call(url, headers, description="data"):
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching {description}: {str(e)}")
        return None

def list_classrooms():
    classrooms = safe_api_call("https://api.github.com/classrooms", HEADERS, "classrooms")
    if classrooms:
        for c in classrooms:
            c.setdefault('name', 'Unnamed Classroom')
            c.setdefault('id', '')
        return classrooms
    st.warning("No classrooms returned")
    return []

def list_assignments(classroom_id):
    if not classroom_id:
        st.error("No classroom ID provided")
        return []
    assignments = safe_api_call(
        f"https://api.github.com/classrooms/{classroom_id}/assignments",
        HEADERS,
        f"assignments for classroom {classroom_id}"
    )
    if assignments:
        for a in assignments:
            a.setdefault('title', 'Untitled Assignment')
            a.setdefault('slug', '')
            a.setdefault('id', '')
            a.setdefault("accepted", '')
            a.setdefault("submissions", '')
        return assignments
    st.warning("No assignments returned")
    return []

def get_group_names(token, org, prefix):
    url = f"https://api.github.com/orgs/{org}/repos"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    repos = safe_api_call(url, headers, "repositories")
    if repos:
        pattern = f"{prefix}-(.+)"
        groups = [match.group(1) for repo in repos if (match := re.search(pattern, repo['name']))]
        if not groups:
            st.warning(f"No groups found matching prefix: {prefix}")
        return groups
    return []

def fetch_activity_data(token, org, repo_name):
    headers = {"Authorization": f"token {token}"}
    issues_details = []
    pr_details = []
    milestone_details = {}  # Changed to a dictionary
    
    # Fetch issues and PRs
    issues_url = f"https://api.github.com/repos/{org}/{repo_name}/issues"
    issues = safe_api_call(issues_url, headers, f"issues for {repo_name}")
    
    if issues:
        for issue in issues:
            data = {
                "title": issue['title'],
                "user": issue['user']['login'],
                "created_at": issue['created_at'],
                "url": issue['html_url']
            }
            if 'pull_request' in issue:
                data["state"] = issue['state']
                pr_details.append(data)
            else:
                issues_details.append(data)
    else:
        st.warning(f"No issues found for {repo_name}")

    # Fetch milestones
    milestones_url = f"https://api.github.com/repos/{org}/{repo_name}/milestones"
    milestones = safe_api_call(milestones_url, headers, f"milestones for {repo_name}")
    
    if milestones:
        for milestone in milestones:
            milestone_title = milestone['title']
            milestone_details[milestone_title] = {
                "state": milestone['state'],
                "due_on": milestone['due_on'],
                "url": milestone['html_url'],
                "description": milestone.get('description', 'No description provided.'),
                "creator": milestone['creator']['login']
            }
    else:
        st.warning(f"No milestones found for {repo_name}")
        
    commits_url = f"https://api.github.com/repos/{org}/{repo_name}/commits"
    commits = safe_api_call(commits_url, headers, f"commits for {repo_name}")

    if commits:
        commit_details = {}
        for commit in commits:
            author = commit["commit"]["author"]["name"]
            if author == "github-classroom[bot]":
                continue
            
            commit_sha = commit["sha"]
            timestamp = commit["commit"]["author"]["date"]

            commit_detail_url = f"https://api.github.com/repos/{org}/{repo_name}/commits/{commit_sha}"
            commit_detail_response = requests.get(commit_detail_url, headers=headers)
            commit_detail = commit_detail_response.json()

            if 'stats' in commit_detail:
                additions = commit_detail['stats']['additions']
                deletions = commit_detail['stats']['deletions']
            else:
                additions = 0
                deletions = 0

            if author not in commit_details:
                commit_details[author] = {'commits': [], 'additions': 0, 'deletions': 0}
            commit_details[author]['commits'].append(timestamp)
            commit_details[author]['additions'] += additions
            commit_details[author]['deletions'] += deletions
        
    return issues_details, pr_details, milestone_details, commit_details

def display_dashboard(issues, prs, milestones, commit_details):
    # Custom CSS for beautification
    st.markdown("""
    <style>
        .big-font { font-size: 24px !important; font-weight: bold; }
        .subheader { color: #34495e; font-size: 20px; margin-top: 20px; }
        .metric-container { padding: 10px; border-radius: 8px; margin-bottom: 15px; }
        .chart-container { margin-bottom: 20px; border-radius: 8px; }
        .stPlotlyChart { border-radius: 8px; overflow: hidden; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h2 class='big-font'>Activity Dashboard</h2>", unsafe_allow_html=True)

    # Count data per user
    user_activity_counts = {}  # Combined counts for all activity types

    # Count issues per user
    for issue in issues:
        user = issue['user']
        user_activity_counts[user] = user_activity_counts.get(user, 0) + 1
    
    # Count pull requests per user
    for pr in prs:
        user = pr['user']
        user_activity_counts[user] = user_activity_counts.get(user, 0) + 1

    # Count milestones per creator
    for milestone_title, milestone_data in milestones.items():
        if 'creator' in milestone_data:
            creator = milestone_data['creator']
            user_activity_counts[creator] = user_activity_counts.get(creator, 0) + 1
    
    # Count commits per user
    for author, details in commit_details.items():
        if author not in user_activity_counts:
            user_activity_counts[author] = 0
        user_activity_counts[author] += len(details['commits'])
        user_activity_counts[author] += details['additions']
        user_activity_counts[author] += details['deletions']
    
    # Dashboard layout
    col1, col2, col3 = st.columns(3, gap="medium")

    # Issues Visualization
    with col1:
        st.markdown("<h3 class='subheader'>Issues 📋</h3>", unsafe_allow_html=True)
        if issues:
            issue_counts = {}
            for issue in issues:
                user = issue['user']
                issue_counts[user] = issue_counts.get(user, 0) + 1

            if issue_counts:
                labels = list(issue_counts.keys())
                values = list(issue_counts.values())
                fig_issues = go.Figure(data=[go.Pie(labels=labels, values=values, textinfo='percent+label')])
                fig_issues.update_layout(
                    title_text="Issues per User", 
                    title_x=0.5, 
                    showlegend=True,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig_issues, use_container_width=True, className="chart-container")
                st.markdown(f"<div class='metric-container'><strong>Total Issues:</strong> {len(issues)}</div>", unsafe_allow_html=True)
            else:
                st.write("No issues to display")
        else:
            st.write("No issues to display")
            
        # Display line graph for commits
        if commit_details:
            st.markdown("<h3 class='subheader'>Commit Activity 📈</h3>", unsafe_allow_html=True)
            line_data = {}
            for author, details in commit_details.items():
                for timestamp in details['commits']:
                    date = timestamp.split("T")[0]
                    if author not in line_data:
                        line_data[author] = []
                    line_data[author].append(date)
            
            fig = go.Figure()
            for author, timestamps in line_data.items():
                commit_counts = {}
                for date in timestamps:
                    commit_counts[date] = commit_counts.get(date, 0) + 1

                sorted_dates = sorted(commit_counts.keys())
                counts = [commit_counts[date] for date in sorted_dates]

                fig.add_trace(go.Scatter(x=sorted_dates, y=counts, mode='lines+markers', name=author))
            
            fig.update_layout(
                title="Commit Activity by Author",
                xaxis_title="Date",
                yaxis_title="Number of Commits",
                xaxis_tickangle=-45,
                xaxis_tickformat="%Y-%m-%d",
                xaxis=dict(tickmode='array', tickvals=sorted_dates),
                yaxis=dict(title="Number of Commits"),
                legend_title="Authors",
                showlegend=True,
                height=400,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig, use_container_width=True, className="chart-container")
        else:
            st.write("No commit data to display")

    # Pull Requests Visualization
    with col2:
        st.markdown("<h3 class='subheader'>Pull Requests 🔄</h3>", unsafe_allow_html=True)
        if prs:
            pr_counts = {}
            for pr in prs:
                user = pr['user']
                pr_counts[user] = pr_counts.get(user, 0) + 1

            if pr_counts:
                labels = list(pr_counts.keys())
                values = list(pr_counts.values())
                fig_pr = go.Figure(data=[go.Pie(labels=labels, values=values, textinfo='percent+label')])
                fig_pr.update_layout(
                    title_text="PRs per User", 
                    title_x=0.5, 
                    showlegend=True,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig_pr, use_container_width=True, className="chart-container")
                st.markdown(f"<div class='metric-container'><strong>Total PRs:</strong> {len(prs)}</div>", unsafe_allow_html=True)
            else:
                st.write("No pull requests to display")
        else:
            st.write("No pull requests to display")
        
        # Pie chart for number of commits for each author
        if commit_details:
            st.markdown("<h3 class='subheader'>Number of Commits by Author 🖋️</h3>", unsafe_allow_html=True)
            labels = list(commit_details.keys())
            values = [len(details['commits']) for details in commit_details.values()]
            fig = go.Figure(data=[go.Pie(labels=labels, values=values, textinfo='percent+label')])
            fig.update_layout(
                title_text="Number of Commits by Author", 
                title_x=0.5, 
                showlegend=True,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig, use_container_width=True, className="chart-container")
        else:
            st.write("No commit data to display")

    # Milestones Visualization
    with col3:
        st.markdown("<h3 class='subheader'>Milestones 🎯</h3>", unsafe_allow_html=True)
        if milestones:
            milestone_counts = {}
            for milestone_title, milestone_data in milestones.items():
                if 'creator' in milestone_data:
                    creator = milestone_data['creator']
                    milestone_counts[creator] = milestone_counts.get(creator, 0) + 1

            if milestone_counts:
                labels = list(milestone_counts.keys())
                values = list(milestone_counts.values())
                fig_milestones = go.Figure(data=[go.Pie(labels=labels, values=values, textinfo='percent+label')])
                fig_milestones.update_layout(
                    title_text="Milestone Contributions per User", 
                    title_x=0.5, 
                    showlegend=True,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig_milestones, use_container_width=True, className="chart-container")
                st.markdown(f"<div class='metric-container'><strong>Total Milestones:</strong> {len(milestones)}</div>", unsafe_allow_html=True)
            else:
                st.write("No milestone contributions to display")
        else:
            st.write("No milestone contributions to display")
            
        # Bar graph for additions and deletions
        if commit_details:
            st.markdown("<h3 class='subheader'>Additions and Deletions 📊</h3>", unsafe_allow_html=True)
            authors = list(commit_details.keys())
            additions = [details['additions'] for details in commit_details.values()]
            deletions = [details['deletions'] for details in commit_details.values()]
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=authors, y=additions, name='Additions'))
            fig.add_trace(go.Bar(x=authors, y=deletions, name='Deletions'))
            fig.update_layout(
                barmode='group', 
                title="Additions and Deletions by Author", 
                xaxis_title="Authors", 
                yaxis_title="Count", 
                showlegend=True,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig, use_container_width=True, className="chart-container")
        else:
            st.write("No commit data to display")

    # Display the combined counts per user
    st.markdown("<h2 class='big-font'>Total Activity Counts per User</h2>", unsafe_allow_html=True)
    if user_activity_counts:
        most_active_user = max(user_activity_counts, key=user_activity_counts.get)
        most_active_count = user_activity_counts[most_active_user]
        least_active_user = min(user_activity_counts, key=user_activity_counts.get)
        least_active_count = user_activity_counts[least_active_user]

        col4, col5 = st.columns(2)

        with col4:
            st.markdown(f"<div class='metric-container'><strong>Most Active User:</strong> {most_active_user} ({most_active_count} activities)</div>", unsafe_allow_html=True)

        with col5:
            st.markdown(f"<div class='metric-container'><strong>Least Active User:</strong> {least_active_user} ({least_active_count} activities)</div>", unsafe_allow_html=True)
    else:
        st.write("No activity data to display")

    return user_activity_counts  # Return the dictionary

def teacher_view():
    # Custom CSS for beautification
    st.markdown("""
    <style>
        .stButton>button { border-radius: 8px; padding: 10px 20px; }
        .stButton>button:hover { opacity: 0.9; }
        .stSelectbox { margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

    st.title("📊 Project Activity Dashboard")
    
    # Initialize session state
    if "auth_code" not in st.session_state:
        st.session_state.auth_code = None
    if "access_token" not in st.session_state:
        st.session_state.access_token = None

    # Authentication
    if not st.session_state.access_token:
        st.markdown("<p class='big-font'>Please authenticate with GitHub</p>", unsafe_allow_html=True)
        if st.button("Login with GitHub"):
            webbrowser.open(AUTH_URL)
        query_params = st.query_params
        if query_params and "code" in query_params:
            st.session_state.auth_code = query_params["code"]
            payload = {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": st.session_state.auth_code,
                "redirect_uri": REDIRECT_URI
            }
            response = requests.post(TOKEN_URL, data=payload, headers={"Accept": "application/json"})
            if response.ok:
                st.session_state.access_token = response.json().get("access_token")
                st.success("Authentication successful!")
                st.experimental_rerun()
            else:
                st.error(f"Authentication failed: {response.text}")
        return

    # Sidebar info
    st.sidebar.write(f"Logged in as: {st.session_state.get('username', 'Teacher')}")
    st.sidebar.write("Role: Teacher")

    # Tabs updated to "Dashboard" and "Download Report"
    dashboard_tab, report_tab = st.tabs(["Dashboard", "Download Report"])

    with dashboard_tab:
        # Classroom and Assignment Selection
        with st.spinner("Loading classrooms..."):
            classrooms = list_classrooms()
        
        if classrooms:
            classroom_options = {c['name']: c for c in classrooms}
            selected_classroom = st.selectbox("Select Classroom", list(classroom_options.keys()), format_func=lambda x: f"📚 {x}")
            classroom_id = classroom_options[selected_classroom]['id']

            with st.spinner("Loading assignments..."):
                assignments = list_assignments(classroom_id)
            
            if assignments:
                assignment_titles = [a['title'] for a in assignments]
                selected_title = st.selectbox("Select Assignment", assignment_titles, format_func=lambda x: f"📝 {x}")
                selected_assignment = next(a for a in assignments if a['title'] == selected_title)
                slug = selected_assignment['slug']

                # Group Selection
                with st.spinner("Loading groups..."):
                    groups = get_group_names(os.getenv("GITHUB_TOKEN"), ORG_NAME, slug)
                
                # Initialize issues, prs, and milestones here with default values
                issues, prs, milestones, commit_details = [], [], {}, {}
                user_activity_counts = {}

                if groups:
                    selected_group = st.selectbox("Select Group", groups, format_func=lambda x: f"👥 {x}")
                    repo_name = f"{slug}-{selected_group}"

                    # Fetch and display data
                    with st.spinner("Fetching activity data..."):
                        issues, prs, milestones, commit_details = fetch_activity_data(
                            os.getenv("GITHUB_TOKEN"),
                            ORG_NAME,
                            repo_name
                        )
                        user_activity_counts = display_dashboard(issues, prs, milestones, commit_details)
                else:
                    st.warning("⚠️ No groups available for this assignment")
            else:
                st.warning("⚠️ No assignments available for this classroom")
        else:
            st.warning("⚠️ No classrooms available")

        # Display Accepted and Submissions counts
        if assignments and selected_assignment:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"<div class='metric-container'>Accepted: {selected_assignment['accepted']}</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div class='metric-container'>Submissions: {selected_assignment['submissions']}</div>", unsafe_allow_html=True)

        # Store the current dashboard state for report generation
        st.session_state.dashboard_data = {
            "issues": issues,
            "prs": prs,
            "milestones": milestones,
            "commit_details": commit_details,
            "selected_classroom": selected_classroom if classrooms else None,
            "selected_assignment": selected_title if assignments else None,
            "selected_group": selected_group if groups else None,
            "accepted": selected_assignment['accepted'] if assignments and selected_assignment else None,
            "submissions": selected_assignment['submissions'] if assignments and selected_assignment else None,
            "user_activity_counts": user_activity_counts
        }

    with report_tab:
            # Generate the report based on the stored dashboard data
        if st.session_state.get("dashboard_data"):
            report_data = st.session_state.dashboard_data
            html_report = generate_html_report(report_data)

            if html_report:
                st.download_button(
                    label="Download HTML Report",
                    data=html_report.encode('utf-8'),
                    file_name="activity_report.html",
                    mime="text/html"
                )
            else:
                st.error("Failed to generate HTML report.")
        else:
            st.warning("No dashboard data available to generate the report. Please view the dashboard first.")

    # Logout
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.username = None
        st.session_state.access_token = None
        st.experimental_rerun()

def generate_html_report(data):
    try:
        # Get most and least active users if available
        most_active_user = "N/A"
        most_active_count = 0
        least_active_user = "N/A"
        least_active_count = 0
        if 'user_activity_counts' in data and data['user_activity_counts']:
            user_activity_counts = data['user_activity_counts']
            most_active_user = max(user_activity_counts, key=user_activity_counts.get)
            most_active_count = user_activity_counts[most_active_user]
            least_active_user = min(user_activity_counts, key=user_activity_counts.get)
            least_active_count = user_activity_counts[least_active_user]

        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>GitHub Activity Report</title>
            <style>
                :root {{
                    --primary-color: #3498db;
                    --secondary-color: #2ecc71;
                    --danger-color: #e74c3c;
                    --dark-color: #2c3e50;
                    --light-color: #ecf0f1;
                    --gray-color: #95a5a6;
                }}
                
                * {{
                    box-sizing: border-box;
                    margin: 0;
                    padding: 0;
                }}
                
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f5f7fa;
                    padding: 20px;
                }}
                
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }}
                
                header {{
                    background: linear-gradient(135deg, var(--primary-color), var(--dark-color));
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                
                h1 {{
                    font-size: 2.5rem;
                    margin-bottom: 10px;
                }}
                
                .report-date {{
                    font-size: 1rem;
                    opacity: 0.9;
                }}
                
                .summary-section {{
                    padding: 30px;
                    background-color: white;
                    border-bottom: 1px solid #eee;
                }}
                
                .summary-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-top: 20px;
                }}
                
                .summary-card {{
                    background: white;
                    border-radius: 8px;
                    padding: 20px;
                    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.08);
                    border-top: 4px solid var(--primary-color);
                }}
                
                .summary-card h3 {{
                    color: var(--dark-color);
                    margin-bottom: 10px;
                    font-size: 1.1rem;
                }}
                
                .summary-card p {{
                    font-size: 1.8rem;
                    font-weight: bold;
                    color: var(--primary-color);
                }}
                
                .activity-section {{
                    padding: 30px;
                }}
                
                .section-title {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 20px;
                    padding-bottom: 10px;
                    border-bottom: 2px solid var(--light-color);
                }}
                
                .section-title h2 {{
                    color: var(--dark-color);
                    font-size: 1.5rem;
                }}
                
                .badge {{
                    background-color: var(--primary-color);
                    color: white;
                    padding: 5px 10px;
                    border-radius: 20px;
                    font-size: 0.9rem;
                }}
                
                .activity-list {{
                    list-style: none;
                }}
                
                .activity-item {{
                    background: white;
                    padding: 20px;
                    margin-bottom: 15px;
                    border-radius: 8px;
                    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
                    border-left: 4px solid var(--primary-color);
                    transition: transform 0.2s, box-shadow 0.2s;
                }}
                
                .activity-item:hover {{
                    transform: translateY(-3px);
                    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
                }}
                
                .activity-item h3 {{
                    color: var(--dark-color);
                    margin-bottom: 10px;
                }}
                
                .meta {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 15px;
                    margin-bottom: 10px;
                    font-size: 0.9rem;
                    color: var(--gray-color);
                }}
                
                .meta span {{
                    display: flex;
                    align-items: center;
                }}
                
                .meta i {{
                    margin-right: 5px;
                }}
                
                .btn {{
                    display: inline-block;
                    background-color: var(--primary-color);
                    color: white;
                    padding: 8px 15px;
                    border-radius: 5px;
                    text-decoration: none;
                    font-size: 0.9rem;
                    margin-top: 10px;
                    transition: background-color 0.2s;
                }}
                
                .btn:hover {{
                    background-color: #2980b9;
                }}
                
                .user-stats {{
                    display: flex;
                    justify-content: space-between;
                    margin-top: 30px;
                }}
                
                .user-stat-card {{
                    flex: 0 0 48%;
                    background: white;
                    border-radius: 8px;
                    padding: 20px;
                    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.08);
                }}
                
                .most-active-card {{
                    border-top: 4px solid var(--secondary-color);
                }}
                
                .least-active-card {{
                    border-top: 4px solid var(--danger-color);
                }}
                
                .user-stat-card h3 {{
                    color: var(--dark-color);
                    margin-bottom: 15px;
                    font-size: 1.2rem;
                }}
                
                .user-stat {{
                    font-size: 1.5rem;
                    font-weight: bold;
                }}
                
                .most-active-stat {{
                    color: var(--secondary-color);
                }}
                
                .least-active-stat {{
                    color: var(--danger-color);
                }}
                
                .commit-stats {{
                    display: flex;
                    gap: 10px;
                    margin-top: 15px;
                }}
                
                .stat-pill {{
                    background-color: #f0f7fd;
                    padding: 5px 10px;
                    border-radius: 20px;
                    font-size: 0.8rem;
                }}
                
                .additions {{
                    color: var(--secondary-color);
                }}
                
                .deletions {{
                    color: var(--danger-color);
                }}
                
                footer {{
                    text-align: center;
                    padding: 20px;
                    background-color: var(--dark-color);
                    color: white;
                    font-size: 0.9rem;
                }}
                
                @media (max-width: 768px) {{
                    .summary-grid {{
                        grid-template-columns: 1fr;
                    }}
                    
                    .user-stats {{
                        flex-direction: column;
                    }}
                    
                    .user-stat-card {{
                        margin-bottom: 20px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>GitHub Activity Report</h1>
                    <p class="report-date">Generated on {datetime.datetime.now().strftime("%B %d, %Y")}</p>
                </header>
                
                <section class="summary-section">
                    <h2>Project Summary</h2>
                    <div class="summary-grid">
                        <div class="summary-card">
                            <h3>Classroom</h3>
                            <p>{data.get('selected_classroom', 'N/A')}</p>
                        </div>
                        <div class="summary-card">
                            <h3>Assignment</h3>
                            <p>{data.get('selected_assignment', 'N/A')}</p>
                        </div>
                        <div class="summary-card">
                            <h3>Group</h3>
                            <p>{data.get('selected_group', 'N/A')}</p>
                        </div>
                        <div class="summary-card">
                            <h3>Accepted</h3>
                            <p>{data.get('accepted', '0')}</p>
                        </div>
                        <div class="summary-card">
                            <h3>Submissions</h3>
                            <p>{data.get('submissions', '0')}</p>
                        </div>
                    </div>
                    
                    <div class="user-stats">
                        <div class="user-stat-card most-active-card">
                            <h3>🌟 Most Active Contributor</h3>
                            <p class="user-stat most-active-stat">{most_active_user}</p>
                            <p>{most_active_count} activities</p>
                        </div>
                        <div class="user-stat-card least-active-card">
                            <h3>🐢 Least Active Contributor</h3>
                            <p class="user-stat least-active-stat">{least_active_user}</p>
                            <p>{least_active_count} activities</p>
                        </div>
                    </div>
                </section>
                
                <section class="activity-section">
                    <div class="section-title">
                        <h2>Issues</h2>
                        <span class="badge">{len(data.get('issues', []))} total</span>
                    </div>
                    
                    {f'<ul class="activity-list">' + 
                     ''.join([f'''
                        <li class="activity-item">
                            <h3>{issue['title']}</h3>
                            <div class="meta">
                                <span><i>👤</i> {issue['user']}</span>
                                <span><i>📅</i> {issue['created_at'].split('T')[0]}</span>
                            </div>
                            <a href="{issue['url']}" class="btn" target="_blank">View Issue</a>
                        </li>
                     ''' for issue in data.get('issues', [])]) + '</ul>'
                     if data.get('issues') else '<p>No issues to display</p>'}
                </section>
                
                <section class="activity-section">
                    <div class="section-title">
                        <h2>Pull Requests</h2>
                        <span class="badge">{len(data.get('prs', []))} total</span>
                    </div>
                    
                    {f'<ul class="activity-list">' + 
                     ''.join([f'''
                        <li class="activity-item">
                            <h3>{pr['title']}</h3>
                            <div class="meta">
                                <span><i>👤</i> {pr['user']}</span>
                                <span><i>📅</i> {pr['created_at'].split('T')[0]}</span>
                                <span><i>🔍</i> {pr['state'].capitalize()}</span>
                            </div>
                            <a href="{pr['url']}" class="btn" target="_blank">View Pull Request</a>
                        </li>
                     ''' for pr in data.get('prs', [])]) + '</ul>'
                     if data.get('prs') else '<p>No pull requests to display</p>'}
                </section>
                
                <section class="activity-section">
                    <div class="section-title">
                        <h2>Milestones</h2>
                        <span class="badge">{len(data.get('milestones', {}))} total</span>
                    </div>
                    
                    {f'<ul class="activity-list">' + 
                     ''.join([f'''
                        <li class="activity-item">
                            <h3>{title}</h3>
                            <div class="meta">
                                <span><i>👤</i> {milestone['creator']}</span>
                                <span><i>📅</i> {milestone['due_on'].split('T')[0] if milestone['due_on'] else 'No due date'}</span>
                                <span><i>🔍</i> {milestone['state'].capitalize()}</span>
                            </div>
                            <p>{milestone['description']}</p>
                            <a href="{milestone['url']}" class="btn" target="_blank">View Milestone</a>
                        </li>
                     ''' for title, milestone in data.get('milestones', {}).items()]) + '</ul>'
                     if data.get('milestones') else '<p>No milestones to display</p>'}
                </section>
                
                <section class="activity-section">
                    <div class="section-title">
                        <h2>Commits</h2>
                        <span class="badge">{sum(len(details['commits']) for details in data.get('commit_details', {}).values()) if data.get('commit_details') else 0} total</span>
                    </div>
                    
                    {f'<ul class="activity-list">' + 
                     ''.join([f'''
                        <li class="activity-item">
                            <h3>{author}</h3>
                            <div class="commit-stats">
                                <span class="stat-pill">Commits: {len(details['commits'])}</span>
                                <span class="stat-pill additions">Additions: {details['additions']}</span>
                                <span class="stat-pill deletions">Deletions: {details['deletions']}</span>
                            </div>
                        </li>
                     ''' for author, details in data.get('commit_details', {}).items()]) + '</ul>'
                     if data.get('commit_details') else '<p>No commit data to display</p>'}
                </section>
                
                <footer>
                    <p>Report generated by GitHub Classroom Dashboard</p>
                </footer>
            </div>
        </body>
        </html>
        """
        return html_content

    except Exception as e:
        st.error(f"Error generating HTML report: {e}")
        return None

def main():
    if not st.session_state.get("logged_in", False):
        st.warning("Please login first")
        return
    
    if st.session_state.get("role") == "teacher":
        teacher_view()
    else:
        st.error("Unauthorized access")

if __name__ == "__main__":
    main()