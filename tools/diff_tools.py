import re
from typing import Any, Dict, List


def parse_unified_diff(raw_diff: str) -> Dict[str, Any]:
    """
    Real Tool 1 (Diff Agent):
    Parses a raw unified git diff into structured file entries, identifying
    touched paths, change modes, added/deleted line counts, and separated code blocks.
    Handles malformed or empty diffs gracefully.
    """
    if not raw_diff or not raw_diff.strip():
        return {
            "success": False,
            "error": "Empty or whitespace-only diff provided.",
            "files": [],
            "total_additions": 0,
            "total_deletions": 0,
        }

    file_chunks = re.split(r"^diff --git ", raw_diff, flags=re.MULTILINE)
    parsed_files: List[Dict[str, Any]] = []
    total_additions = 0
    total_deletions = 0

    for chunk in file_chunks:
        if not chunk.strip():
            continue

        lines = chunk.splitlines()
        header = lines[0]
        # Match "a/path b/path"
        paths = header.split(" ")
        file_path = "unknown"
        if len(paths) >= 2:
            file_path = paths[1].removeprefix("b/")

        added_lines: List[str] = []
        deleted_lines: List[str] = []
        add_count = 0
        del_count = 0

        in_hunk = False
        for line in lines[1:]:
            if line.startswith("@@"):
                in_hunk = True
                continue
            if in_hunk:
                if line.startswith("+") and not line.startswith("+++"):
                    add_count += 1
                    added_lines.append(line[1:])
                elif line.startswith("-") and not line.startswith("---"):
                    del_count += 1
                    deleted_lines.append(line[1:])

        total_additions += add_count
        total_deletions += del_count

        is_test = bool(
            "test" in file_path.lower()
            or file_path.endswith("_test.py")
            or "tests/" in file_path.lower()
        )

        parsed_files.append({
            "path": file_path,
            "change_type": "modified" if del_count > 0 and add_count > 0 else ("added" if add_count > 0 else "deleted"),
            "additions": add_count,
            "deletions": del_count,
            "added_code": "\n".join(added_lines),
            "deleted_code": "\n".join(deleted_lines),
            "is_test_file": is_test,
        })

    return {
        "success": True,
        "files": parsed_files,
        "total_additions": total_additions,
        "total_deletions": total_deletions,
    }


def compute_diff_metrics(files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Real Tool 2 (Diff Agent):
    Computes engineering metrics across all modified files, such as churn ratio,
    file distribution by extension, and test-to-code modification ratio.
    """
    if not files:
        return {
            "total_files": 0,
            "net_churn": 0,
            "test_to_code_ratio": 0.0,
            "extensions": {},
            "risk_footprint": "LOW",
        }

    total_files = len(files)
    total_adds = sum(f.get("additions", 0) for f in files)
    total_dels = sum(f.get("deletions", 0) for f in files)
    net_churn = total_adds + total_dels

    test_files = [f for f in files if f.get("is_test_file", False)]
    impl_files = [f for f in files if not f.get("is_test_file", False)]

    test_adds = sum(f.get("additions", 0) for f in test_files)
    impl_adds = sum(f.get("additions", 0) for f in impl_files)

    ratio = (test_adds / max(1, impl_adds)) if impl_adds > 0 else (1.0 if test_adds > 0 else 0.0)

    extensions: Dict[str, int] = {}
    for f in files:
        ext = f.get("path", "").split(".")[-1] if "." in f.get("path", "") else "unknown"
        extensions[ext] = extensions.get(ext, 0) + 1

    # Footprint heuristic
    if net_churn > 300 or total_files > 10:
        risk_footprint = "HIGH"
    elif net_churn > 80 or total_files > 4:
        risk_footprint = "MEDIUM"
    else:
        risk_footprint = "LOW"

    return {
        "total_files": total_files,
        "total_additions": total_adds,
        "total_deletions": total_dels,
        "net_churn": net_churn,
        "test_to_code_ratio": round(ratio, 2),
        "extensions": extensions,
        "risk_footprint": risk_footprint,
    }
