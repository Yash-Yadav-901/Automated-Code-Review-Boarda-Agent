from typing import Any, Dict, List

SEVERITY_ORDER = {
    "CRITICAL": 1,
    "HIGH": 2,
    "MEDIUM": 3,
    "LOW": 4,
    "INFO": 5,
}


def deduplicate_and_rank_findings(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicates findings keyed on file_path, line_number, and rule_id,
    and sorts them strictly by severity (CRITICAL -> INFO).
    """
    seen_keys = set()
    deduped: List[Dict[str, Any]] = []

    for f in findings:
        key = (
            f.get("file_path", ""),
            f.get("line_number"),
            f.get("rule_id", ""),
            f.get("category", ""),
        )
        if key not in seen_keys:
            seen_keys.add(key)
            deduped.append(f)

    deduped.sort(
        key=lambda x: (
            SEVERITY_ORDER.get(x.get("severity", "INFO"), 99),
            x.get("file_path", ""),
            x.get("line_number") or 0,
        )
    )

    return deduped


def compute_merge_verdict(
    severity_counts: Dict[str, int],
    has_test_coverage_blocker: bool = False
) -> Dict[str, Any]:
    """
    Evaluates merge eligibility:
    - Any CRITICAL or HIGH finding blocks merge (request-changes).
    - Missing test coverage blocker blocks merge (request-changes).
    - Otherwise approves with advisories or cleanly.
    """
    critical_count = severity_counts.get("CRITICAL", 0)
    high_count = severity_counts.get("HIGH", 0)
    medium_count = severity_counts.get("MEDIUM", 0)
    low_count = severity_counts.get("LOW", 0)

    reasons: List[str] = []

    if critical_count > 0:
        reasons.append(f"Blocked by {critical_count} CRITICAL violation(s).")
    if high_count > 0:
        reasons.append(f"Blocked by {high_count} HIGH severity finding(s).")
    if has_test_coverage_blocker:
        reasons.append("Blocked by test coverage policy: new public APIs introduced without tests.")

    if reasons:
        verdict = "request-changes"
        summary = "Changes requested. Code cannot be merged until CRITICAL and HIGH issues are resolved."
    else:
        verdict = "approve"
        if medium_count > 0 or low_count > 0:
            summary = f"Approved with advisories: {medium_count} medium and {low_count} low/style notices."
        else:
            summary = "Approved cleanly: code meets all style, security, and coverage quality gates."

    return {
        "verdict": verdict,
        "summary": summary,
        "blocking_reasons": reasons,
        "counts": severity_counts,
    }
