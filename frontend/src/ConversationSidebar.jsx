import { useRef, useState } from "react";

const TITLE_MAX_LENGTH = 100; // תואם ל-conversation_title_max_length בשרת

function ConversationItem({ conversation, active, disabled, onSelect, onRename, onDelete }) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(conversation.title);
  const cancelled = useRef(false);

  function startEditing() {
    setTitle(conversation.title);
    cancelled.current = false;
    setEditing(true);
  }

  // השמירה קורית רק ביציאה מהשדה, כך ש-Enter ולחיצה בחוץ לא שומרים פעמיים
  function handleBlur() {
    setEditing(false);
    const trimmed = title.trim();
    if (!cancelled.current && trimmed && trimmed !== conversation.title) {
      onRename(conversation.id, trimmed);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Escape") cancelled.current = true;
    if (e.key === "Enter" || e.key === "Escape") e.currentTarget.blur();
  }

  if (editing) {
    return (
      <li className="conversation editing">
        <input
          autoFocus
          value={title}
          maxLength={TITLE_MAX_LENGTH}
          onChange={(e) => setTitle(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={handleBlur}
          aria-label="שם השיחה"
        />
      </li>
    );
  }

  return (
    <li className={`conversation${active ? " active" : ""}`}>
      <button
        type="button"
        className="conversation-title"
        onClick={() => onSelect(conversation.id)}
        disabled={disabled}
        title={conversation.title}
        aria-current={active ? "page" : undefined}
      >
        {conversation.title}
      </button>
      <button type="button" className="icon" onClick={startEditing} disabled={disabled} aria-label="שינוי שם" title="שינוי שם">
        ✎
      </button>
      <button type="button" className="icon" onClick={() => onDelete(conversation.id)} disabled={disabled} aria-label="מחיקה" title="מחיקה">
        🗑
      </button>
    </li>
  );
}

export default function ConversationSidebar({
  conversations, activeId, open, loading, error, disabled, onNew, onSelect, onRename, onDelete,
}) {
  return (
    <aside className={`card side-panel sidebar${open ? " open" : ""}`}>
      <button type="button" className="new-conversation" onClick={onNew} disabled={disabled}>
        + שיחה חדשה
      </button>
      {loading && <p className="hint">טוען שיחות...</p>}
      {error && <p className="error">{error}</p>}
      {!loading && conversations.length === 0 && <p className="hint">עוד אין שיחות.</p>}
      <ul className="conversation-list">
        {conversations.map((c) => (
          <ConversationItem
            key={c.id}
            conversation={c}
            active={c.id === activeId}
            disabled={disabled}
            onSelect={onSelect}
            onRename={onRename}
            onDelete={onDelete}
          />
        ))}
      </ul>
    </aside>
  );
}
