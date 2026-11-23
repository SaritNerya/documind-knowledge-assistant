import Answer from "./Answer";

export default function MessageBubble({ role, content, sources }) {
  if (role === "user") return <div className="bubble-question">{content}</div>;
  return <Answer content={content} sources={sources ?? []} />;
}
