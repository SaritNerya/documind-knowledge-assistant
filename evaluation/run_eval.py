import json
import sys
import time
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from app.core.database import SessionLocal
from app.services.rag import answer_question

USER_ID = 1  # המשתמש שהעלה את המסמכים
HERE = Path(__file__).parent


def average(values):
    return sum(values) / len(values) if values else 0.0


def keyword_groups(q):
    """כל קבוצה = חלופות. נכון אם מכל קבוצה מופיעה לפחות מילה אחת."""
    return [[k] if isinstance(k, str) else k for k in q.get("keywords", [])]


def matches(text, groups):
    return all(any(alt in text for alt in group) for group in groups)


def main():
    questions = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))
    db = SessionLocal()
    results = []

    for q in questions:
        start = time.perf_counter()
        # בהערכה בלי חיפוש אינטרנט, כדי למדוד רק את המסמכים
        r = answer_question(db, USER_ID, q["question"], q.get("history", []), allow_web=False)
        elapsed = time.perf_counter() - start

        groups = keyword_groups(q)
        chunk_hit = retrieval_hit = None

        if q["type"] == "answerable":
            retrieved_text = " ".join(c["content"] for c in r.chunks)
            retrieval_hit = any(c["filename"] == q["source"] for c in r.chunks)
            chunk_hit = matches(retrieved_text, groups)
            correct = r.found and matches(r.answer, groups)
        elif q["type"] == "unanswerable":
            correct = not r.found
        elif q["type"] == "meta":        # שאלות על המסמכים עצמם
            correct = matches(r.answer, groups)
        elif q["type"] == "chitchat":    # שיחה קלילה: תשובה, בלי מקורות
            correct = bool(r.answer) and not r.sources
        else:
            raise ValueError(f"unknown type: {q['type']}")

        results.append({
            "question": q["question"], "type": q["type"], "correct": correct,
            "retrieval_hit": retrieval_hit, "chunk_hit": chunk_hit,
            "found": r.found, "sources": r.sources, "queries": r.queries,
            "latency": round(elapsed, 2), "answer": r.answer,
        })

    (HERE / "results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("\n===== סיכום =====")
    for t in ("answerable", "unanswerable", "meta", "chitchat"):
        subset = [r for r in results if r["type"] == t]
        if subset:
            print(f"{t:13} {len(subset):3} שאלות | נכון: {average([r['correct'] for r in subset]):.0%}")
    ans = [r for r in results if r["type"] == "answerable"]
    if ans:
        print(f"שליפה ברמת מסמך: {average([r['retrieval_hit'] for r in ans]):.0%} | "
              f"ברמת קטע: {average([r['chunk_hit'] for r in ans]):.0%}")
    print(f"זמן ממוצע: {average([r['latency'] for r in results]):.2f} שניות")

    print("\n===== שאלות שנכשלו =====")
    for r in results:
        if not r["correct"]:
            print(f"- [{r['type']}] {r['question']}")
            print(f"  found: {r['found']} | chunk_hit: {r['chunk_hit']}")
            print(f"  תשובה: {r['answer'][:150]}")


if __name__ == "__main__":
    main()