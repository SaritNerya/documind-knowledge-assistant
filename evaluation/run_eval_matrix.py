import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
os.chdir(BACKEND)

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.api.chat import NOT_FOUND_ANSWER
from app.core.database import SessionLocal
from app.services.llm import answer_from_context
from app.services.retrieval import search_chunks

USER_ID = 1
HERE = Path(__file__).parent
EXPERIMENTS_DIR = HERE / "experiments"
MIN_SCORES = [0.2, 0.3, 0.4, 0.5]


def average(values):
    return sum(values) / len(values) if values else 0.0


def keyword_groups(question_obj):
    """Return list of alternative keyword groups; each group is treated as OR."""
    return [[k] if isinstance(k, str) else k for k in question_obj.get("keywords", [])]


def matches(text, groups):
    if not groups:
        return False
    return all(any(alt.lower() in text.lower() for alt in group) for group in groups)


def dedupe_chunks(chunks):
    unique = {}
    for chunk in chunks:
        key = (chunk["filename"], chunk["page"], (chunk["content"] or "").strip())
        if key not in unique:
            unique[key] = chunk
    return list(unique.values())


def classify_failure(question, answer, relevant_chunks, deduped_chunks, threshold, retrieval_hit_after, chunk_hit, answer_status):
    if question["type"] == "answerable":
        if not retrieval_hit_after:
            return "retrieval_miss"
        if not chunk_hit:
            return "chunk_miss"
        if answer_status == "review_needed":
            return "review_needed"
        if answer_status == "incorrect":
            return "answer_incorrect"
        return "none"

    if answer_status == "incorrect_refusal":
        return "hallucination"
    if answer_status == "review_needed":
        return "review_needed"
    return "none"


def answer_status_for(question, answer):
    text = (answer or "").strip()
    refused = "לא מצאתי" in text or "אין לי מידע" in text
    if question["type"] == "answerable":
        groups = keyword_groups(question)
        if not groups:
            return "review_needed"
        if refused:
            return "incorrect"
        if matches(text, groups):
            return "correct"
        return "review_needed"

    # unanswerable
    if refused:
        return "correct_refusal"
    return "incorrect_refusal"


