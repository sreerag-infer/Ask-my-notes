import { useState } from "react";
import "./App.css";
import Voice from "./Voice";


const API = "http://localhost:8000";

// Converts sources into short text, like "rules.pdf p.2"
function showSources(sources = []) {
  const names = sources.map(
    (s) => `${s.source} p.${s.page}`
  );
  return [...new Set(names)].join(" · ");
}

function App() {
  // App state
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [agentMode, setAgentMode] = useState(false);

  // Adds one message to the chat
  function addMessage(msg) {
    setMessages((old) => [...old, msg]);
  }

  // Handles asking questions
  async function askQuestion() {
    if (!question.trim() || loading) return;

    const myQuestion = question.trim();

    addMessage({ role: "user", text: myQuestion });
    setQuestion("");
    setLoading(true);

    try {
      const res = await fetch(`${API}/${agentMode ? "agent" : "ask"}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: myQuestion,
        }),
      });

      if (!res.ok) {
        throw new Error("Server error");
      }

      const data = await res.json();

      addMessage({ role: "bot", text: data.answer, sources: data.sources, steps: data.steps });
    } catch {
      addMessage({
        role: "bot",
        text: "Oops! Is the backend running?",
      });
    }

    setLoading(false);
  }

  // Handles PDF uploads
  async function uploadPdf(e) {
    const file = e.target.files[0];

    if (!file || loading) return;

    const form = new FormData();
    form.append("file", file);

    setLoading(true);

    try {
      const res = await fetch(`${API}/upload`, {
        method: "POST",
        body: form,
      });

      if (!res.ok) {
        throw new Error("Upload error");
      }

      const data = await res.json();

      addMessage({
        role: "bot",
        text: data.message || "PDF uploaded successfully!",
      });

    } catch {
      addMessage({
        role: "bot",
        text: "Upload failed. Try again.",
      });
    }

    setLoading(false);
    e.target.value = "";
  }

  return (
    <div className="app">

      <h1>📚 Ask My Notes</h1>
      <div className="top">
        <label className="mode">
          <input type="checkbox" checked={agentMode}
            onChange={(e) => setAgentMode(e.target.checked)} />
          🤖 Agent mode
        </label>
        <Voice />
      </div>

      <div className="chat">

        {messages.length === 0 && (
          <p className="hint">
            Ask anything about your notes 👇
          </p>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            <p>{m.text}</p>

            {m.sources && <small>📄 {showSources(m.sources)}</small>}
            {m.steps?.length > 0 && <small>🛠 {m.steps.join(" → ")}</small>}
          </div>
        ))}

        {loading && (
          <div className="msg bot">
            Thinking… 🤔
          </div>
        )}

      </div>

      <div className="ask-box">

        <label className="upload">
          📎 PDF
          <input
            type="file"
            accept=".pdf,application/pdf"
            hidden
            onChange={uploadPdf}
            disabled={loading}
          />
        </label>

        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) =>
            e.key === "Enter" && askQuestion()
          }
          placeholder="Type your question…"
          disabled={loading}
        />

        <button
          onClick={askQuestion}
          disabled={loading || !question.trim()}
        >
          Ask
        </button>

      </div>

    </div>
  );
}

export default App;