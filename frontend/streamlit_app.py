import streamlit as st
import requests

# FastAPI Endpoint URL
API_URL = "http://0.0.0.0:8000/api/cooking"

st.title("Cooking Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What can I help you with today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)

    # Add a spinner while waiting for the response
    with st.spinner("Thinking..."):
        try:
            response = requests.post(API_URL, json={"query": prompt})
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            bot_response = response.json()["response"]
            st.session_state.messages.append({"role": "assistant", "content": bot_response})
            st.chat_message("assistant").markdown(bot_response)
        except requests.exceptions.RequestException as e:
            st.error(f"An error occurred: {e}")
        except KeyError:
            st.error("Invalid response from the API.")
