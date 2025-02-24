import streamlit as st
import requests

# GitHub API setup
GITHUB_API_URL = "https://api.github.com/repos/philberthung/project/issues"
GITHUB_TOKEN = "YOUR_GITHUB_TOKEN"  # Replace with your GitHub token

# Function to create a GitHub issue
def create_github_issue(title, body):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    issue = {
        "title": title,
        "body": body
    }
    response = requests.post(GITHUB_API_URL, json=issue, headers=headers)
    return response

# Streamlit app layout
st.title("Student Input Form")
student_input = st.text_area("Write your input here:")

if st.button("Submit"):
    if student_input:
        response = create_github_issue("Student Input", student_input)
        if response.status_code == 201:
            st.success("Issue created successfully!")
        else:
            st.error("Failed to create issue. Please try again.")
    else:
        st.warning("Please enter something before submitting.")