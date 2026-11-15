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
    Real Tool 1 (Reviewer Manager Agent):
    Deduplicates overlapping or redundant findings reported across multiple agents
    (keyed on file_path, line_number, and rule_id) and sorts them strictly
    by severity (CRITICAL -> HIGH -> MEDIUM -> LOW -> INFO).
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

    # Sort primarily by severity rank, secondarily by file and line
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
    Real Tool 2 (Reviewer Manager Agent):
    Applies enterprise governance gates to decide between 'approve' and 'request-changes':
    - ANY CRITICAL finding -> REJECT (request-changes)
    - ANY HIGH finding (e.g. untested public logic, high security risk) -> REJECT (request-changes)
    - Test coverage gap blocker -> REJECT (request-changes)
    - Medium or below only -> APPROVE (with non-blocking review recommendations)
    - Zero issues -> APPROVE (clean pass)
    """
    critical_count = severity_counts.get("CRITICAL", 0)
    high_count = severity_counts.get("HIGH", 0)
    medium_count = severity_counts.get("MEDIUM", 0)
    low_count = severity_counts.get("LOW", 0)

    reasons: List[str] = []

    if critical_count > 0:
        reasons.append(f"Blocked by {critical_count} CRITICAL severity violation(s) (e.g., security risks, credentials, injections).")
    if high_count > 0:
        reasons.append(f"Blocked by {high_count} HIGH severity finding(s) (e.g., missing test coverage, syntax issues).")
    if has_test_coverage_blocker:
        reasons.append("Blocked by test coverage policy: new public APIs introduced without accompanying tests.")

    if reasons:
        verdict = "request-changes"
        summary = "Changes requested. Code cannot be merged until all CRITICAL and HIGH severity issues are resolved."
    else:
        verdict = "approve"
        if medium_count > 0 or low_count > 0:
            summary = f"Approved with advisories: {medium_count} medium and {low_count} low/style notices. Safe to merge."
        else:
            summary = "Approved cleanly: code meets all style, security, and coverage quality gates."

    return {
        "verdict": verdict,
        "summary": summary,
        "blocking_reasons": reasons,
        "counts": severity_counts,
    }
