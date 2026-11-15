import ast
import re
from typing import Any, Dict, List, Optional


def detect_test_file_presence(
    modified_files: List[str],
    all_diff_files: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Evaluates whether business logic modifications have corresponding test modifications.
    Pairs implementation files with their anticipated test files (e.g. `service.py` -> `test_service.py`).
    """
    if all_diff_files is None:
        all_diff_files = modified_files

    code_files = [f for f in modified_files if not _is_test(f) and f.endswith(".py")]
    test_files = [f for f in all_diff_files if _is_test(f)]

    uncovered_files: List[str] = []
    paired_files: Dict[str, Optional[str]] = {}

    for c_file in code_files:
        base_name = c_file.split("/")[-1].replace(".py", "")
        matched_test = None
        for t_file in test_files:
            if base_name in t_file:
                matched_test = t_file
                break

        paired_files[c_file] = matched_test
        if matched_test is None:
            uncovered_files.append(c_file)

    test_presence_score = 1.0 if not code_files else (len(code_files) - len(uncovered_files)) / len(code_files)

    return {
        "code_files_count": len(code_files),
        "test_files_count": len(test_files),
        "uncovered_files": uncovered_files,
        "paired_files": paired_files,
        "test_presence_score": round(test_presence_score, 2),
        "has_tests": len(test_files) > 0 or len(code_files) == 0,
    }


def evaluate_test_adequacy(
    code_snippets: Dict[str, str],
    test_snippets: Dict[str, str]
) -> List[Dict[str, Any]]:
    """
    Cross-references newly defined functions in implementation files with assertions
    and test call patterns in test files. Flags functions that have 0 corresponding assertions.
    """
    findings: List[Dict[str, Any]] = []

    functions_to_test: List[tuple[str, str, int]] = []
    for f_path, code in code_snippets.items():
        if _is_test(f_path) or not f_path.endswith(".py"):
            continue
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not node.name.startswith("_"):
                        functions_to_test.append((f_path, node.name, node.lineno))
        except SyntaxError:
            pass

    combined_test_code = "\n".join(test_snippets.values())
    has_asserts = "assert" in combined_test_code

    for f_path, func_name, line_no in functions_to_test:
        func_tested = func_name in combined_test_code
        if not func_tested or not has_asserts:
            findings.append({
                "file_path": f_path,
                "line_number": line_no,
                "severity": "HIGH",
                "category": "Test Coverage Gap",
                "rule_id": "COV-001",
                "description": f"Public function '{func_name}' has no identifiable unit test assertions.",
                "suggestion": f"Add a unit test in tests/ verifying '{func_name}' for standard and edge cases.",
            })

    if functions_to_test and not test_snippets:
        findings.append({
            "file_path": functions_to_test[0][0],
            "line_number": 1,
            "severity": "HIGH",
            "category": "Missing Test Suite",
            "rule_id": "COV-002",
            "description": "Diff introduces new logic but includes zero test files in the changeset.",
            "suggestion": "Include test files accompanying code changes before requesting merge.",
        })

    return findings


def _is_test(path: str) -> bool:
    lower = path.lower()
    return "test" in lower or lower.endswith("_test.py") or "tests/" in lower
