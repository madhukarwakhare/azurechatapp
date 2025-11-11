# app.py
import os
from dotenv import load_dotenv
import streamlit as st
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient


st.set_page_config(page_title="Azure Chat App", page_icon="💬", layout="centered")
load_dotenv()  # loads .env if available

PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
MODEL_DEPLOYMENT = os.getenv("MODEL_DEPLOYMENT")

# -----------------------------
# Session state
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a helpful AI assistant that answers questions."}
    ]
if "client_ready" not in st.session_state:
    st.session_state.client_ready = False
if "openai_client" not in st.session_state:
    st.session_state.openai_client = None

# -----------------------------
# Init client (no user inputs)
# -----------------------------
def init_client():
    if not PROJECT_ENDPOINT or not MODEL_DEPLOYMENT:
        # We don’t prompt users for any config; just show a single error if misconfigured.
        st.error(
            "Server configuration missing. Please set PROJECT_ENDPOINT and MODEL_DEPLOYMENT as environment variables."
        )
        return False
    try:
        credential = DefaultAzureCredential(
            exclude_environment_credential=True,
            exclude_managed_identity_credential=True,
        )
        project_client = AIProjectClient(credential=credential, endpoint=PROJECT_ENDPOINT)
        st.session_state.openai_client = project_client.get_openai_client(api_version="2024-10-21")
        return True
    except Exception as ex:
        st.error(f"Initialization error: {ex}")
        return False

if not st.session_state.client_ready:
    st.session_state.client_ready = init_client()

# -----------------------------
# UI
# -----------------------------
st.title("💬 ChatGPT-1")
st.caption("Type a prompt below to chat")

# Render chat (hide system message)
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
user_input = st.chat_input("Type your message…")

if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    if not st.session_state.client_ready:
        with st.chat_message("assistant"):
            st.error("Chat client not ready. Check server configuration.")
    else:
        try:
            # Call completion
            resp = st.session_state.openai_client.chat.completions.create(
                model=MODEL_DEPLOYMENT,
                messages=st.session_state.messages,
            )
            completion = resp.choices[0].message.content

            # Show assistant reply
            with st.chat_message("assistant"):
                st.markdown(completion)

            # Save to history
            st.session_state.messages.append({"role": "assistant", "content": completion})
        except Exception as ex:
            with st.chat_message("assistant"):
                st.error(f"Request failed: {ex}")
