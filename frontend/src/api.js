const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export const getToken = () => localStorage.getItem("token");
export const setToken = (t) => localStorage.setItem("token", t);
export const clearToken = () => localStorage.removeItem("token");

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (res.status === 401 && token) {
    clearToken();
    window.location.href = "/login"; // ה-token פג, חוזרים למסך ההתחברות
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const message = typeof err.detail === "string" ? err.detail : "הנתונים שהוזנו אינם תקינים";
    const error = new Error(message);
    error.status = res.status; // מאפשר לרכיבים להבחין למשל ב-404
    throw error;
  }
  return res.status === 204 ? null : res.json();
}

function jsonBody(method, body) {
  return { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
}

export function register(email, password, inviteCode) {
  return request("/auth/register", jsonBody("POST", { email, password, invite_code: inviteCode }));
}

export async function login(email, password) {
  // ה-endpoint של login מצפה לנתוני טופס, לא JSON
  const data = await request("/auth/login", {
    method: "POST",
    body: new URLSearchParams({ username: email, password }),
  });
  setToken(data.access_token);
}

export const listDocuments = (conversationId) =>
  request(`/conversations/${conversationId}/documents`);

export function uploadDocument(conversationId, file) {
  const form = new FormData();
  form.append("file", file);
  return request(`/conversations/${conversationId}/documents`, { method: "POST", body: form });
}

export const deleteDocument = (id) => request(`/documents/${id}`, { method: "DELETE" });

export const listConversations = () => request("/conversations");
export const createConversation = () => request("/conversations", { method: "POST" });
export const renameConversation = (id, title) =>
  request(`/conversations/${id}`, jsonBody("PATCH", { title }));
export const deleteConversation = (id) => request(`/conversations/${id}`, { method: "DELETE" });
export const getConversationMessages = (id) => request(`/conversations/${id}/messages`);
export const askInConversation = (id, question) =>
  request(`/conversations/${id}/ask`, jsonBody("POST", { question }));

