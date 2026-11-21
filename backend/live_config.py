# live_config.py - settings shared by both voice agents
import os
import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import types
from tools import search_notes

load_dotenv()
gemini = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=types.HttpOptions(api_version="v1beta")
)
MODEL = "gemini-3.8-live"

search_notes_tool = {
    "name": "search_notes",
    "description": "Search the student's PDF notes for a topic.",
    "parameters": {"type": "OBJECT",
                   "properties": {"query": {"type": "STRING"}},
                   "required": ["query"]},
}

CONFIG = {
    "response_modalities": ["AUDIO"],              # Gemini talks back
    "system_instruction": "You are Study Buddy, a friendly voice tutor. "
        "Keep answers short, like a real conversation. Use search_notes "
        "for anything about the student's notes and say which file you used.",
    "tools": [{"function_declarations": [search_notes_tool]}],
    "input_audio_transcription": {},               # text of what you said
    "output_audio_transcription": {},              # text of what it said
}

async def answer_tool_call(session, tool_call):
    replies = []
    for fc in tool_call.function_calls:
        print(f"  🛠  {fc.name}({fc.args})")
        if fc.name == "search_notes":
            result = await asyncio.to_thread(search_notes, **(fc.args or {}))
        else:
            result = "Unknown tool"
        replies.append(types.FunctionResponse(id=fc.id, name=fc.name,
                                              response={"result": result}))
    await session.send_tool_response(function_responses=replies)