def run_single_experiment(min_score):
    questions = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))
    db = SessionLocal()
    results = []
    retrieval_times = []
    answer_times = []
    duplicate_chunks_removed = 0

    try:
        for q in questions:
            retrieval_start = time.perf_counter()
            raw_chunks = search_chunks(db, USER_ID, q["question"])
            deduped_chunks = dedupe_chunks(raw_chunks)
            duplicate_chunks_removed += max(0, len(raw_chunks) - len(deduped_chunks))
            retrieval_elapsed = time.perf_counter() - retrieval_start
            retrieval_times.append(retrieval_elapsed)

            relevant = [c for c in deduped_chunks if c["score"] >= min_score]
            retrieval_hit_before = any(c["filename"] == q["source"] for c in deduped_chunks)
            retrieval_hit_after = any(c["filename"] == q["source"] for c in relevant)

            if q["type"] == "answerable":
                groups = keyword_groups(q)
                retrieved_text = " ".join(c["content"] for c in deduped_chunks)
                chunk_hit = matches(retrieved_text, groups)
            else:
                groups = []
                chunk_hit = None

            if relevant:
                answer_start = time.perf_counter()
                answer = answer_from_context(q["question"], relevant)
                answer_elapsed = time.perf_counter() - answer_start
                answer_times.append(answer_elapsed)
            else:
                answer = NOT_FOUND_ANSWER
                answer_elapsed = 0.0

            answer_state = answer_status_for(q, answer)
            failure_type = classify_failure(
                q,
                answer,
                relevant,
                deduped_chunks,
                min_score,
                retrieval_hit_after,
                chunk_hit,
                answer_state,
            )

            results.append(
                {
                    "question": q["question"],
                    "type": q["type"],
                    "source": q.get("source"),
                    "min_score": min_score,
                    "retrieval_hit_before_threshold": retrieval_hit_before,
                    "retrieval_hit_after_threshold": retrieval_hit_after,
                    "top_score": round(deduped_chunks[0]["score"], 3) if deduped_chunks else 0.0,
                    "relevant_count": len(relevant),
                    "unique_retrieval_count": len(deduped_chunks),
                    "chunk_hit": chunk_hit,
                    "answer_status": answer_state,
                    "failure_type": failure_type,
                    "retrieval_latency_seconds": round(retrieval_elapsed, 4),
                    "answer_latency_seconds": round(answer_elapsed, 4),
                    "answer": answer,
                    "retrieved": [
                        {
                            "file": c["filename"],
                            "page": c["page"],
                            "score": round(c["score"], 3),
                            "text": c["content"],
                        }
                        for c in deduped_chunks
                    ],
                }
            )
    finally:
        db.close()

    answerable = [r for r in results if r["type"] == "answerable"]
    unanswerable = [r for r in results if r["type"] == "unanswerable"]

    retrieval_summary = {
        "hit_rate_before_threshold": average([1.0 if r["retrieval_hit_before_threshold"] else 0.0 for r in answerable]),
        "hit_rate_after_threshold": average([1.0 if r["retrieval_hit_after_threshold"] else 0.0 for r in answerable]),
        "avg_top_score_answerable": average([r["top_score"] for r in answerable]),
        "avg_top_score_unanswerable": average([r["top_score"] for r in unanswerable]),
        "avg_retrieval_latency": average([r["retrieval_latency_seconds"] for r in results]),
        "duplicate_chunks_removed": duplicate_chunks_removed,
    }

    answer_accuracy = average([1.0 if r["answer_status"] == "correct" else 0.0 for r in answerable])
    refusal_rate = average([1.0 if r["answer_status"] == "correct_refusal" else 0.0 for r in unanswerable])
    hallucination_rate = average([1.0 if r["answer_status"] == "incorrect_refusal" else 0.0 for r in unanswerable])
    review_needed = average([1.0 if r["answer_status"] == "review_needed" else 0.0 for r in results])

    summary = {
        "min_score": min_score,
        "question_counts": {
            "total": len(results),
            "answerable": len(answerable),
            "unanswerable": len(unanswerable),
        },
        "retrieval": retrieval_summary,
        "answer_generation": {
            "answer_accuracy": answer_accuracy,
            "refusal_rate": refusal_rate,
            "hallucination_rate": hallucination_rate,
            "review_needed_rate": review_needed,
            "avg_answer_latency": average([r["answer_latency_seconds"] for r in results if r["answer_latency_seconds"] > 0]),
        },
        "heuristic_note": "Keyword matching is a heuristic signal only; it is not a semantic equivalence check and should be treated as a review signal when uncertain.",
    }

    return {
        "summary": summary,
        "details": results,
    }


def write_markdown_report(experiment_name, experiment_data):
    summary = experiment_data["summary"]
    details = experiment_data["details"]
    lines = []
    lines.append(f"# Evaluation report: {experiment_name}")
    lines.append("")
    lines.append(f"- MIN_SCORE: {summary['min_score']}")
    lines.append(f"- Total questions: {summary['question_counts']['total']}")
    lines.append(f"- Answerable: {summary['question_counts']['answerable']}")
    lines.append(f"- Unanswerable: {summary['question_counts']['unanswerable']}")
    lines.append("")
    lines.append("## Retrieval")
    lines.append(f"- Retrieval Hit Rate before threshold: {summary['retrieval']['hit_rate_before_threshold']:.2%}")
    lines.append(f"- Retrieval Hit Rate after threshold: {summary['retrieval']['hit_rate_after_threshold']:.2%}")
    lines.append(f"- Avg top score (answerable): {summary['retrieval']['avg_top_score_answerable']:.3f}")
    lines.append(f"- Avg top score (unanswerable): {summary['retrieval']['avg_top_score_unanswerable']:.3f}")
    lines.append(f"- Avg retrieval latency: {summary['retrieval']['avg_retrieval_latency']:.3f}s")
    lines.append(f"- Duplicate chunks removed: {summary['retrieval']['duplicate_chunks_removed']}")
    lines.append("")
    lines.append("## Answer generation")
    lines.append(f"- Answer Accuracy: {summary['answer_generation']['answer_accuracy']:.2%}")
    lines.append(f"- Refusal Rate: {summary['answer_generation']['refusal_rate']:.2%}")
    lines.append(f"- Hallucination Rate: {summary['answer_generation']['hallucination_rate']:.2%}")
    lines.append(f"- Review-needed rate: {summary['answer_generation']['review_needed_rate']:.2%}")
    lines.append(f"- Avg answer latency: {summary['answer_generation']['avg_answer_latency']:.3f}s")
    lines.append("")
    lines.append("## Failed questions")
    failed = [r for r in details if r["failure_type"] not in ("none", None)]
    if not failed:
        lines.append("- No failed questions for this threshold.")
    else:
        for r in failed:
            lines.append(f"- [{r['type']}] {r['question']}")
            lines.append(f"  - failure_type: {r['failure_type']}")
            lines.append(f"  - retrieval_after_threshold: {r['retrieval_hit_after_threshold']}")
            lines.append(f"  - chunk_hit: {r['chunk_hit']}")
            lines.append(f"  - answer_status: {r['answer_status']}")
    lines.append("")
    lines.append(summary["heuristic_note"])
    return "\n".join(lines) + "\n"


