import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")

st.set_page_config(page_title="AI Meeting Copilot", page_icon="🤖", layout="wide")

if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


col_left, col_mid, col_right = st.columns([1, 2, 1])

with col_mid:
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    
    st.markdown("<h1><span style='font-family: \"Segoe UI Emoji\", sans-serif;'>🤖</span> AI Meeting Copilot</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color: #A0A0A0; font-size: 1.05rem; line-height: 1.5;'>"
        "Automatically extract executive summaries, key decisions, action items, and open questions—then chat directly with your meeting transcript. <br>"
        "</p>", 
        unsafe_allow_html=True
    )
    st.markdown("<br>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🌐 YouTube URL", "📤 Upload File"])
    
    with tab1:
        st.write("Provide the URL of a publicly hosted meeting, webinar, or presentation  for instant AI analysis.")
        source_input = st.text_input("YouTube Link:", placeholder="https://youtube.com/...", label_visibility="collapsed")
        
        if st.button("Analyze URL", type="primary", use_container_width=True):
            if not source_input:
                st.warning("Please enter a valid link.")
            else:
                with st.spinner("Downloading and analyzing... This may take a few minutes."):
                    try:
                        response = requests.post(f"{API_URL}/api/analyze", json={"source": source_input})
                        if response.status_code == 200:
                            st.session_state.analysis_results = response.json()
                            st.session_state.chat_history = [] 
                        else:
                            st.error(f"Backend Error: {response.text}")
                    except Exception as e:
                        st.error(f"Connection failed: {e}")


    with tab2:
        st.write("Securely upload your local meeting recording (audio or video) for instant AI analysis.")
        
        
        uploaded_file = st.file_uploader(
            "Drag and drop file here (Max size: 1 GB)", 
            type=["mp4", "mp3", "wav", "m4a", "mov"]
        )
        
        if st.button("Analyze File", type="primary", use_container_width=True):
            if not uploaded_file:
                st.warning("Please upload a file first.")
            else:
                with st.spinner(f"Securely uploading {uploaded_file.name} to server..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        response = requests.post(f"{API_URL}/api/analyze-upload", files=files)
                        
                        if response.status_code == 200:
                            st.session_state.analysis_results = response.json()
                            st.session_state.chat_history = []
                        else:
                            st.error(f"Backend Error: {response.text}")
                    except Exception as e:
                        st.error(f"Connection failed: {e}")


if st.session_state.analysis_results:
    
    st.divider() 
    
    results = st.session_state.analysis_results
    
    
    st.header(results.get("title", "Meeting Summary"))
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Executive Summary")
        st.write(results.get("summary", "No summary available."))
        
        st.subheader("Key Decisions")
        st.write(results.get("key_decisions", "No decisions recorded."))
        
    with col2:
        st.subheader("Action Items")
        st.write(results.get("action_items", "No action items recorded."))
        
        st.subheader("Open Questions")
        st.write(results.get("open_questions", "No open questions recorded."))
        
    st.divider()
    
    st.markdown("<h1><span style='font-family: \"Segoe UI Emoji\", sans-serif;'>🤖</span> Chat with this Meeting</h1>", unsafe_allow_html=True)
    
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            
    if prompt := st.chat_input("E.g., 'What was the deadline for the marketing phase?'"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Searching knowledge base..."):
                try:
                    chat_res = requests.post(f"{API_URL}/api/chat", json={"question": prompt})
                    if chat_res.status_code == 200:
                        answer = chat_res.json().get("answer", "No answer provided.")
                        st.write(answer)
                        st.session_state.chat_history.append({"role": "assistant", "content": answer})
                    else:
                        st.error("Failed to get a valid response from the server.")
                except Exception as e:
                    st.error(f"Error querying backend: {e}")