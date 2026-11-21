# voice.py - the live voice door: browser <-> our backend <-> Gemini Live
import asyncio
import json
from fastapi import APIRouter, WebSocket
from google.genai import types
from live_config import gemini, MODEL, CONFIG, answer_tool_call

router = APIRouter()
@router.websocket("/voice")
async def voice(ws: WebSocket):
    await ws.accept()
    async with gemini.aio.live.connect(model=MODEL, config=CONFIG) as session:

        async def browser_to_gemini():
            while True:
                pcm = await ws.receive_bytes()           # 16 kHz mic audio
                await session.send_realtime_input(
                    audio=types.Blob(data=pcm, mime_type="audio/pcm;rate=16000"))
        async def gemini_to_browser():
            while True:
                async for response in session.receive():
                    if response.tool_call:
                        await answer_tool_call(session, response.tool_call)
                    content = response.server_content
                    if not content:
                        continue
                    if content.interrupted:
                        await ws.send_text(json.dumps({"type": "interrupted"}))
                    if content.model_turn:
                        for part in content.model_turn.parts:
                            if part.inline_data:                # 24 kHz voice
                                await ws.send_bytes(part.inline_data.data)
                    text = content.output_transcription and content.output_transcription.text
                    if text:
                        await ws.send_text(json.dumps({"type": "caption", "text": text}))
                    if content.turn_complete:
                        await ws.send_text(json.dumps({"type": "done"}))
        # Run both directions at once; stop both when the browser leaves
        tasks = [asyncio.create_task(browser_to_gemini()),
                 asyncio.create_task(gemini_to_browser())]
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
