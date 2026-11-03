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
    window.location.reload(); // ה-token פג, חוזרים למסך ההתחברות
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const message = typeof err.detail === "string" ? err.detail : "הנתונים שהוזנו אינם תקינים";
    throw new Error(message);
  }
  return res.status === 204 ? null : res.json();
}

export async function register(email, password) {
  return request("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
}

export async function login(email, password) {
  // ה-endpoint של login מצפה לנתוני טופס, לא JSON
  const data = await request("/auth/login", {
    method: "POST",
    body: new URLSearchParams({ username: email, password }),
  });
  setToken(data.access_token);
}

export const listDocuments = () => request("/documents");

export function uploadDocument(file) {
  const form = new FormData();
  form.append("file", file);
  return request("/documents", { method: "POST", body: form });
}

export const deleteDocument = (id) => request(`/documents/${id}`, { method: "DELETE" });

export function ask(question) {
  return request("/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
}

export const getMessages = () => request("/messages");
export const clearMessages = () => request("/messages", { method: "DELETE" });