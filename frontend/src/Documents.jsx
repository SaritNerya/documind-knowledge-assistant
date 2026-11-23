import { useEffect, useRef, useState } from "react";
import { uploadDocument, deleteDocument } from "./api";

/**
 * תיבת "כל המסמכים": מסומנת כשכולם נבחרו, ריקה כשאף אחד, ובמצב ביניים (קו) כשרק חלקם.
 * לחיצה כשהכול מסומן מבטלת את כולם. בכל מצב אחר היא בוחרת את כולם.
 */
function SelectAllCheckbox({ selectedCount, total, onChange }) {
  const ref = useRef(null);
  const all = selectedCount === total;
  const some = selectedCount > 0 && !all;

  // indeterminate לא קיים כ-attribute ב-HTML, אפשר לקבוע אותו רק דרך ה-DOM
  useEffect(() => {
    ref.current.indeterminate = some;
  }, [some]);

  return <input ref={ref} type="checkbox" checked={all} onChange={() => onChange(!all)} />;
}

/**
 * חלונית המסמכים של השיחה: העלאה, מחיקה, ובחירה אילו מסמכים משתתפים בחיפוש.
 * המסמכים והבחירה מגיעים מ-useConversationDocuments (דרך ChatPage), כדי שגם השליחה תכיר אותם.
 * conversationId=null הוא מסך שיחה חדשה (עוד אין מסמכים).
 */
export default function Documents({
  documents, conversationId, open, ensureConversation, whileBusy, onUploaded, disabled,
}) {
  const [uploading, setUploading] = useState(false);
  const { docs, error, isSelected, selectedCount, toggle, setAll } = documents;

  async function handleUpload(e) {
    const input = e.target;
    const file = input.files[0];
    if (!file) return;
    setUploading(true);
    let id = conversationId;
    try {
      id = await ensureConversation(); // בשיחה חדשה: ההעלאה יוצרת את השיחה
      await whileBusy(id, () => uploadDocument(id, file)); // השיחה לא תנוקה באמצע ההעלאה
      await documents.reload(id);
      onUploaded();
    } catch (err) {
      documents.showError(id, err.message);
    } finally {
      setUploading(false);
      input.value = ""; // מאפשר להעלות שוב את אותו קובץ
    }
  }

  async function handleDelete(docId) {
    if (!window.confirm("למחוק את המסמך?")) return;
    try {
      await deleteDocument(docId);
      await documents.reload(conversationId);
    } catch (err) {
      documents.showError(conversationId, err.message);
    }
  }

  return (
    <aside className={`card side-panel docs-panel${open ? " open" : ""}`}>
      <h2>המסמכים בשיחה</h2>
      <input type="file" accept=".pdf,.docx" onChange={handleUpload} disabled={uploading || disabled} />
      {uploading && <p>מעלה ומעבד את המסמך, זה עשוי לקחת כמה שניות...</p>}
      {error && <p className="error">{error}</p>}
      {docs.length === 0 && !uploading && <p className="hint">עוד לא הועלו מסמכים לשיחה הזו.</p>}

      {docs.length > 0 && (
        <>
          <label className="docs-summary chip-select">
            <SelectAllCheckbox selectedCount={selectedCount} total={docs.length} onChange={setAll} />
            <span className="docs-summary-text">
              <span>כל המסמכים</span>
              <span className="hint">{selectedCount} מתוך {docs.length} בחיפוש</span>
            </span>
          </label>
          <ul className="chip-list" aria-label="מסמכים. מסמך מסומן משתתף בחיפוש">
            {docs.map((d) => {
              const selected = isSelected(d.id);
              return (
                <li className={`chip doc-chip${selected ? " is-active" : " is-off"}`} key={d.id}>
                  <label className="chip-select">
                    <input type="checkbox" checked={selected} onChange={() => toggle(d.id)} />
                    <span className="bidi">{d.filename}</span>
                  </label>
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
              );
            })}
          </ul>
        </>
      )}
    </aside>
  );
}
