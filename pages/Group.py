import streamlit as st
import pandas as pd

# Initialize session state for members and potential members
if 'members' not in st.session_state:
    st.session_state.members = pd.DataFrame(columns=["Email"])
    
if 'potential_members' not in st.session_state:
    # Example list of potential members (this could come from a database)
    st.session_state.potential_members = ["alice@example.com", "bob@example.com", "charlie@example.com"]

# Function to invite selected members
def invite_member(selected_email):
    new_member = pd.DataFrame({"Email": [selected_email]})
    st.session_state.members = pd.concat([st.session_state.members, new_member], ignore_index=True)

# Streamlit UI
st.title("Group Member Invitation")

# Member invitation form
st.subheader("Invite Group Members")
selected_member = st.selectbox("Select a member to invite", st.session_state.potential_members)

invite_submitted = st.button("Invite Member")
if invite_submitted:
    invite_member(selected_member)
    st.success(f"Member {selected_member} invited successfully!")

# Display invited members
st.subheader("Invited Members")
st.dataframe(st.session_state.members)


st.sidebar.button("Logout")