import streamlit as st
import requests
import json
from io import BytesIO
import base64
from gtts import gTTS
from datetime import datetime

# Set up the page with better UI
st.set_page_config(
    page_title="Voice Bot powered by Groq and gTTS",
    page_icon="🔊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
        .stTextInput input, .stTextArea textarea {
            border-radius: 20px !important;
            padding: 10px !important;
        }
        .stButton button {
            border-radius: 20px !important;
            background-color: #4CAF50 !important;
            color: white !important;
            font-weight: bold !important;
            border: none !important;
            padding: 10px 24px !important;
        }
        .stButton button:hover {
            background-color: #45a049 !important;
        }
        .chat-message {
            padding: 12px 16px;
            border-radius: 20px;
            margin-bottom: 8px;
            max-width: 80%;
        }
        .user-message {
            background-color: #e3f2fd;
            margin-left: auto;
            border-bottom-right-radius: 5px !important;
        }
        .bot-message {
            background-color: #f1f1f1;
            margin-right: auto;
            border-bottom-left-radius: 5px !important;
        }
        .message-time {
            font-size: 0.8em;
            color: #666;
            margin-top: 4px;
        }
        .stMarkdown h1 {
            text-align: center;
            color: #2c3e50;
        }
        .sidebar .sidebar-content {
            background-color: #f8f9fa;
        }
    </style>
""", unsafe_allow_html=True)

# App title with better styling
st.markdown("<h1 style='text-align: center; color: #2c3e50;'>Voice Bot powered by Groq and gTTS</h1>", unsafe_allow_html=True)
st.markdown("---")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize audio state
if "audio_played" not in st.session_state:
    st.session_state.audio_played = False

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")
    
    # API Key
    groq_api_key = st.text_input("Enter your Groq API Key:", type="password", help="Get your API key from Groq Cloud")
    st.markdown("[Get Groq API Key](https://console.groq.com/keys)")
    
    st.markdown("---")
    
    # Voice settings
    st.subheader("🎙️ Voice Settings")
    col1, col2 = st.columns(2)
    with col1:
        language = st.selectbox(
            "Language",
            ["en", "es", "fr", "de", "it", "pt", "hi", "ja"],
            index=0,
            help="Select the language for voice output"
        )
    with col2:
        slow_speech = st.checkbox("Slow Speech", False, help="Enable for slower speech")
    
    st.markdown("---")
    
    # Clear chat button
    if st.button("🧹 Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # Display message content
        st.markdown(f"<div class='chat-message {'user-message' if message['role'] == 'user' else 'bot-message'}'>"
                    f"{message['content']}"
                    f"<div class='message-time'>{message['time']}</div>"
                    f"</div>", unsafe_allow_html=True)
        
        # Display audio player for bot responses
        if message["role"] == "assistant" and "audio_bytes" in message:
            audio_bytes = BytesIO(base64.b64decode(message["audio_bytes"]))
            st.audio(audio_bytes, format="audio/mp3")

# Accept user input
if prompt := st.chat_input("Type your message here..."):
    if not groq_api_key:
        st.error("Please enter your Groq API key in the sidebar.")
    else:
        # Chat history
        current_time = datetime.now().strftime("%H:%M")
        st.session_state.messages.append({"role": "user", "content": prompt, "time": current_time})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(f"<div class='chat-message user-message'>"
                        f"{prompt}"
                        f"<div class='message-time'>{current_time}</div>"
                        f"</div>", unsafe_allow_html=True)
        
        with st.spinner("Voice Bot is thinking..."):
            try:
                headers = {
                    "Authorization": f"Bearer {groq_api_key}",
                    "Content-Type": "application/json"
                }
                
                # Include chat history for context
                messages_for_api = [
                    {"role": msg["role"], "content": msg["content"]} 
                    for msg in st.session_state.messages 
                    if msg["role"] in ["user", "assistant"]
                ]
                
                payload = {
                    "messages": messages_for_api,
                    "model": "llama-3.3-70b-versatile"
                }
                
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                response.raise_for_status()
                result = response.json()
                
                if "choices" in result and len(result["choices"]) > 0:
                    answer = result["choices"][0]["message"]["content"]
                    current_time = datetime.now().strftime("%H:%M")
                    
                    # Convert text to speech
                    tts = gTTS(text=answer, lang=language, slow=slow_speech)
                    audio_bytes = BytesIO()
                    tts.write_to_fp(audio_bytes)
                    audio_bytes.seek(0)
                    
                    # Audio as base64
                    audio_base64 = base64.b64encode(audio_bytes.read()).decode()
                    
                    # chat history
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": answer, 
                        "time": current_time,
                        "audio_bytes": audio_base64
                    })
                    
                    # Display response
                    with st.chat_message("assistant"):
                        st.markdown(f"<div class='chat-message bot-message'>"
                                    f"{answer}"
                                    f"<div class='message-time'>{current_time}</div>"
                                    f"</div>", unsafe_allow_html=True)
                        
                        # Displaying Audio player
                        audio_bytes = BytesIO(base64.b64decode(audio_base64))
                        st.audio(audio_bytes, format="audio/mp3")
                        
                else:
                    st.error("No response from Groq API.")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"Error calling Groq API: {str(e)}")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

# Instructions to use the application
with st.sidebar:
    st.markdown("---")
    st.subheader("ℹ️ How to use")
    st.markdown("""
    1. Enter your Groq API key
    2. Type your message in the chat box
    3. The bot will respond with text and voice
    4. Adjust voice settings as needed
    5. Clear chat history when needed
    """)