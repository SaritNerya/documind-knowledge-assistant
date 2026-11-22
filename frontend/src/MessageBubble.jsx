export default function MessageBubble({ role, content, sources }) {
  return (
    <div className={`bubble ${role}`}>
      <div>{content}</div>
      {sources?.length > 0 && (
        <div className="sources">
          מקורות:
          {sources.map((s, i) =>
            s.url ? (
              <a className="source-tag" key={i} href={s.url} target="_blank" rel="noreferrer">
                {s.filename}
              </a>
            ) : (
              <span className="source-tag" key={i}>{s.filename}, עמוד {s.page}</span>
            )
          )}
        </div>
      )}
    </div>
  );
}
