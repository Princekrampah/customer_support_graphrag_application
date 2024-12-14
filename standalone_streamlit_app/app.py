import streamlit as st
import time
from qa_chatbot import PaysokoQA
from qa_logger import QALogger
import pandas as pd


class PaysokoStreamlitApp:
    def __init__(self):
        self.qa = PaysokoQA()
        self.logger = QALogger()

    def initialize_session_state(self):
        if 'messages' not in st.session_state:
            st.session_state['messages'] = []
        if 'user_input' not in st.session_state:
            st.session_state['user_input'] = ''
        if 'tone' not in st.session_state:
            st.session_state['tone'] = "Professional and formal"
        if 'loading' not in st.session_state:
            st.session_state['loading'] = False

    def handle_send(self):
        user_input = st.session_state.user_input.strip()
        if user_input:  # Verify input is not empty
            # Set loading state to True
            st.session_state.loading = True

            try:
                # Show a spinner while processing
                with st.spinner('Generating response...'):
                    response = self.qa.ask(user_input, st.session_state.tone)

                # Log the interaction
                self.logger.log_qa(user_input, response)

                # Add messages to session state
                st.session_state.messages.append(
                    {"role": "user", "content": user_input})
                st.session_state.messages.append(
                    {"role": "assistant", "content": response})

                # Clear the input after sending
                st.session_state.user_input = ''

            except Exception as e:
                st.error(f"An error occurred: {e}")

            finally:
                # Ensure loading state is set to False
                st.session_state.loading = False

    def display_chat(self):
        st.title("Paysoko Customer Service Assistant")

        # Display existing messages first
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.write(f"👤 You: {message['content']}")
            else:
                with st.chat_message("assistant", avatar="./images/paysoko_chatbot.png"):
                    st.markdown(message["content"])

        # Optional: Display loading indicator if in loading state
        if st.session_state.get('loading', False):
            with st.spinner('Generating response...'):
                time.sleep(1)  # Ensure spinner is visible

        # Chat input area at the bottom
        st.write("")  # Add some spacing
        st.write("")  # Additional spacing

        # Input and send button
        col1, col2 = st.columns([3, 1])

        with col1:
            # Text input with session state
            st.text_input(
                "Ask a question",
                key="user_input",
                on_change=self.handle_send,
                disabled=st.session_state.get('loading', False)
            )

        with col2:
            # Tone selector with session state
            st.selectbox(
                "Select tone",
                [
                    "Professional and formal",
                    "Friendly and helpful",
                    "Brief and direct",
                    "Detailed and explanatory"
                ],
                key="tone",
                disabled=st.session_state.get('loading', False)
            )

    def display_logs(self):
        st.title("Chat Logs")

        try:
            df = pd.read_csv("qa_logs.csv")
            st.dataframe(df, use_container_width=True, hide_index=True)
        except FileNotFoundError:
            st.warning("No logs found. Start chatting to generate logs.")

    def run(self):
        self.initialize_session_state()

        # Page tabs
        tab1, tab2 = st.tabs(["Chat", "Logs"])

        with tab1:
            self.display_chat()

        with tab2:
            self.display_logs()


# Page config
st.set_page_config(
    page_title="Paysoko Customer Service",
    page_icon="./images/paysoko_chatbot.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    #MainMenu {visibility: hidden;}
    .stDeployButton {display:none;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        max-width: none;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #f0f2f6;
    }
    .assistant-message {
        background-color: #e8eaf6;
    }
    .stTextInput > div > div > input {
        background-color: #333;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    app = PaysokoStreamlitApp()
    app.run()
