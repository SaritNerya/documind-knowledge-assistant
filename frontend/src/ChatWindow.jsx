import { useEffect, useRef, useState } from "react";
import MessageBubble from "./MessageBubble";

export default function ChatWindow({ title, messages, loading, thinking, sending, error, onSend }) {
  const [question, setQuestion] = useState("");
  const bottomRef = useRef(null);

  // גלילה אוטומטית להודעה האחרונה
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinking]);

  function handleSubmit(e) {
    e.preventDefault();
    const q = question.trim();
    if (!q || sending) return;
    setQuestion("");
    onSend(q);
  }

  return (
    <div className="card">
      <h2>{title}</h2>

      <div className="chat-box">
        {loading && <p className="hint">טוען את השיחה...</p>}
        {!loading && messages.length === 0 && (
          <p className="hint">שאלי שאלה על המסמכים שהעלית, למשל: "כמה ימי חופשה מגיעים לי?"</p>
        )}
        {messages.map((m, i) => (
          <MessageBubble key={i} role={m.role} content={m.content} sources={m.sources} />
        ))}
        {thinking && <div className="bubble assistant">חושב...</div>}
        <div ref={bottomRef} />
      </div>

      {error && <p className="error">{error}</p>}

      <form className="chat-form" onSubmit={handleSubmit}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="הקלידי שאלה..."
          maxLength={2000}
          disabled={sending || loading}
        />
        <button type="submit" disabled={sending || loading || !question.trim()}>
          שליחה
        </button>
      </form>
    </div>
  );
}
