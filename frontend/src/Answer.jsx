import { useId, useState } from "react";
import SourceNotes from "./SourceNotes";
import CopyButton from "./components/CopyButton";

// תשובה שנשענת על מסמכים: יש מקורות, ולאף אחד מהם אין url (מקורות מהרשת תמיד עם url).
// שיחת חולין ותשובה בלי מידע חוזרות בלי מקורות, ולכן גם הן בלי חותמת.
const isDocumentBacked = (sources) => sources.length > 0 && sources.every((s) => !s.url);

// שורת המשנה של החותמת: המסמך שאומת מולו, ו"ועוד N" אם היו כמה
function verifiedAgainst(sources) {
  const names = [...new Set(sources.map((s) => s.filename))];
  return names.length > 1 ? `${names[0]} ועוד ${names.length - 1}` : names[0];
}

/** מספר הערה בתוך התשובה. במקור ממסמך הוא כפתור שפותח את הציטוט */
function FootnoteRef({ index, source, open, controls, onToggle }) {
  if (source.url) return <sup className="footnote-ref">{index + 1}</sup>;
  return (
    <sup>
      <button
        type="button"
        className="footnote-ref footnote-button"
        aria-label={`מקור ${index + 1}: ${source.filename}, עמוד ${source.page}`}
        aria-expanded={open}
        aria-controls={open ? controls : undefined}
        onClick={() => onToggle(index)}
      >
        {index + 1}
      </button>
    </sup>
  );
}

export default function Answer({ content, sources = [], thinking = false }) {
  const [openIndex, setOpenIndex] = useState(null);
  const baseId = useId();
  // מזהה כרטיס הציטוט: משותף לצ'יפים ולמספרי ההערות, בשביל aria-controls
  const quoteIdOf = (i) => `${baseId}-quote-${i}`;
  const toggle = (i) => setOpenIndex((current) => (current === i ? null : i));
  const verified = isDocumentBacked(sources);
  const className = ["answer", verified && "is-verified", thinking && "is-thinking"]
    .filter(Boolean)
    .join(" ");

  return (
    <article className={className} aria-busy={thinking || undefined}>
      {verified && (
        <div className="stamp" role="note">
          <span className="stamp-title">מאומת מול המסמך</span>
          <span className="stamp-doc bidi">{verifiedAgainst(sources)}</span>
        </div>
      )}
      <p className="answer-text">
        {content}
        {sources.map((s, i) => (
          <FootnoteRef
            key={i}
            index={i}
            source={s}
            open={openIndex === i}
            controls={quoteIdOf(i)}
            onToggle={toggle}
          />
        ))}
      </p>
      {!thinking && (
        <div className="answer-actions">
          {/* content הוא טקסט התשובה בלבד: המקורות ומספרי ההערות לא נכללים בו */}
          <CopyButton text={content} label="העתקת התשובה" />
        </div>
      )}
      {sources.length > 0 && (
        <SourceNotes sources={sources} openIndex={openIndex} onToggle={toggle} quoteIdOf={quoteIdOf} />
      )}
    </article>
  );
}
