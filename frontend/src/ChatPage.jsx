import { useCallback, useEffect, useRef, useState } from "react";
import { useMatch, useNavigate } from "react-router-dom";
import {
  askInConversation,
  createConversation,
  deleteConversation,
  getConversationMessages,
  listConversations,
  renameConversation,
} from "./api";
import ChatWindow from "./ChatWindow";
import ConversationSidebar from "./ConversationSidebar";
import Documents from "./Documents";
import useConversationDocuments from "./hooks/useConversationDocuments";

const NEW_TITLE = "שיחה חדשה";

export default function ChatPage() {
  const navigate = useNavigate();
  const isIndex = useMatch("/") !== null;
  const match = useMatch("/c/:conversationId");
  // null = מסך שיחה חדשה. NaN = כתובת לא תקינה (למשל /c/abc)
  const activeId = match ? Number(match.params.conversationId) : null;

  const [conversations, setConversations] = useState([]);
  const [listLoading, setListLoading] = useState(true);
  const [listError, setListError] = useState("");
  // ההודעות שמוצגות, יחד עם מזהה השיחה שהן שייכות לה
  const [chat, setChat] = useState({ id: null, messages: [], error: "" });
  const [pendingId, setPendingId] = useState(undefined); // השיחה שממתינה לתשובה. undefined = אין
  const [openPanel, setOpenPanel] = useState(null); // בטלפון: "conversations" | "documents" | null
  const creatingRef = useRef(null);
  const busyRef = useRef(new Set()); // שיחות עם שאלה או העלאה בתהליך: אסור לנקות אותן
  const documents = useConversationDocuments(activeId);
  const previousIdRef = useRef(activeId);

  const sending = pendingId !== undefined;
  // בזמן מעבר מ-/new ל-/c/:id אחרי השליחה הראשונה, ממשיכים להציג את השיחה הממתינה
  const showChat = chat.id === activeId || (sending && chat.id === pendingId);
  const messagesLoading = activeId !== null && !Number.isNaN(activeId) && !showChat;

  const refreshConversations = useCallback(async () => {
    try {
      setConversations(await listConversations());
      setListError("");
    } catch (err) {
      setListError(err.message);
    } finally {
      setListLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshConversations();
  }, [refreshConversations]);

  // "/" מעביר לשיחה האחרונה, או לשיחה חדשה אם אין
  useEffect(() => {
    if (!isIndex || listLoading || listError) return;
    navigate(conversations.length ? `/c/${conversations[0].id}` : "/new", { replace: true });
  }, [isIndex, listLoading, listError, conversations, navigate]);

  // טעינת ההודעות כשעוברים לשיחה שעוד לא מוצגת
  useEffect(() => {
    if (activeId === null || chat.id === activeId) return;
    if (Number.isNaN(activeId)) {
      navigate("/new", { replace: true });
      return;
    }
    let cancelled = false;
    getConversationMessages(activeId)
      .then((messages) => {
        if (!cancelled) setChat({ id: activeId, messages, error: "" });
      })
      .catch((err) => {
        if (cancelled) return;
        if (err.status === 404) {
          // שיחה שלא קיימת או שאינה שלי: מעבר נקי לשיחה חדשה
          navigate("/new", { replace: true });
          refreshConversations();
        } else {
          setChat({ id: activeId, messages: [], error: err.message });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [activeId, chat.id, navigate, refreshConversations]);

  // כמו בצ'אט אמיתי: שיחה שעזבו בלי לכתוב בה כלום לא נשמרת.
  // השרת מוחק רק אם השיחה באמת ריקה (בלי הודעות ובלי מסמכים), כך שאין סכנה לאבד תוכן.
  useEffect(() => {
    const leftId = previousIdRef.current;
    previousIdRef.current = activeId;
    if (leftId === null || leftId === activeId || Number.isNaN(leftId)) return;
    if (busyRef.current.has(leftId)) return;
    deleteConversation(leftId, { onlyIfEmpty: true })
      .then(refreshConversations)
      .catch(() => {}); // ניקוי שקט: אם נכשל, השיחה פשוט נשארת
  }, [activeId, refreshConversations]);

  // מריץ פעולה על שיחה ומסמן אותה כ"עסוקה" עד שהפעולה מסתיימת
  async function whileBusy(conversationId, task) {
    busyRef.current.add(conversationId);
    try {
      return await task();
    } finally {
      busyRef.current.delete(conversationId);
    }
  }

  function goTo(path) {
    setOpenPanel(null);
    navigate(path);
  }

  // שיחה חדשה נוצרת בשרת רק בפעולה הראשונה (הודעה או העלאת מסמך).
  // creatingRef מונע יצירה כפולה אם שתי הפעולות קורות יחד.
  function ensureConversation() {
    if (activeId !== null) return Promise.resolve(activeId);
    if (!creatingRef.current) {
      creatingRef.current = createConversation()
        .then((created) => {
          setConversations((prev) => [created, ...prev]); // מופיעה בסרגל מיד
          navigate(`/c/${created.id}`, { replace: true });
          return created.id;
        })
        .finally(() => {
          creatingRef.current = null;
        });
    }
    return creatingRef.current;
  }

  async function handleSend(question) {
    const startId = activeId;
    const userMessage = { role: "user", content: question };
    setChat((prev) => ({
      id: startId,
      messages: [...(prev.id === startId ? prev.messages : []), userMessage],
      error: "",
    }));
    setPendingId(startId);

    let targetId = startId;
    try {
      if (targetId === null) {
        const createdId = await ensureConversation();
        targetId = createdId;
        setChat((prev) => ({ ...prev, id: createdId }));
        setPendingId(createdId);
      }
      const conversationId = targetId;
      const data = await whileBusy(conversationId, () =>
        askInConversation(conversationId, question, documents.searchScope)
      );
      const answer = { role: "assistant", content: data.answer, sources: data.sources };
      setChat((prev) =>
        prev.id === conversationId ? { ...prev, messages: [...prev.messages, answer] } : prev
      );
      // הכותרת (זמנית או חכמה) מגיעה עם התשובה, אז אין צורך לטעון את הרשימה מחדש
      bumpConversation(conversationId, { title: data.title });
    } catch (err) {
      const conversationId = targetId;
      setChat((prev) => (prev.id === conversationId ? { ...prev, error: err.message } : prev));
      refreshConversations(); // אחרי כישלון לא בטוח מה המצב בשרת, אז טוענים מחדש
    } finally {
      setPendingId(undefined);
    }
  }

  // מעדכן שיחה ברשימה ומעביר אותה לראש, כמו שהשרת ממיין (לפי פעילות אחרונה)
  function bumpConversation(id, changes) {
    setConversations((prev) => {
      const current = prev.find((c) => c.id === id);
      if (!current) return prev;
      return [{ ...current, ...changes }, ...prev.filter((c) => c.id !== id)];
    });
  }

  async function handleRename(id, title) {
    try {
      const updated = await renameConversation(id, title);
      setConversations((prev) => prev.map((c) => (c.id === id ? updated : c)));
      setListError("");
    } catch (err) {
      setListError(err.message);
    }
  }

  async function handleDelete(id) {
    if (!window.confirm("למחוק את השיחה? כל ההודעות בה יימחקו.")) return;
    try {
      await deleteConversation(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      setListError("");
      if (id === activeId) navigate("/", { replace: true });
    } catch (err) {
      setListError(err.message);
    }
  }

  const active = conversations.find((c) => c.id === activeId);
  const title = activeId === null ? NEW_TITLE : active?.title ?? "";

  // הודעה מעל שורת הקלט כשהחיפוש לא רץ על כל המסמכים
  const scope = documents.searchScope;
  const noDocumentSelected = scope !== null && scope.length === 0;
  const scopeNote = noDocumentSelected
    ? "לא נבחר אף מסמך. סמני לפחות מסמך אחד בחלונית המסמכים."
    : scope && `החיפוש יתבצע ב-${scope.length} מתוך ${documents.docs.length} המסמכים`;

  return (
    <div className="workspace">
      {openPanel && <div className="backdrop" onClick={() => setOpenPanel(null)} />}
      <ConversationSidebar
        conversations={conversations}
        activeId={activeId}
        open={openPanel === "conversations"}
        loading={listLoading}
        error={listError}
        disabled={sending}
        onNew={() => goTo("/new")}
        onSelect={(id) => goTo(`/c/${id}`)}
        onRename={handleRename}
        onDelete={handleDelete}
      />
      <main className="main">
        {/* בטלפון בלבד: פתיחת הפאנלים שבצדדים */}
        <div className="panel-toggles">
          <button type="button" className="btn-ghost" onClick={() => setOpenPanel("conversations")}>
            ☰ שיחות
          </button>
          <button type="button" className="btn-ghost" onClick={() => setOpenPanel("documents")}>
            מסמכים ▤
          </button>
        </div>
        <ChatWindow
          title={title}
          messages={showChat ? chat.messages : []}
          loading={messagesLoading}
          thinking={sending && showChat}
          sending={sending}
          error={showChat ? chat.error : ""}
          note={scopeNote}
          blocked={noDocumentSelected}
          onSend={handleSend}
        />
      </main>
      <Documents
        documents={documents}
        conversationId={activeId}
        open={openPanel === "documents"}
        ensureConversation={ensureConversation}
        whileBusy={whileBusy}
        onUploaded={refreshConversations}
        disabled={sending}
      />
    </div>
  );
}
