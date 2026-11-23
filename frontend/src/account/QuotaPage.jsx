import { getUsage } from "../api";
import Page from "../components/Page";
import ProgressBar from "../components/ProgressBar";
import useApiData from "../hooks/useApiData";

const LOW_RATIO = 0.2; // מתחת ל-20% שנשארו: הפס נצבע באזהרה עדינה

// הסבר קצר לכל מצב. המכסה "מתגלגלת": כל שאלה חוזרת למכסה 24 שעות אחרי ששאלו אותה
const NOTES = {
  ok: "המכסה נספרת לפי 24 השעות האחרונות: כל שאלה חוזרת אלייך יום אחרי ששאלת אותה.",
  low: "נשארו מעט שאלות להיום. כל שאלה חוזרת אלייך 24 שעות אחרי ששאלת אותה.",
  empty: "המכסה של היום נגמרה. השאלות יחזרו בהדרגה, 24 שעות אחרי כל שאלה.",
};

function quotaLevel(remaining, limit) {
  if (remaining === 0) return "empty";
  return remaining / limit <= LOW_RATIO ? "low" : "ok";
}

/** המכסה היומית: כמה שאלות נשארו היום, עם פס התקדמות. */
export default function QuotaPage() {
  const { data, error, loading } = useApiData(getUsage);

  return (
    <Page title="מכסה יומית" subtitle="כמה שאלות נשארו לך היום">
      <section className="card page-section quota-card">
        {loading && <p className="hint">טוען...</p>}
        {error && <p className="error">{error}</p>}
        {data && <QuotaSummary limit={data.daily_limit} used={data.used_today} />}
      </section>
    </Page>
  );
}

function QuotaSummary({ limit, used }) {
  const remaining = Math.max(0, limit - used);
  const level = quotaLevel(remaining, limit);

  return (
    <>
      <p className="quota-headline">
        נשארו <span className="quota-number">{remaining}</span> מתוך {limit} שאלות היום
      </p>
      <ProgressBar value={remaining} max={limit} label="שאלות שנשארו היום" level={level} />
      <p className="hint">{NOTES[level]}</p>
    </>
  );
}
