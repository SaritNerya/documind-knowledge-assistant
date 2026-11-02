import { useEffect, useRef, useState } from "react";
import { ask, getMessages, clearMessages } from "./api";

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

    // טעינת ההיסטוריה פעם אחת, כשהרכיב נטען
    useEffect(() => {
        getMessages()
            .then((history) =>
                setMessages(
                    history.map((m) => ({ role: m.role, text: m.content, sources: m.sources }))
                )
            )
            .catch((err) => setError(err.message));
    }, []);

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
    async function handleClear() {
        if (!window.confirm("למחוק את כל השיחה?")) return;
        try {
            await clearMessages();
            setMessages([]);
        } catch (err) {
            setError(err.message);
        }
    }

    return (
        <div className="card">
            <h2>שאלות על המסמכים</h2>

            {messages.length > 0 && (
                <button type="button" onClick={handleClear}>נקי שיחה</button>
            )}

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