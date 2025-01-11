import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import re
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def get_youtube_id(url):
    """
    Extracts the YouTube video ID from a URL.
    """
    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?youtu(?:be\.com|\.be)\/(?:watch\?v=|embed\/|v\/)?([\w-]{11})(?:\S+)?$',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/shorts\/([\w-]{11})(?:\S+)?$'
    ]
    for pattern in patterns:
        match = re.match(pattern, url)
        if match:
            return match.group(1)
    return None

def get_transcript(youtube_id):
    """
    Retrieves and formats the transcript for a YouTube video.
    """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(youtube_id)
        formatter = TextFormatter()
        formatted_transcript = formatter.format_transcript(transcript)
        return formatted_transcript
    except Exception as e:
        return f"An error occurred: {e}"

def chat_with_transcript():
    """
    Provides a chat interface to interact with the YouTube transcript.
    """
    st.subheader("Chat with the YouTube Transcript")

    # Check if transcript is available
    if "transcript_content" not in st.session_state or not st.session_state["transcript_content"]:
        st.info("No transcript to chat with yet. Please enter a YouTube URL and fetch the transcript first.")
        return

    # Initialize conversation
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # Display existing conversation
    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # User input
    user_input = st.chat_input("Enter a question or comment about the transcript:")
    if user_input:
        # Add user message to chat history
        st.session_state["chat_history"].append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)

        # Prepare messages for OpenAI
        system_msg = {
            "role": "system",
            "content": (
                "You are a helpful assistant. Use the following YouTube transcript to answer questions:\n\n"
                f"{st.session_state['transcript_content']}\n\n"
                "Only use the provided transcript if relevant to the question. If it's not relevant, say so."
            )
        }
        messages = [system_msg] + [{"role": msg["role"], "content": msg["content"]} for msg in st.session_state["chat_history"]]

        # Get response from OpenAI
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
                max_tokens=512
            )
            answer = response.choices[0].message.content.strip()
        except Exception as e:
            answer = f"OpenAI API Error: {str(e)}"

        # Add AI response to chat history
        st.session_state["chat_history"].append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.write(answer)

# Streamlit app
st.title("YouTube Transcript and Chat")

youtube_url = st.text_input("Enter YouTube URL:")

if youtube_url:
    youtube_id = get_youtube_id(youtube_url)

    if youtube_id:
        with st.spinner("Retrieving transcript..."):
            transcript = get_transcript(youtube_id)

        if "error occurred" in transcript:
            st.error(transcript)
        else:
            st.subheader("Transcript:")
            st.write(transcript)

            # Store transcript in session state for chat
            st.session_state["transcript_content"] = transcript
    else:
        st.error("Invalid YouTube URL. Please enter a valid URL.")

# Chat interface
st.divider()
chat_with_transcript()