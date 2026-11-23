import { useEffect, useRef, useState } from "react";
import { uploadDocument, deleteDocument } from "./api";
import FileDropZone from "./components/FileDropZone";

const ACCEPTED_FILES = ".pdf,.docx"; // תואם ל-ALLOWED_EXTENSIONS בשרת

function UploadIcon() {
  return (
    <svg className="dropzone-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path d="M12 16V4m0 0-5 5m5-5 5 5M5 20h14" />
    </svg>
  );
}

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

  // מקבלת קובץ מ-FileDropZone (נגרר או נבחר), כבר אחרי בדיקת הסיומת
  async function handleUpload(file) {
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
      <FileDropZone
        accept={ACCEPTED_FILES}
        disabled={uploading || disabled}
        onFile={handleUpload}
        onReject={(message) => documents.showError(conversationId, message)}
      >
        {uploading ? (
          <span>מעלה ומעבד את המסמך, זה עשוי לקחת כמה שניות...</span>
        ) : (
          <>
            <UploadIcon />
            <span className="dropzone-title">גררי קובץ לכאן</span>
            <span className="hint">או לחצי לבחירה · PDF או Word</span>
          </>
        )}
      </FileDropZone>
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
