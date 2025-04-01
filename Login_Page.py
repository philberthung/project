import streamlit as st
import time
import pandas as pd
from pymongo import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://nata:isd2025@isdcluster.jnn9ctb.mongodb.net/?appName=ISDcluster"
client = MongoClient(uri, server_api=ServerApi('1'))

try:
    client.admin.command('ping')
    print("Connected to MongoDB!")
except Exception as e:
    print(f"Connection failed: {e}")

# CSS to hide the sidebar
css = '''
<style>
    [data-testid="stSidebarNav"] {
        display: none;
    }
</style>
'''
st.markdown(css, unsafe_allow_html=True)

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

# Streamlit UI
image_path = "logo_comp.png"  # Replace with your image path
st.image(image_path, use_container_width=True)  # Display the image at the top

st.title("Login Page")

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None
if "permission" not in st.session_state:
    st.session_state.permission = None

# Login page
if not st.session_state.logged_in:
    username_input = st.text_input("Username")
    password_input = st.text_input("Password", type="password")

    if st.button("Login"):
        if username_input in USER_DATABASE and USER_DATABASE[username_input]['password'] == password_input:
            st.success("Login successful! Redirecting...")
            time.sleep(2)

            # Store role, permission, and netid in session state
            st.session_state.role = USER_DATABASE[username_input]['role']
            st.session_state.permission = USER_DATABASE[username_input]['permission']
            st.session_state.netid = username_input  # Add this line

            # Write to list.txt
            with open("list.txt", "a") as f:
                f.write(f"{st.session_state.role}, {username_input}, {password_input}\n")

            st.session_state.logged_in = True
            st.rerun()
        
        else:
            st.error("Invalid username or password.")

else:
    # Role-specific content after successful login
    if st.session_state.role == "teacher":
        st.write("You have access to teacher resources.")
        st.switch_page("pages/Assignment.py")  # Switch to teacher's page
        time.sleep(1)
        
    elif st.session_state.role == "student":
        st.write("You have access to student resources.")
        # Switch based on permission
        if st.session_state.permission == "leader":
            st.switch_page("pages/Group.py")  # Switch to student's page
        elif st.session_state.permission == "member":
            st.switch_page("pages/GIt_Function.py")
        else:
            st.error("You do not have permission to access this resource.")
        time.sleep(1)

    # Show logout button only after login
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.permission = None
        st.session_state.netid = None
        st.switch_page("Login_Page.py")