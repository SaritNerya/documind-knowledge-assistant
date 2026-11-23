import { useCallback, useEffect, useState } from "react";
import { listDocuments } from "../api";

const NONE = { docs: [], error: "" };

/**
 * המסמכים של שיחה, ואילו מהם משתתפים בחיפוש.
 *
 * הבחירה נשמרת כרשימת המסמכים שהמשתמש *הוציא*, ולא כרשימת הנבחרים.
 * כך מסמך חדש שמעלים משתתף אוטומטית, בלי לסנכרן דבר.
 * כל מצב נשמר יחד עם מזהה השיחה שלו, כדי לא להציג נתונים של שיחה אחרת.
 */
export default function useConversationDocuments(conversationId) {
  const [list, setList] = useState({ id: null, ...NONE });
  const [excluded, setExcluded] = useState({ id: null, ids: [] });

  useEffect(() => {
    if (conversationId === null || Number.isNaN(conversationId)) return;
    let cancelled = false;
    listDocuments(conversationId)
      .then((docs) => !cancelled && setList({ id: conversationId, docs, error: "" }))
      .catch((err) => !cancelled && err.status !== 404 &&
        setList({ id: conversationId, docs: [], error: err.message }));
    return () => {
      cancelled = true;
    };
  }, [conversationId]);

  const { docs, error } = list.id === conversationId ? list : NONE;
  const excludedIds = excluded.id === conversationId ? excluded.ids : [];
  const isSelected = (docId) => !excludedIds.includes(docId);
  const selectedIds = docs.filter((d) => isSelected(d.id)).map((d) => d.id);

  function toggle(docId) {
    setExcluded((prev) => {
      const ids = prev.id === conversationId ? prev.ids : [];
      return {
        id: conversationId,
        ids: ids.includes(docId) ? ids.filter((id) => id !== docId) : [...ids, docId],
      };
    });
  }

  const reload = useCallback(async (id) => {
    setList({ id, docs: await listDocuments(id), error: "" });
  }, []);

  function showError(id, message) {
    setList((prev) => ({ id, docs: prev.id === id ? prev.docs : [], error: message }));
  }

  return {
    docs,
    error,
    isSelected,
    selectedCount: selectedIds.length,
    toggle,
    // true: כל המסמכים בחיפוש. false: אף מסמך
    setAll: (selected) =>
      setExcluded({ id: conversationId, ids: selected ? [] : docs.map((d) => d.id) }),
    // מה נשלח לשרת עם השאלה: null = כל המסמכים בשיחה, אחרת רק הנבחרים
    searchScope: selectedIds.length === docs.length ? null : selectedIds,
    reload,
    showError,
  };
}
