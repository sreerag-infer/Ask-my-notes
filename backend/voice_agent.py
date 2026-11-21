# voice_agent.py - talk to your notes! Run it in a terminal, use headphones
import asyncio
import pyaudio
from google.genai import types
from live_config import gemini, MODEL, CONFIG, answer_tool_call

FORMAT, CHANNELS, CHUNK = pyaudio.paInt16, 1, 1024
MIC_RATE, SPEAKER_RATE = 16000, 24000        # Gemini hears 16 kHz, speaks 24 kHz
pya = pyaudio.PyAudio()
speaker_queue = asyncio.Queue()

async def listen(session):
    # Microphone -> Gemini, a small piece at a time
    mic = await asyncio.to_thread(pya.open, format=FORMAT, channels=CHANNELS,
                                  rate=MIC_RATE, input=True, frames_per_buffer=CHUNK)
    while True:
        data = await asyncio.to_thread(mic.read, CHUNK, exception_on_overflow=False)
        await session.send_realtime_input(
            audio=types.Blob(data=data, mime_type="audio/pcm;rate=16000"))

async def receive(session):
    # Gemini -> speaker queue (plus tool calls and live captions)
    while True:
        async for response in session.receive():
            if response.tool_call:
                await answer_tool_call(session, response.tool_call)
            content = response.server_content
            if not content:
                continue
            if content.interrupted:              # you spoke: stop talking
                while not speaker_queue.empty():
                    speaker_queue.get_nowait()
            if content.model_turn:
                for part in content.model_turn.parts:
                    if part.inline_data:
                        speaker_queue.put_nowait(part.inline_data.data)
            if content.output_transcription and content.output_transcription.text:
                print(content.output_transcription.text, end="", flush=True)
            if content.turn_complete:
                print()
async def speak():
    # Speaker queue -> your speakers or headphones
    speaker = await asyncio.to_thread(pya.open, format=FORMAT, channels=CHANNELS,
                                      rate=SPEAKER_RATE, output=True)
    while True:
        data = await speaker_queue.get()
        await asyncio.to_thread(speaker.write, data)
async def main():
    async with gemini.aio.live.connect(model=MODEL, config=CONFIG) as session:
        print("🎙  Connected! Start talking. Press Ctrl+C to stop.")
        async with asyncio.TaskGroup() as tg:     # run all three at once
            tg.create_task(listen(session))
            tg.create_task(receive(session))
            tg.create_task(speak())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBye!")
    finally:
        pya.terminate()
