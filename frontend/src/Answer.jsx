import SourceNotes from "./SourceNotes";

// תשובה שנשענת על מסמכים: יש מקורות, ולאף אחד מהם אין url (מקורות מהרשת תמיד עם url).
// שיחת חולין ותשובה בלי מידע חוזרות בלי מקורות, ולכן גם הן בלי חותמת.
const isDocumentBacked = (sources) => sources.length > 0 && sources.every((s) => !s.url);

// שורת המשנה של החותמת: המסמך שאומת מולו, ו"ועוד N" אם היו כמה
function verifiedAgainst(sources) {
  const names = [...new Set(sources.map((s) => s.filename))];
  return names.length > 1 ? `${names[0]} ועוד ${names.length - 1}` : names[0];
}

export default function Answer({ content, sources = [], thinking = false }) {
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
        {sources.map((_, i) => (
          <sup key={i} className="footnote-ref">{i + 1}</sup>
        ))}
      </p>
      {sources.length > 0 && <SourceNotes sources={sources} />}
    </article>
  );
}
