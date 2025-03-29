import openai
from utils.database import create_connection, init_db
from utils.helpers import get_openai_key, format_review
from datetime import datetime
import re
from g4f.client import Client

client = Client()
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}],
    web_search=False
)


class LanguageTutorBot:
    def __init__(self):
        init_db()
        self.client = Client()
        self.session_id = datetime.now().strftime("%Y%m%d%H%M%S")
        self.conversation_history = []

    def get_user_preferences(self):
        target_lang = input("What language would you like to learn? ")
        base_lang = input("What is your native language? ")
        level = input("What's your current level (beginner/intermediate/advanced)? ")
        scenario = input("Choose a scenario (restaurant/hotel/shopping/greetings): ")
        return target_lang, base_lang, level, scenario

    def generate_scene(self, scenario, target_lang):
        scenes = {
            'restaurant': f"You're in a {target_lang}-speaking restaurant. Order food and interact with the waiter.",
            'hotel': f"You're checking into a {target_lang}-speaking hotel. Talk to the receptionist.",
            'shopping': f"You're shopping in a {target_lang} store. Negotiate prices and ask about products.",
            'greetings': f"Start a casual conversation with a {target_lang} speaker you just met."
        }
        return scenes.get(scenario.lower(), "General conversation")

    def get_correction(self, target_lang, base_lang, level, scenario, user_input):
        prompt = (f"Act as a {target_lang} language tutor. The student knows {base_lang} and is {level} level. "
                  f"Current scenario: {scenario}. The student wrote: '{user_input}'. "
                  "If there are mistakes, first provide the corrected version, then explain briefly in English. "
                  "Format: [CORRECTED_VERSION]||[EXPLANATION]||[CATEGORY]. "
                  "If no mistakes, respond normally without special formatting.")

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            web_search=False
        )
        return response.choices[0].message.content

    def log_mistake(self, incorrect, corrected, explanation, category):
        conn = create_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''INSERT INTO mistakes 
                                (session_id, incorrect_text, corrected_text, explanation, category)
                                VALUES (?, ?, ?, ?, ?)''',
                               (self.session_id, incorrect, corrected, explanation, category))
                conn.commit()
            except Exception as e:
                print(f"Database error: {e}")
            finally:
                conn.close()

    def start_chat(self):
        target_lang, base_lang, level, scenario = self.get_user_preferences()
        scene_description = self.generate_scene(scenario, target_lang)
        print(f"\nScenario: {scene_description}\nLet's start! (type 'exit' to quit)\n")

        while True:
            user_input = input("You: ")
            if user_input.lower() == 'exit':
                break

            response = self.get_correction(target_lang, base_lang, level, scenario, user_input)

            if '||' in response:
                corrected, explanation, category = response.split('||', 2)
                print(f"Tutor: {corrected.strip()}")
                print(f"Explanation: {explanation.strip()} ({category.strip()})\n")
                self.log_mistake(user_input, corrected.strip(), explanation.strip(), category.strip())
            else:
                print(f"Tutor: {response}")

            self.conversation_history.append((user_input, response))

        self.show_review()

    def show_review(self):
        conn = create_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute('''SELECT * FROM mistakes 
                                WHERE session_id = ?''', (self.session_id,))
                mistakes = cursor.fetchall()
                print("\n" + format_review(mistakes))
            except Exception as e:
                print(f"Error retrieving review: {e}")
            finally:
                conn.close()


if __name__ == "__main__":
    bot = LanguageTutorBot()
    bot.start_chat()