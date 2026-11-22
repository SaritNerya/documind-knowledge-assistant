import { useEffect, useState } from "react";
import { listDocuments, uploadDocument, deleteDocument } from "./api";

// המסמכים של השיחה הפעילה בלבד. conversationId=null הוא מסך שיחה חדשה (עוד אין מסמכים).
export default function Documents({ conversationId, open, ensureConversation, onUploaded, disabled }) {
  // המסמכים והשגיאה נשמרים יחד עם מזהה השיחה שלהם, כדי לא להציג נתונים של שיחה אחרת
  const [state, setState] = useState({ id: null, docs: [], error: "" });
  const [uploading, setUploading] = useState(false);
  const current = state.id === conversationId ? state : { docs: [], error: "" };

  useEffect(() => {
    if (conversationId === null || Number.isNaN(conversationId)) return;
    let cancelled = false;
    listDocuments(conversationId)
      .then((docs) => !cancelled && setState({ id: conversationId, docs, error: "" }))
      .catch((err) => !cancelled && err.status !== 404 &&
        setState({ id: conversationId, docs: [], error: err.message }));
    return () => {
      cancelled = true;
    };
  }, [conversationId]);

  async function reload(id, error = "") {
    setState({ id, docs: await listDocuments(id), error });
  }

  async function handleUpload(e) {
    const input = e.target;
    const file = input.files[0];
    if (!file) return;
    setUploading(true);
    let id = conversationId;
    try {
      id = await ensureConversation(); // בשיחה חדשה: ההעלאה יוצרת את השיחה
      await uploadDocument(id, file);
      await reload(id);
      onUploaded();
    } catch (err) {
      setState((prev) => ({ id, docs: prev.id === id ? prev.docs : [], error: err.message }));
    } finally {
      setUploading(false);
      input.value = ""; // מאפשר להעלות שוב את אותו קובץ
    }
  }

  async function handleDelete(docId) {
    if (!window.confirm("למחוק את המסמך?")) return;
    try {
      await deleteDocument(docId);
      await reload(conversationId);
    } catch (err) {
      setState((prev) => ({ ...prev, error: err.message }));
    }
  }

  return (
    <aside className={`card side-panel docs-panel${open ? " open" : ""}`}>
      <h2>המסמכים בשיחה</h2>
      <input type="file" accept=".pdf,.docx" onChange={handleUpload} disabled={uploading || disabled} />
      {uploading && <p>מעלה ומעבד את המסמך, זה עשוי לקחת כמה שניות...</p>}
      {current.error && <p className="error">{current.error}</p>}
      {current.docs.length === 0 && !uploading && <p className="hint">עוד לא הועלו מסמכים לשיחה הזו.</p>}
      {current.docs.length > 0 && (
        <ul className="chip-list" aria-label="מסמכים">
          {current.docs.map((d) => (
            <li className="chip" key={d.id}>
              <span className="bidi">{d.filename}</span>
              <button
                type="button"
                className="chip-remove"
                onClick={() => handleDelete(d.id)}
                disabled={disabled}
                aria-label={`מחיקת ${d.filename}`}
                title="מחיקה"
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
}
