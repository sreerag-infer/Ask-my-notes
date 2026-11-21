import { useRef, useState } from "react";

const VOICE_URL = "ws://localhost:8000/voice";

// Turns microphone numbers (-1 to 1) into 16-bit sound bytes for Gemini
function toPCM16(samples) {
  const pcm = new Int16Array(samples.length);
  for (let i = 0; i < samples.length; i++) {
    pcm[i] = Math.max(-1, Math.min(1, samples[i])) * 0x7fff;
  }
  return pcm.buffer;
}
function Voice() {
  const [on, setOn] = useState(false);
  const [caption, setCaption] = useState("");
  const live = useRef({});              // remembers the open connections
  // 1. Microphone -> backend, 0.1 seconds at a time
  async function startMic(ws) {
    const micCtx = new AudioContext({ sampleRate: 16000 });
    await micCtx.audioWorklet.addModule("/mic-processor.js");
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const worklet = new AudioWorkletNode(micCtx, "mic-processor");
    micCtx.createMediaStreamSource(stream).connect(worklet);
    let saved = [];
    worklet.port.onmessage = (e) => {
      saved.push(...e.data);
      if (saved.length >= 1600 && ws.readyState === WebSocket.OPEN) {
        ws.send(toPCM16(saved));
        saved = [];
      }
    };
    return { micCtx, stream };
  }
  // 2. Backend -> speakers: play each piece right after the last one
  function startSpeaker(ws) {
    const speakerCtx = new AudioContext({ sampleRate: 24000 });
    let playAt = 0;
    let playing = [];
    let newTurn = true;
    ws.onmessage = (e) => {
      if (typeof e.data === "string") {
        const msg = JSON.parse(e.data);
        if (msg.type === "caption") {
          setCaption((old) => (newTurn ? msg.text : old + msg.text));
          newTurn = false;
        }
        if (msg.type === "done") newTurn = true;
        if (msg.type === "interrupted") {
          playing.forEach((s) => s.stop());
          playing = [];
          playAt = 0;
          newTurn = true;
        }
        return;
      }
      const pcm = new Int16Array(e.data);
      const sound = speakerCtx.createBuffer(1, pcm.length, 24000);
      const channel = sound.getChannelData(0);
      for (let i = 0; i < pcm.length; i++) channel[i] = pcm[i] / 0x8000;
      const source = speakerCtx.createBufferSource();
      source.buffer = sound;
      source.connect(speakerCtx.destination);
      playAt = Math.max(playAt, speakerCtx.currentTime);
      source.start(playAt);
      playAt += sound.duration;
      playing.push(source);
      source.onended = () => (playing = playing.filter((s) => s !== source));
    };
    return speakerCtx;
  }
  // 3. The button: start or stop everything
  async function start() {
    const ws = new WebSocket(VOICE_URL);
    ws.binaryType = "arraybuffer";
    const speakerCtx = startSpeaker(ws);
    live.current = { ws, speakerCtx };
    try {
      const { micCtx, stream } = await startMic(ws);
      live.current = { ws, speakerCtx, micCtx, stream };
    } catch (err) {
      alert("Microphone problem: " + err.message);
      return stop();
    }
    ws.onclose = () => stop();
    if (ws.readyState > WebSocket.OPEN) return stop();
    setOn(true);
  }

  function stop() {
    const { ws, micCtx, speakerCtx, stream } = live.current;
    live.current = {};
    ws?.close();
    stream?.getTracks().forEach((t) => t.stop());
    if (micCtx && micCtx.state !== "closed") micCtx.close();
    if (speakerCtx && speakerCtx.state !== "closed") speakerCtx.close();
    setOn(false);
    setCaption("");
  }
  return (
    <div className="voice">
      <button className={on ? "talk on" : "talk"} onClick={on ? stop : start}>
        {on ? "⏹ Stop" : "🎙 Talk to Study Buddy"}
      </button>
      {on && <p className="caption">{caption || "Listening… say hello!"}</p>}
    </div>
  );
}

export default Voice;
