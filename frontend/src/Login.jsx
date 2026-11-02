import { useState } from "react";
import { login, register } from "./api";

export default function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isRegister, setIsRegister] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (isRegister) await register(email, password);
      await login(email, password);
      onLogin();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card login-box" dir="rtl">
      <h2>DocuMind</h2>
      <form onSubmit={handleSubmit}>
        <input type="email" placeholder="אימייל" value={email}
          onChange={(e) => setEmail(e.target.value)} required />
        <input type="password" placeholder="סיסמה (לפחות 8 תווים)" value={password}
          onChange={(e) => setPassword(e.target.value)} required />
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={loading}>
          {isRegister ? "הרשמה" : "התחברות"}
        </button>
      </form>
      <button type="button" onClick={() => setIsRegister(!isRegister)}>
        {isRegister ? "יש לי כבר חשבון" : "אין לי חשבון, הרשמה"}
      </button>
    </div>
  );
}