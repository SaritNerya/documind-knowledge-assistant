import { changePassword } from "../api";
import PasswordField from "../components/PasswordField";
import PasswordStrength from "../components/PasswordStrength";
import StatusMessage from "../components/StatusMessage";
import useAsyncAction from "../hooks/useAsyncAction";
import useFormFields from "../hooks/useFormFields";
import { validatePasswordChange } from "../validation";

const EMPTY = { current: "", password: "", confirm: "" };

/** החלפת סיסמה: נוכחית, חדשה ואימות. בדיקות בזמן הקלדה, כמו במסך ההרשמה. */
export default function ChangePasswordForm() {
  const { values, bind, reset } = useFormFields(EMPTY);
  const save = useAsyncAction();
  const errors = validatePasswordChange(values);
  const filled = values.current && values.password && values.confirm;
  const canSubmit = filled && Object.keys(errors).length === 0 && !save.pending;

  async function handleSubmit(e) {
    e.preventDefault();
    if (!canSubmit) return;
    if (await save.run(() => changePassword(values.current, values.password), "הסיסמה הוחלפה")) {
      reset();
    }
  }

  return (
    <section className="card page-section">
      <h3>החלפת סיסמה</h3>
      <form onSubmit={handleSubmit} noValidate>
        <PasswordField label="סיסמה נוכחית" autoComplete="current-password" {...bind("current")} />
        <PasswordField
          label="סיסמה חדשה"
          autoComplete="new-password"
          error={errors.password}
          {...bind("password")}
        >
          <PasswordStrength password={values.password} />
        </PasswordField>
        <PasswordField
          label="אימות הסיסמה החדשה"
          autoComplete="new-password"
          error={errors.confirm}
          {...bind("confirm")}
        />
        <button type="submit" className="btn-playful" disabled={!canSubmit}>
          {save.pending ? "מחליפה..." : "החלפת סיסמה"}
        </button>
        <StatusMessage tone={save.tone} message={save.message} />
      </form>
    </section>
  );
}
