import streamlit as st
import requests
import os

# Set up page config
st.set_page_config(page_title="Student Engagement Analyzer", page_icon="🎓", layout="wide")

# Get backend URL from Streamlit secrets, environment variables, or default placeholder
# You will set this in the Streamlit Cloud dashboard
BACKEND_URL = os.getenv("BACKEND_URL", "https://your-username-student-engagement.hf.space")

def check_backend_connection():
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        if response.status_code == 200:
            return True, "Backend is connected and healthy! 🟢"
        else:
            return False, f"Backend returned status {response.status_code} 🟡"
    except Exception as e:
        return False, f"Could not connect to backend. Please check the URL. 🔴"

def main():
    st.title("🎓 Student Engagement Analyzer")
    st.markdown("Upload a classroom video to categorize student behavior into engagement levels (E1-E4).")
    
    # Sidebar for configuration and connection status
    with st.sidebar:
        st.header("⚙️ Configuration")
        st.caption("Backend API endpoint:")
        st.code(BACKEND_URL, language="text")
        
        if st.button("Test Backend Connection"):
            with st.spinner("Pinging Hugging Face Space..."):
                is_connected, msg = check_backend_connection()
                if is_connected:
                    st.success(msg)
                else:
                    st.error(msg)
                    st.markdown("*(Make sure your Hugging Face Space is public or you have the correct authentication headers set up)*")
                    
        st.markdown("---")
        st.markdown("### Deployment Instructions")
        st.markdown("1. Go to Streamlit Cloud Dashboard.")
        st.markdown("2. Edit your app settings -> **Secrets**.")
        st.markdown("3. Add `BACKEND_URL = \"your-huggingface-space-url\"`")

    # Main content area
    st.write("### Video Upload")
    uploaded_file = st.file_uploader("Choose a video file to analyze...", type=["mp4", "avi", "mov"])
    
    if uploaded_file is not None:
        st.video(uploaded_file)
        
        if st.button("Analyze Video", type="primary", use_container_width=True):
            st.info("Initiating analysis pipeline...")
            
            with st.spinner("Uploading and analyzing... This may take a few minutes depending on the video length."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(f"{BACKEND_URL}/analyze", files=files, timeout=300) # 5 min timeout
                    
                    if response.status_code == 200:
                        st.success("Analysis complete!")
                        # Save the returned video temporarily to display it
                        with open("output_video.mp4", "wb") as f:
                            f.write(response.content)
                        st.video("output_video.mp4")
                        st.balloons()
                    else:
                        st.error(f"Error from server: {response.status_code} - {response.text}")
                except Exception as e:
                    st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
