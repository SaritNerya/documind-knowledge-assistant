import { useState } from "react";
import { login, register } from "./api";
import Logo from "./components/Logo";
import PasswordField from "./components/PasswordField";
import PasswordStrength from "./components/PasswordStrength";
import Tabs from "./components/Tabs";
import TextField from "./components/TextField";
import { validateAuthForm } from "./validation";

const TABS = [
  { id: "login", label: "התחברות" },
  { id: "register", label: "הרשמה" },
];
const PANEL_ID = "auth-panel";
const EMPTY_FORM = { email: "", password: "", confirm: "", inviteCode: "documind2026" };

export default function Login({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [remember, setRemember] = useState(false);

  const isRegister = mode === "register";
  const errors = validateAuthForm(form, isRegister);
  const requiredFilled = form.email && form.password && (!isRegister || (form.confirm && form.inviteCode));
  const canSubmit = !loading && requiredFilled && Object.keys(errors).length === 0;

  // מחזיר value ו-onChange לשדה, כדי לא לחזור על אותו קוד בכל שדה
  const bind = (name) => ({
    value: form[name],
    onChange: (e) => setForm((prev) => ({ ...prev, [name]: e.target.value })),
  });

  function switchMode(next) {
    setMode(next);
    setError("");
    setForm((prev) => ({ ...EMPTY_FORM, email: prev.email })); // האימייל נשמר במעבר בין הלשוניות
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!canSubmit) return;
    setError("");
    setLoading(true);
    try {
      if (isRegister) await register(form.email, form.password, form.inviteCode);
      await login(form.email, form.password, remember);
      onLogin();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-page" dir="rtl">
      <div className="card auth-card">
        <Logo as="h1" />
        <p className="tagline">שאלי את המסמכים שלך</p>

        <Tabs tabs={TABS} value={mode} onChange={switchMode} panelId={PANEL_ID} label="כניסה לחשבון" />

        <form
          id={PANEL_ID}
          role="tabpanel"
          aria-labelledby={`${PANEL_ID}-${mode}`}
          className="auth-form"
          onSubmit={handleSubmit}
          noValidate
        >
          <TextField
            label="אימייל"
            type="email"
            autoComplete="email"
            dir="ltr"
            error={errors.email}
            {...bind("email")}
          />

          <PasswordField
            label="סיסמה"
            autoComplete={isRegister ? "new-password" : "current-password"}
            error={errors.password}
            {...bind("password")}
          >
            {isRegister && <PasswordStrength password={form.password} />}
          </PasswordField>

          {isRegister && (
            <>
              <PasswordField
                label="אימות סיסמה"
                autoComplete="new-password"
                error={errors.confirm}
                {...bind("confirm")}
              />
              <TextField label="קוד הזמנה" autoComplete="off" {...bind("inviteCode")} />
            </>
          )}

          <label className="checkbox">
            <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
            זכור אותי
          </label>

          {error && <p className="error" role="alert">{error}</p>}

          <button type="submit" className="auth-submit" disabled={!canSubmit}>
            {loading ? "רגע..." : isRegister ? "יצירת חשבון" : "כניסה"}
          </button>
        </form>
      </div>
    </main>
  );
}
