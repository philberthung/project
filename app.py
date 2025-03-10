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

def main():
    st.title("Page 2")
    st.write("Welcome to Page 2!")

    # No need to clear the sidebar since it's hidden
    # st.sidebar.empty()

    if st.button("Go to Page 1"):
        st.switch_page("test/login.py")
        time.sleep(1)

if __name__ == "__main__":
    main()