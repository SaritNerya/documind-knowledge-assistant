import { useId, useState } from "react";

// כרטיס הציטוט. quote יגיע מהשרת בעתיד; בינתיים מוצגים רק המסמך והעמוד.
function QuoteCard({ id, number, source }) {
  return (
    <blockquote className="quote" id={id}>
      {source.quote && (
        <p>
          <mark>{source.quote}</mark>
        </p>
      )}
      <footer className="quote-cite">
        <span className="footnote-ref">{number}</span> מתוך{" "}
        <cite className="bidi">{source.filename}</cite>, עמוד {source.page}
      </footer>
    </blockquote>
  );
}

// המקורות כהערות שוליים: צ'יפ לכל מקור. מקור ממסמך פותח וסוגר ציטוט, מקור מהרשת הוא קישור.
export default function SourceNotes({ sources }) {
  const [openIndex, setOpenIndex] = useState(null);
  const baseId = useId();
  const quoteId = (i) => `${baseId}-quote-${i}`;

  return (
    <div className="source-notes">
      <ul className="chip-list" aria-label="מקורות">
        {sources.map((s, i) => (
          <li key={i}>
            {s.url ? (
              <a className="chip" href={s.url} target="_blank" rel="noreferrer">
                <span className="chip-num">{i + 1}</span>
                <span className="bidi">{s.filename}</span>
              </a>
            ) : (
              <button
                type="button"
                className={`chip${openIndex === i ? " is-active" : ""}`}
                aria-expanded={openIndex === i}
                aria-controls={openIndex === i ? quoteId(i) : undefined}
                onClick={() => setOpenIndex(openIndex === i ? null : i)}
              >
                <span className="chip-num">{i + 1}</span>
                <span className="bidi">{s.filename}</span>
                <span>עמוד {s.page}</span>
              </button>
            )}
          </li>
        ))}
      </ul>
      {openIndex !== null && (
        <QuoteCard id={quoteId(openIndex)} number={openIndex + 1} source={sources[openIndex]} />
      )}
    </div>
  );
}
