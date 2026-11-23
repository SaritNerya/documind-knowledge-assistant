import { useEffect, useLayoutEffect, useRef, useState } from "react";
import Answer from "./Answer";
import FadeText from "./components/FadeText";
import MessageBubble from "./MessageBubble";

const NEAR_BOTTOM_PX = 120; // הודעה חדשה גוללת אוטומטית רק אם המשתמש כבר קרוב לתחתית

/**
 * note: הודעה קצרה מעל שורת הקלט (למשל באילו מסמכים יתבצע החיפוש).
 * blocked: כשהוא true השליחה חסומה וה-note מוצג כאזהרה.
 */
export default function ChatWindow({
  title, messages, loading, thinking, sending, error, note, blocked = false, onSend,
}) {
  const [question, setQuestion] = useState("");
  const scrollRef = useRef(null);
  const nearBottomRef = useRef(true);

  function handleScroll() {
    const el = scrollRef.current;
    nearBottomRef.current = el.scrollHeight - el.scrollTop - el.clientHeight < NEAR_BOTTOM_PX;
  }

  // שיחה שנטענת מחדש מתחילה תמיד מהסוף
  useEffect(() => {
    if (loading) nearBottomRef.current = true;
  }, [loading]);

  // גוללים רק את אזור ההודעות (לא את העמוד), ורק אם המשתמש לא באמצע קריאה למעלה.
  // החלקות נקבעת ב-CSS (scroll-behavior), שמכבד prefers-reduced-motion.
  useLayoutEffect(() => {
    const el = scrollRef.current;
    if (el && nearBottomRef.current) el.scrollTop = el.scrollHeight;
  }, [messages, thinking]);

  function handleSubmit(e) {
    e.preventDefault();
    const q = question.trim();
    if (!q || sending || blocked) return;
    setQuestion("");
    nearBottomRef.current = true; // מי ששולח שאלה רוצה לראות את התשובה
    onSend(q);
  }

  // Enter שולח, Shift+Enter יורד שורה. בזמן הקלדה במקלדת הרכבה (isComposing) לא שולחים.
  function handleKeyDown(e) {
    if (e.key !== "Enter" || e.shiftKey || e.nativeEvent.isComposing) return;
    e.preventDefault();
    e.currentTarget.form.requestSubmit();
  }

  return (
    <div className="card chat-card">
      <h2>
        <FadeText text={title} />
      </h2>

      <div className="chat-box" ref={scrollRef} onScroll={handleScroll}>
        {loading && <p className="hint">טוען את השיחה...</p>}
        {!loading && messages.length === 0 && (
          <p className="hint">שאלי שאלה על המסמכים שהעלית, למשל: "כמה ימי חופשה מגיעים לי?"</p>
        )}
        {messages.map((m, i) => (
          <MessageBubble key={i} role={m.role} content={m.content} sources={m.sources} />
        ))}
        {thinking && <Answer content="חושב..." thinking />}
      </div>

      {error && <p className="error">{error}</p>}
      {note && <p className={`chat-note${blocked ? " is-warning" : ""}`} aria-live="polite">{note}</p>}

      <form className="chat-form" onSubmit={handleSubmit}>
        <textarea
          rows={1}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="הקלידי שאלה..."
          aria-label="שאלה"
          maxLength={2000}
          disabled={sending || loading}
        />
        <button type="submit" disabled={sending || loading || blocked || !question.trim()}>
          שליחה
        </button>
      </form>
    </div>
  );
}
