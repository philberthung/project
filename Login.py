import streamlit as st
import webbrowser
import requests
import urllib.parse
from streamlit.web.server import Server
import time
import pandas as pd
from pymongo import MongoClient
from pymongo.server_api import ServerApi

st.set_page_config(page_title="Login", page_icon=":guardsman:", layout="wide", initial_sidebar_state="collapsed")

# MongoDB connection
uri = "mongodb+srv://nata:isd2025@isdcluster.jnn9ctb.mongodb.net/?appName=ISDcluster"
client = MongoClient(uri, server_api=ServerApi('1'))

# Check connection
try:
    client.admin.command('ping')
except Exception as e:
    st.error(f"Could not connect to MongoDB: {e}")

# CSS to hide the sidebar
css = '''
<style>
    [data-testid="stSidebarNav"] {
        display: none;
    }
</style>
'''
st.markdown(css, unsafe_allow_html=True)

# Streamlit UI
image_path = "logo_comp.png"  # Replace with your image path
st.image(image_path, use_container_width=True)  # Display the image at the top

# Access the database and collection
db = client.students_database  # Replace with your database name
students_collection = db.students  # Replace with your collection name

# Load student data
students_data = list(students_collection.find({}))  # Fetch all students
students_df = pd.DataFrame(students_data)

# Create a user database with roles and permissions
USER_DATABASE = {}
for i in range(len(students_df)):
    USER_DATABASE[students_df['netid'][i]] = {
        'password': students_df['password'][i],
        'role': students_df['role'][i],
        'permission': students_df['permission'][i]
    }

# OAuth settings
client_id = "Ov23liTxryC5DAIzStP8"
client_secret = "bf372b10e0e6064de4bf1c99db9f60deb02376a3"
redirect_uri = "http://localhost:8501"  # Replace with your redirect URI
token_url = "https://github.com/login/oauth/access_token"
auth_url = f"https://github.com/login/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}"

# Streamlit app
st.title("GitHub Classroom Management")

# Initialize session state
if "auth_code" not in st.session_state:
    st.session_state.auth_code = None
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "query_params" not in st.session_state:
    st.session_state.query_params = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None
if "permission" not in st.session_state:
    st.session_state.permission = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None  # Initialize user_email
if "netid" not in st.session_state:
    st.session_state.netid = None

# Function to get query parameters from URL
def get_query_params():
    try:
        # Access the current request's query parameters
        query_params = st.query_params
        return query_params
    except:
        return None

# --- OAuth Flow ---
# Step 1: Button to start OAuth flow
if not st.session_state.auth_code and not st.session_state.access_token and not st.session_state.logged_in:
    st.subheader("Connect Github account")
    if st.button("Login with GitHub"):
        st.write("Opening GitHub authorization page...")
        webbrowser.open(auth_url)
        st.write("Please authorize the app. Waiting for redirect...")

# Step 2: Automatically capture the code from redirect
if not st.session_state.access_token and not st.session_state.logged_in:
    query_params = get_query_params()
    if query_params and "code" in query_params:
        st.session_state.auth_code = query_params["code"]
        # Clear query params to prevent re-processing
        st.query_params.clear()

# Step 3: Exchange code for access token
if st.session_state.auth_code and not st.session_state.access_token and not st.session_state.logged_in:
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
        scope = token_data.get("scope")
        token_type = token_data.get("token_type")

        if access_token:
            st.session_state.access_token = access_token
            st.success("GitHub Login successful!")
        else:
            st.error("Failed to retrieve access token.")
            st.write("Response:", token_data)
    except Exception as e:
        st.error(f"Error fetching token: {e}")

# --- MongoDB Login ---
if st.session_state.access_token and not st.session_state.logged_in:
    st.subheader("Login the System")
    username_input = st.text_input("Username (NetID)")
    password_input = st.text_input("Password", type="password")

    if st.button("Login"):
        if username_input in USER_DATABASE and USER_DATABASE[username_input]['password'] == password_input:
            st.success("Login successful! Redirecting...")
            time.sleep(2)  # Wait for 2 seconds

            # Get the role and permission from the user database
            st.session_state.role = USER_DATABASE[username_input]['role']
            st.session_state.permission = USER_DATABASE[username_input]['permission']
            st.session_state.netid = username_input  # Store the username (netid)

            # Write role, username, and password to list.txt
            with open("list.txt", "a") as f:
                f.write(f"{st.session_state.role}, {username_input}, {password_input}\n")

            st.session_state.logged_in = True  # Set logged in state
            st.rerun()  # Rerun to show the role-specific content
        else:
            st.error("Invalid username or password.")

# --- After Login (GitHub OAuth + MongoDB) ---
if st.session_state.logged_in:
    st.write(f"You are logged in as: {st.session_state.netid} with role: {st.session_state.role}")

    # Role-specific content after successful login
    if st.session_state.role == "teacher":
        st.write("You have access to teacher resources.")
        st.switch_page("pages/Details_of_User.py")  # Switch to teacher's page
        time.sleep(1)
    elif st.session_state.role == "student":
        st.write("You have access to student resources.")
        # Switch based on permission
        if st.session_state.permission == "leader":
            st.switch_page("pages/Details_of_User.py")  # Switch to student's page
        elif st.session_state.permission == "member":
            st.switch_page("pages/Details_of_User.py")
        else:
            st.error("You do not have permission to access this resource.")
        time.sleep(1)

    # Show logout button only after login
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None  # Reset role
        st.session_state.permission = None  # Reset permission
        st.session_state.user_email = None  # Reset user_email
        st.session_state.access_token = None # Reset access token
        st.session_state.auth_code = None # Reset auth code
        st.rerun()  # Rerun to go back to the login page