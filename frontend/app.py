import streamlit as st

def main():
    st.set_page_config(page_title="Student Engagement Analyzer", layout="wide")
    st.title("Student Engagement Analyzer")
    st.write("Welcome to the Student Engagement Analyzer frontend.")
    st.info("Upload a classroom video to categorize student behavior into engagement levels (E1-E4).")

if __name__ == "__main__":
    main()
