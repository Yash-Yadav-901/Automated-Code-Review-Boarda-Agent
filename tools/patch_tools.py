import difflib
from typing import Any, Dict, Optional


def extract_code_context(
    file_content: str,
    target_line: Optional[int],
    window: int = 4
) -> Dict[str, Any]:
    """
    Locates the target line within the file content and extracts surrounding
    context lines to facilitate accurate patch synthesis.
    """
    lines = file_content.splitlines()
    if not lines:
        return {
            "target_line": target_line,
            "snippet": "",
            "start_line": 1,
            "end_line": 1,
        }

    line_num = target_line if (target_line and 1 <= target_line <= len(lines)) else 1
    start_idx = max(0, line_num - window - 1)
    end_idx = min(len(lines), line_num + window)

    snippet_lines = lines[start_idx:end_idx]

    return {
        "target_line": line_num,
        "start_line": start_idx + 1,
        "end_line": end_idx,
        "snippet": "\n".join(snippet_lines),
        "total_lines": len(lines),
    }


def generate_unified_patch(
    file_path: str,
    original_code: str,
    replacement_code: str
) -> str:
    """
    Constructs a syntactically valid unified diff patch that can be applied
    directly via `git apply`.
    """
    orig_lines = original_code.splitlines(keepends=True)
    repl_lines = replacement_code.splitlines(keepends=True)

    if orig_lines and not orig_lines[-1].endswith("\n"):
        orig_lines[-1] += "\n"
    if repl_lines and not repl_lines[-1].endswith("\n"):
        repl_lines[-1] += "\n"

    diff_lines = list(
        difflib.unified_diff(
            orig_lines,
            repl_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm="\n",
        )
    )

    if not diff_lines:
        return f"# No visual differences between original and replacement for {file_path}"

    return "".join(diff_lines)
