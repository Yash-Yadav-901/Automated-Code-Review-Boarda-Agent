"""
Plain Python tools used across the Automated Code Review Board agents.
Each agent calls at least two real tools written as plain Python functions.
"""
from .diff_tools import parse_unified_diff, compute_diff_metrics
from .style_tools import check_pep8_and_docstrings, calculate_cyclomatic_complexity
from .security_tools import scan_secrets_and_credentials, audit_code_vulnerabilities
from .coverage_tools import detect_test_file_presence, evaluate_test_adequacy
from .review_tools import deduplicate_and_rank_findings, compute_merge_verdict
from .patch_tools import extract_code_context, generate_unified_patch

__all__ = [
    "parse_unified_diff",
    "compute_diff_metrics",
    "check_pep8_and_docstrings",
    "calculate_cyclomatic_complexity",
    "scan_secrets_and_credentials",
    "audit_code_vulnerabilities",
    "detect_test_file_presence",
    "evaluate_test_adequacy",
    "deduplicate_and_rank_findings",
    "compute_merge_verdict",
    "extract_code_context",
    "generate_unified_patch",
]
