import { useEffect, useRef, useState } from "react";
import { ask } from "./api";

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef(null);

  // גלילה אוטומטית להודעה האחרונה
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSubmit(e) {
    e.preventDefault();
    const q = question.trim();
    if (!q || loading) return;

    setError("");
    setQuestion("");
    setMessages((prev) => [...prev, { role: "user", text: q }]);
    setLoading(true);

    try {
      const data = await ask(q);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: data.answer, sources: data.sources },
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <h2>שאלות על המסמכים</h2>

      <div className="chat-box">
        {messages.length === 0 && (
          <p className="hint">שאלי שאלה על המסמכים שהעלית, למשל: "כמה ימי חופשה מגיעים לי?"</p>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`bubble ${m.role}`}>
            <div>{m.text}</div>
            {m.sources?.length > 0 && (
              <div className="sources">
                מקורות:
                {m.sources.map((s, j) => (
                  <span className="source-tag" key={j}>
                    {s.filename}, עמוד {s.page}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}

        {loading && <div className="bubble assistant">חושב...</div>}
        <div ref={bottomRef} />
      </div>

      {error && <p className="error">{error}</p>}

      <form className="chat-form" onSubmit={handleSubmit}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="הקלידי שאלה..."
          maxLength={2000}
          disabled={loading}
        />
        <button type="submit" disabled={loading || !question.trim()}>
          שליחה
        </button>
      </form>
    </div>
  );
}