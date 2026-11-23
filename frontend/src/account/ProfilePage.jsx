import { getUsage } from "../api";
import Page from "../components/Page";
import StatCard from "../components/StatCard";
import useApiData from "../hooks/useApiData";
import useCurrentUser from "../hooks/useCurrentUser";
import { displayNameOf } from "./CurrentUserContext";
import DisplayNameForm from "./DisplayNameForm";

const joinedDate = new Intl.DateTimeFormat("he-IL", { dateStyle: "long" });

/** הפרופיל: מי אני (שם, אימייל, תאריך הצטרפות) ומה השימוש שלי. */
export default function ProfilePage() {
  const { user } = useCurrentUser();
  const usage = useApiData(getUsage);

  if (!user) return <Page title="פרופיל"><p className="hint">טוען...</p></Page>;

  const stats = [
    { label: "מסמכים שהעלית", value: usage.data?.documents, icon: "📄" },
    { label: "שיחות", value: usage.data?.conversations, icon: "💬" },
    { label: "שאלות ששאלת", value: usage.data?.questions, icon: "✍️" },
  ];

  return (
    <Page title={`שלום, ${displayNameOf(user)}`} subtitle="הפרטים שלך ומה עשית עד עכשיו ב-DocuMind">
      <section className="card page-section">
        <h3>הפרטים שלך</h3>
        <DisplayNameForm />
        <dl className="details">
          <div>
            <dt>אימייל</dt>
            <dd className="bidi" dir="ltr">{user.email}</dd>
          </div>
          <div>
            <dt>תאריך הצטרפות</dt>
            <dd>{joinedDate.format(new Date(user.created_at))}</dd>
          </div>
        </dl>
      </section>

      <section className="card page-section">
        <h3>השימוש שלך</h3>
        {usage.error ? (
          <p className="error">{usage.error}</p>
        ) : (
          <div className="stat-grid">
            {stats.map((s) => (
              <StatCard key={s.label} label={s.label} icon={s.icon} value={usage.loading ? "…" : s.value} />
            ))}
          </div>
        )}
      </section>
    </Page>
  );
}
