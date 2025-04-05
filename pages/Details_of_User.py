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
db = client.students_database  # Replace with your database name
students_collection = db.students  # Replace with your collection name

# Load student data
students_data = list(students_collection.find({}))  # Fetch all students
students_df = pd.DataFrame(students_data)

# Streamlit UI
st.title("User Profiles")

# Display user info
if "username" not in st.session_state:
    st.session_state.username = ""  # Initialize username
st.sidebar.write(f"Logged in as: {st.session_state.username}")
st.sidebar.write(f"Role: {st.session_state.role}")

# Logout button
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None
    st.switch_page("Login.py")


# Check if the user is logged in and netid is available in session state
if 'logged_in' in st.session_state and st.session_state.logged_in and 'netid' in st.session_state:
    netid = st.session_state.netid

    # Filter the DataFrame to only show the logged-in user's information
    user_data = students_df[students_df['netid'] == netid]  # Assuming 'netid' stores the login email

    with st.container(border=True):  # Create a container for the content
        if not user_data.empty:
            # Create columns within the container
            col1, col2 = st.columns([2, 1])

            with col1:                
                st.markdown(
                    f"""
                    <div style="border: 1px; padding: 10px; border-radius: 5px; justify-content: center; align-items: center; flex-direction: column;">
                        <h2>{user_data['name'].iloc[0]}</h2>
                        <p><strong>NetID:</strong> {user_data['netid'].iloc[0]}</p>
                        <p><strong>Role:</strong> {user_data['role'].iloc[0]}</p>
                        <p><strong>Email:</strong> {user_data['email'].iloc[0]}</p>
                    </div>
                    """, unsafe_allow_html=True
                )
            
            with col2:
                # Display an image with square styling
                image_path = "pages/cat.jpg"  # Use the relative path
                st.image(image_path, use_container_width=True, width=150)
                   
        else:
            st.warning("No data found for the logged-in user.")
    
else:
    st.info("Please log in to view your information.")
