# tools.py - the agent's "hands": small Python functions it can use
import datetime
from ingest import collection

SYSTEM_PROMPT = """You are Study Buddy, a friendly study agent.
Use your tools when they help:
- search_notes for anything about the student's notes
- calculate for any maths
- today for today's date
- add_task to save a to-do for the student
Answer in simple words. Say which file and page you used."""

def search_notes(query: str) -> str:
    """Search the student's PDF notes and return the best matches."""
    results = collection.query(query_texts=[query], n_results=3)
    found = []
    for text, info in zip(results["documents"][0], results["metadatas"][0]):
        found.append(f"[{info['source']} p.{info['page']}] {text}")
    return "\n\n".join(found) or "Nothing found in the notes."

def calculate(expression: str) -> str:
    """Do maths, for example: (72 + 85 + 90) / 3"""
    if "**" in expression or not all(c in "0123456789+-*/(). " for c in expression):
        return "I can only use numbers, + - * / and brackets."
    try:
        return str(round(eval(expression), 4))
    except Exception:
        return "That maths has a mistake in it."

def today() -> str:
    """Get today's date and the day of the week."""
    return datetime.date.today().strftime("%A, %d %B %Y")


def add_task(task: str, due: str) -> str:
    """Save a study task with its due date to the to-do list."""
    with open("tasks.txt", "a", encoding="utf-8") as f:
        f.write(f"- {task} (due: {due})\n")
    return f"Saved: {task} (due: {due})"

