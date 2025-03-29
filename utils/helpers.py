from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv('config/example.env')


def get_openai_key():
    return os.getenv('OPENAI_API_KEY')


def format_review(mistakes):
    if not mistakes:
        return "No mistakes found! Great job!"

    review = "Mistakes Review:\n"
    categories = {}
    for mistake in mistakes:
        cat = mistake[6] or 'General'
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(mistake)

    for cat, items in categories.items():
        review += f"\n=== {cat.upper()} ===\n"
        for idx, item in enumerate(items, 1):
            review += (f"{idx}. Original: {item[3]}\n"
                       f"   Corrected: {item[4]}\n"
                       f"   Explanation: {item[5]}\n")
    return review