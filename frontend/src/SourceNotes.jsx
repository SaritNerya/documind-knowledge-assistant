import { useEffect, useRef } from "react";
import HighlightedText from "./components/HighlightedText";

/**
 * כרטיס הציטוט: הקטע המדויק מהמסמך, והמשפט הרלוונטי מסומן במרקר.
 * בפתיחה גוללים את המשפט המסומן לתוך התצוגה (הקטע עצמו יכול להיות ארוך).
 */
function QuoteCard({ id, number, source }) {
  const markRef = useRef(null);

  useEffect(() => {
    markRef.current?.scrollIntoView({ block: "nearest" });
  }, [source]);

  return (
    <blockquote className="quote" id={id}>
      {source.quote ? (
        <p className="quote-text">
          <HighlightedText markRef={markRef} text={source.quote} highlight={source.highlight} />
        </p>
      ) : (
        <p className="hint">הקטע המדויק נשמר רק בתשובות חדשות.</p>
      )}
      <footer className="quote-cite">
        <span className="footnote-ref">{number}</span> מתוך{" "}
        <cite className="bidi">{source.filename}</cite>, עמוד {source.page}
      </footer>
    </blockquote>
  );
}

/**
 * המקורות כהערות שוליים: צ'יפ לכל מקור. מקור ממסמך פותח וסוגר את הציטוט, מקור מהרשת הוא קישור.
 * המקור הפתוח מנוהל ב-Answer, כי גם מספרי ההערות שבתוך התשובה פותחים אותו.
 */
export default function SourceNotes({ sources, openIndex, onToggle, quoteIdOf }) {
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
                aria-controls={openIndex === i ? quoteIdOf(i) : undefined}
                onClick={() => onToggle(i)}
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
        <QuoteCard id={quoteIdOf(openIndex)} number={openIndex + 1} source={sources[openIndex]} />
      )}
    </div>
  );
}
