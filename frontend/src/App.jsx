import { useState } from "react";
import "./App.css";

const API = "http://localhost:8000";

// Turns the sources into short text, like "rules.pdf p.2"
function showSources(sources) {
  const names = sources.map((s) => `${s.source} p.${s.page}`);
  return [...new Set(names)].join(" · ");
}
function App() {
  // The app's memory
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  // Adds one message to the chat
  function addMessage(msg) {
    setMessages((old) => [...old, msg]);
  }
// Runs when you press Ask
  async function askQuestion() {
    if (!question.trim()) return;
    const myQuestion = question;
    addMessage({ role: "user", text: myQuestion });
    setQuestion("");
    setLoading(true);
try {
      const res = await fetch(`${API}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: myQuestion }),
      });
      if (!res.ok) throw new Error("Server error");
      const data = await res.json();
      addMessage({ role: "bot", text: data.answer, sources: data.sources });
    } catch {
      addMessage({ role: "bot", text: "Oops! Is the backend running?" });
    }
    setLoading(false);
  }
// What you see on the screen
  return (
    <div className="app">
      <h1>📚 Ask My Notes</h1>
      <div className="chat">
        {messages.length === 0 && (
          <p className="hint">Ask anything about your notes 👇</p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            <p>{m.text}</p>
            {m.sources && <small>📄 {showSources(m.sources)}</small>}
          </div>
        ))}
        {loading && <div className="msg bot">Thinking… 🤔</div>}
      </div>
      <div className="ask-box">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && askQuestion()}
          placeholder="Type your question…"
        />
        <button onClick={askQuestion} disabled={loading}>
          Ask
        </button>
      </div>
    </div>
  );
}

export default App;