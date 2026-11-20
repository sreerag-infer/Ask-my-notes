# main.py - our backend: the "waiter" between the screen and the AI
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from ingest import collection

load_dotenv()                                  # read the .env file
ai = Groq(api_key=os.getenv("GROQ_API_KEY"))   # the AI brain

app = FastAPI()

# Allow our React page to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Question(BaseModel):
    question: str

@app.get("/")
def home():
    return {"status": "running", "pieces": collection.count()}

@app.post("/ask")
def ask(q: Question):
    # 1. FIND the 4 pieces of your notes that match best
    results = collection.query(query_texts=[q.question], n_results=4)
    pieces = results["documents"][0]
    sources = results["metadatas"][0]

    # 2. ADD the pieces and the question into one message
    notes = "\n\n".join(pieces)
    prompt = f"""Answer the question using ONLY these notes.
If the answer is not in the notes, say "Not found in your notes."

Notes:
{notes}

Question: {q.question}"""

    # 3. ANSWER: send it all to the AI on Groq
    reply = ai.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    answer = reply.choices[0].message.content
    return {"answer": answer, "sources": sources}

