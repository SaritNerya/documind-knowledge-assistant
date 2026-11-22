import { useCallback, useEffect, useState } from "react";
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
  const [sidebarOpen, setSidebarOpen] = useState(false);

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

  function goTo(path) {
    setSidebarOpen(false);
    navigate(path);
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
      // שיחה חדשה נוצרת בשרת רק עכשיו, בשליחה הראשונה
      if (targetId === null) {
        const created = await createConversation();
        targetId = created.id;
        setChat((prev) => ({ ...prev, id: created.id }));
        setPendingId(created.id);
        navigate(`/c/${created.id}`, { replace: true });
      }
      const conversationId = targetId;
      const data = await askInConversation(conversationId, question);
      const answer = { role: "assistant", content: data.answer, sources: data.sources };
      setChat((prev) =>
        prev.id === conversationId ? { ...prev, messages: [...prev.messages, answer] } : prev
      );
    } catch (err) {
      const conversationId = targetId;
      setChat((prev) => (prev.id === conversationId ? { ...prev, error: err.message } : prev));
    } finally {
      setPendingId(undefined);
      refreshConversations(); // כותרת וסדר מתעדכנים בשרת אחרי שאלה
    }
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

  return (
    <div className="workspace">
      {sidebarOpen && <div className="backdrop" onClick={() => setSidebarOpen(false)} />}
      <ConversationSidebar
        conversations={conversations}
        activeId={activeId}
        open={sidebarOpen}
        loading={listLoading}
        error={listError}
        disabled={sending}
        onNew={() => goTo("/new")}
        onSelect={(id) => goTo(`/c/${id}`)}
        onRename={handleRename}
        onDelete={handleDelete}
      />
      <main className="main">
        <button type="button" className="sidebar-toggle" onClick={() => setSidebarOpen(true)}>
          ☰ שיחות
        </button>
        <Documents />
        <ChatWindow
          title={title}
          messages={showChat ? chat.messages : []}
          loading={messagesLoading}
          thinking={sending && showChat}
          sending={sending}
          error={showChat ? chat.error : ""}
          onSend={handleSend}
        />
      </main>
    </div>
  );
}
