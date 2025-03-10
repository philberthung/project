import streamlit as st
import time
def main():
    st.title("Page 1")
    st.write("Welcome to Page 1!")
    if st.button("Go to Page 2"):
        st.switch_page("pages/app.py")
        time.sleep(1)

if __name__ == "__main__":
    main()