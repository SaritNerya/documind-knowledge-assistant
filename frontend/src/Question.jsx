import CopyButton from "./components/CopyButton";

/** שאלת המשתמש: בועה, ומתחתיה שורת פעולות (כרגע: העתקת השאלה). */
export default function Question({ content }) {
  return (
    <div className="question">
      <div className="bubble-question">{content}</div>
      <div className="message-actions">
        <CopyButton text={content} label="העתקת השאלה" />
      </div>
    </div>
  );
}