def save_experiment(min_score, experiment_path):
    data = run_single_experiment(min_score)
    (experiment_path / "summary.json").write_text(
        json.dumps(data["summary"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (experiment_path / "details.json").write_text(
        json.dumps(data["details"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (experiment_path / "summary.md").write_text(
        write_markdown_report(f"MIN_SCORE={min_score}", data),
        encoding="utf-8",
    )
    return data


def compare_experiments(experiment_records):
    comparison_rows = []
    for record in experiment_records:
        s = record["summary"]
        comparison_rows.append(
            {
                "min_score": s["min_score"],
                "retrieval_hit_rate_after": s["retrieval"]["hit_rate_after_threshold"],
                "answer_accuracy": s["answer_generation"]["answer_accuracy"],
                "refusal_rate": s["answer_generation"]["refusal_rate"],
                "hallucination_rate": s["answer_generation"]["hallucination_rate"],
                "avg_retrieval_latency": s["retrieval"]["avg_retrieval_latency"],
                "avg_answer_latency": s["answer_generation"]["avg_answer_latency"],
                "review_needed_rate": s["answer_generation"]["review_needed_rate"],
            }
        )

    comparison_json = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "experiments": comparison_rows,
    }
    return comparison_json


def main():
    EXPERIMENTS_DIR.mkdir(exist_ok=True)
    experiment_records = []

    for score in MIN_SCORES:
        stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        experiment_dir = EXPERIMENTS_DIR / f"min_score_{score}_{stamp}"
        experiment_dir.mkdir(parents=True, exist_ok=True)
        data = save_experiment(score, experiment_dir)
        experiment_records.append(data)

    comparison = compare_experiments(experiment_records)
    comparison_path = EXPERIMENTS_DIR / f"comparison_{datetime.now().strftime('%Y%m%dT%H%M%S')}.json"
    comparison_path.write_text(json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8")

    table_lines = [
        "# Comparison of MIN_SCORE values",
        "",
        "| MIN_SCORE | Retrieval Hit Rate After | Answer Accuracy | Refusal Rate | Hallucination Rate | Avg Retrieval Latency | Avg Answer Latency | Review Needed |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for row in comparison["experiments"]:
        table_lines.append(
            "| {min_score} | {retrieval_hit_rate_after:.2%} | {answer_accuracy:.2%} | {refusal_rate:.2%} | {hallucination_rate:.2%} | {avg_retrieval_latency:.3f}s | {avg_answer_latency:.3f}s | {review_needed_rate:.2%} |".format(
                min_score=row["min_score"],
                retrieval_hit_rate_after=row["retrieval_hit_rate_after"],
                answer_accuracy=row["answer_accuracy"],
                refusal_rate=row["refusal_rate"],
                hallucination_rate=row["hallucination_rate"],
                avg_retrieval_latency=row["avg_retrieval_latency"],
                avg_answer_latency=row["avg_answer_latency"],
                review_needed_rate=row["review_needed_rate"],
            )
        )

    comparison_path_md = str(comparison_path).replace(".json", ".md")
    Path(comparison_path_md).write_text("\n".join(table_lines) + "\n", encoding="utf-8")

    print("Created experiments:")
    for record in experiment_records:
        print(f"- MIN_SCORE {record['summary']['min_score']}: {record['summary']['question_counts']['total']} questions")

    print(f"\nComparison saved to {comparison_path}")
    print(f"Markdown comparison saved to {comparison_path_md}")


if __name__ == "__main__":
    main()
