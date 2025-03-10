import streamlit as st
import time

# CSS to hide the sidebar
css = '''
<style>
    [data-testid="stSidebarNav"] {
        display: none;
    }
</style>
'''
st.markdown(css, unsafe_allow_html=True)

# Simulated user database (username: password)
USER_DATABASE = {
    "user1": "password1",
    "user2": "password2"
}

def login(username, password):
    """Check if the username and password match the records."""
    return USER_DATABASE.get(username) == password

# Streamlit UI
image_path = "logo_comp.png"  # Replace with your image path
st.image(image_path, use_container_width=True)  # Display the image at the top

st.title("Login Page")

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None

# Show role selection only if the user is not logged in
if not st.session_state.logged_in:
    role_selection = st.selectbox("Select your role", ["Teacher", "Student"])
    if role_selection != "Select":
        st.session_state.role = role_selection

# Login page
if not st.session_state.logged_in and st.session_state.role is not None:
    username_input = st.text_input("Username")
    password_input = st.text_input("Password", type="password")

    if st.button("Login"):
        if login(username_input, password_input):
            st.success("Login successful! Redirecting...")
            time.sleep(2)  # Wait for 2 seconds

            # Write role, username, and password to list.txt
            with open("list.txt", "a") as f:
                f.write(f"{st.session_state.role}, {username_input}, {password_input}\n")

            st.session_state.logged_in = True  # Set logged in state
            st.rerun()  # Rerun to show the role-specific content
        else:
            st.error("Invalid username or password.")
else:
    # Role-specific content after successful login
    if st.session_state.role == "Teacher":
        st.write("You have access to teacher resources.")
        st.switch_page("pages/GIt_Function.py")
        time.sleep(1)
    elif st.session_state.role == "Student":
        st.write("You have access to student resources.")
        st.switch_page("pages/GIt_Function.py")
        time.sleep(1)

        # Add student-specific content here

    # Show logout button only after login
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None  # Reset role
        st.rerun()  # Rerun to go back to the login page