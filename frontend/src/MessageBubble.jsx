import Answer from "./Answer";
import Question from "./Question";

export default function MessageBubble({ role, content, sources }) {
  if (role === "user") return <Question content={content} />;
  return <Answer content={content} sources={sources ?? []} />;
}
