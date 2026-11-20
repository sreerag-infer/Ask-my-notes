# ingest.py - reads your PDFs, cuts them into small pieces
# and saves the pieces in the "notes box" (ChromaDB)
import os
import chromadb
from pypdf import PdfReader

# The notes box, saved in a folder called notes_db
client = chromadb.PersistentClient(path="notes_db")
collection = client.get_or_create_collection("my_notes")

def cut_into_pieces(text, size=800, overlap=100):
    pieces = []
    start = 0
    while start < len(text):
        pieces.append(text[start:start + size])
        start = start + size - overlap
    return pieces

def add_pdf(path):
    name = os.path.basename(path)
    reader = PdfReader(path)
    count = 0
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        for i, piece in enumerate(cut_into_pieces(text)):
            if piece.strip():
                collection.upsert(
                    ids=[f"{name}-page{page_number}-{i}"],
                    documents=[piece],
                    metadatas=[{"source": name, "page": page_number}],
                )
                count = count + 1
    print(f"Added {name}: {count} pieces")
    return count

# This part runs only when you type: python ingest.py
if __name__ == "__main__":
    for file in os.listdir("docs"):
        if file.lower().endswith(".pdf"):
            add_pdf(os.path.join("docs", file))
    print("Total pieces in the notes box:", collection.count())
