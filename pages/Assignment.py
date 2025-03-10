import streamlit as st
import pandas as pd

# Initialize an empty DataFrame to store assignments
if 'assignments' not in st.session_state:
    st.session_state.assignments = pd.DataFrame(columns=["Title", "Description", "Deadline"])

# Function to add assignments
def add_assignment(title, description, deadline):
    new_assignment = pd.DataFrame({"Title": [title], "Description": [description], "Deadline": [deadline]})
    st.session_state.assignments = pd.concat([st.session_state.assignments, new_assignment], ignore_index=True)

# Streamlit UI
st.title("Assignment Management")

# Make the form full width by using a container
with st.container():
    with st.form("assignment_form"):
        st.markdown("<style>.stTextInput, .stTextArea, .stDateInput { width: 100%; }</style>", unsafe_allow_html=True)
        
        title = st.text_input("Assignment Title")
        description = st.text_area("Assignment Description")
        deadline = st.date_input("Deadline")

        # Submit button
        submitted = st.form_submit_button("Create Assignment")
        if submitted:
            add_assignment(title, description, deadline)
            st.success("Assignment created successfully!")

# Display current assignments
st.subheader("Current Assignments")
st.dataframe(st.session_state.assignments)

st.sidebar.button("Logout")