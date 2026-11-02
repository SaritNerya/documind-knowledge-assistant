import { useEffect, useState } from "react";
import { listDocuments, uploadDocument, deleteDocument } from "./api";

export default function Documents() {
  const [docs, setDocs] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  async function refresh() {
    try {
      setDocs(await listDocuments());
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    setError("");
    setUploading(true);
    try {
      await uploadDocument(file);
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
      e.target.value = ""; // מאפשר להעלות שוב את אותו קובץ
    }
  }

  async function handleDelete(id) {
    if (!window.confirm("למחוק את המסמך?")) return;
    try {
      await deleteDocument(id);
      await refresh();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="card">
      <h2>המסמכים שלי</h2>
      <input type="file" accept=".pdf,.docx" onChange={handleUpload} disabled={uploading} />
      {uploading && <p>מעלה ומעבד את המסמך, זה עשוי לקחת כמה שניות...</p>}
      {error && <p className="error">{error}</p>}
      {docs.length === 0 && !uploading && <p>עוד לא הועלו מסמכים.</p>}
      {docs.map((d) => (
        <div className="row" key={d.id}>
          <span>{d.filename}</span>
          <button onClick={() => handleDelete(d.id)}>מחיקה</button>
        </div>
      ))}
    </div>
  );
}