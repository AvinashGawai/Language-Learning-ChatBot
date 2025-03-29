import streamlit as st
from g4f.client import Client
from utils.database import create_connection, init_db
from utils.helpers import format_review
from datetime import datetime

# Initialize database
init_db()

# Configure page
st.set_page_config(page_title="Language Tutor Bot", page_icon="🗣️")

# Initialize session state
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'session_id' not in st.session_state:
    st.session_state.session_id = datetime.now().strftime("%Y%m%d%H%M%S")
if 'start_chat' not in st.session_state:
    st.session_state.start_chat = False

client = Client()

# Language options
LANGUAGES = [
    "English", "Spanish", "French", "German", "Italian",
    "Chinese", "Japanese", "Korean", "Russian", "Arabic",
    "Portuguese", "Hindi", "Turkish", "Dutch", "Swedish"
]

SCENARIOS = {
    "Restaurant": "Order food and interact with the waiter",
    "Hotel": "Check-in at a hotel",
    "Shopping": "Negotiate prices in a store",
    "Greetings": "Casual conversation",
    "Travel": "Ask for directions",
    "Business": "Professional meeting"
}


def log_mistake(incorrect, corrected, explanation, category):
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO mistakes 
                            (session_id, incorrect_text, corrected_text, explanation, category)
                            VALUES (?, ?, ?, ?, ?)''',
                           (st.session_state.session_id, incorrect, corrected, explanation, category))
            conn.commit()
        except Exception as e:
            st.error(f"Database error: {e}")
        finally:
            conn.close()


def get_correction(target_lang, base_lang, level, scenario, user_input):
    prompt = (f"Act as a {target_lang} language tutor. The student knows {base_lang} and is {level} level. "
              f"Current scenario: {scenario}. The student wrote: '{user_input}'. "
              "If there are mistakes, first provide the corrected version, then explain briefly in English. "
              "Format: [CORRECTED_VERSION]||[EXPLANATION]||[CATEGORY]. "
              "If no mistakes, respond normally without special formatting.")

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            web_search=False
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"AI Service Error: {str(e)}")
        return None


def show_review():
    conn = create_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''SELECT * FROM mistakes 
                            WHERE session_id = ?''', (st.session_state.session_id,))
            mistakes = cursor.fetchall()
            st.subheader("Session Review")
            st.write(format_review(mistakes))
        except Exception as e:
            st.error(f"Error retrieving review: {e}")
        finally:
            conn.close()


# App layout
st.title("🌍 Language Learning Chatbot")

# Sidebar for settings
with st.sidebar:
    st.header("Settings")
    base_lang = st.selectbox("Your Native Language", LANGUAGES, index=0)
    target_lang = st.selectbox("Language to Learn", LANGUAGES, index=1)
    level = st.selectbox("Your Level", ["Beginner", "Intermediate", "Advanced"])
    scenario = st.selectbox("Choose Scenario", list(SCENARIOS.keys()))

    if st.button("Start/Restart Conversation"):
        st.session_state.start_chat = True
        st.session_state.conversation = []
        st.session_state.session_id = datetime.now().strftime("%Y%m%d%H%M%S")
        st.rerun()

# Chat interface
if st.session_state.start_chat:
    st.subheader(SCENARIOS[scenario])
    st.write("Start chatting in the selected language. Type 'exit' to end the session.")

    # Display conversation history
    for message in st.session_state.conversation:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "correction" in message:
                with st.expander("See correction"):
                    st.write(f"**Corrected:** {message['correction']}")
                    st.write(f"**Explanation:** {message['explanation']}")
                    st.write(f"**Category:** {message['category']}")

    # User input
    user_input = st.chat_input("Type your message...")

    if user_input:
        if user_input.lower() == 'exit':
            st.session_state.start_chat = False
            show_review()
            st.rerun()

        # Add user message to history
        st.session_state.conversation.append({"role": "user", "content": user_input})

        # Get AI response
        with st.spinner("Analyzing your message..."):
            response = get_correction(target_lang, base_lang, level, scenario, user_input)

        if response:
            if '||' in response:
                corrected, explanation, category = response.split('||', 2)
                correction_data = {
                    "correction": corrected.strip(),
                    "explanation": explanation.strip(),
                    "category": category.strip()
                }
                log_mistake(user_input, corrected.strip(), explanation.strip(), category.strip())
            else:
                correction_data = {"content": response}

            # Add tutor response to history
            st.session_state.conversation.append({
                "role": "assistant",
                "content": response if '||' not in response else corrected.strip(),
                **correction_data
            })

            st.rerun()

else:
    st.write("Configure your settings in the sidebar and click 'Start Conversation' to begin!")
    st.image("https://cdn.pixabay.com/photo/2018/06/08/00/48/artificial-intelligence-3461455_1280.jpg",
             caption="Language Learning Assistant")

# Footer
st.markdown("---")
st.markdown("Built with Streamlit and GPT-4 • [GitHub Repository](https://github.com/your-repo)")