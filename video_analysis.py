import streamlit as st
import base64
import os
import requests
import tempfile
import cv2

# Constants
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or "your_api_key_here"
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

st.set_page_config(page_title="🏏 AI Cricket Commentary", layout="wide")

# ---------- COMPONENT: Extract Frames ----------
def extract_frames(video_path, frame_count=5):
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    interval = total_frames // frame_count

    frames_base64 = []
    for i in range(frame_count):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i * interval)
        success, frame = cap.read()
        if success:
            _, buffer = cv2.imencode('.jpg', frame)
            base64_frame = base64.b64encode(buffer).decode("utf-8")
            frames_base64.append(base64_frame)
    cap.release()
    return frames_base64

# ---------- COMPONENT: Send to Groq ----------
def generate_commentary(frames):
    images_payload = [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}} for img in frames]

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are Rameez Raja giving energetic, passionate live cricket commentary. "
                    "Describe the cricket action happening in these images as if you're watching a thrilling live match. "
                    "No placeholders or mentions of 'frames' or 'base64'. Just pure, immersive, play-by-play commentary."
                )
            },
            {
                "role": "user",
                "content": images_payload
            }
        ],
        "temperature": 0.9,
        "max_tokens": 800
    }

    response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        st.error(f"Error from Groq API: {response.json()}")
        return None

# ---------- STREAMLIT UI ----------
st.title("🏏 Rameez Raja’s Live Commentary Generator")
st.caption("Upload a short cricket video and get thrilling commentary, AI-style!")

uploaded_video = st.file_uploader("🎥 Upload Your Cricket Clip", type=["mp4", "mov", "avi"])

if uploaded_video:
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
        tmp.write(uploaded_video.read())
        temp_video_path = tmp.name

    st.info("🎞️ Extracting key moments...")

    frames = extract_frames(temp_video_path)

    st.success("✅ Frames extracted successfully!")
    st.image([base64.b64decode(f) for f in frames], width=220, caption=[f"Moment {i+1}" for i in range(len(frames))])

    if st.button("🎙️ Generate Rameez Commentary"):
        with st.spinner("Talking to Rameez Raja..."):
            commentary = generate_commentary(frames)

        if commentary:
            st.markdown("### 🎤 Rameez Raja Says:")
            st.markdown(f"```\n{commentary}\n```")
