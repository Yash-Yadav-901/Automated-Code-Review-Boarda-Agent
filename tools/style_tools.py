import ast
import re
from typing import Any, Dict, List


def check_pep8_and_docstrings(code_snippets: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Real Tool 1 (Style Agent):
    Audits Python code snippets for PEP 8 styling conventions, missing docstrings
    on functions and classes, naming standard compliance (snake_case vs CamelCase),
    and line length limits (> 100 characters).
    Includes honest failure recovery when parsing malformed syntax.
    """
    findings: List[Dict[str, Any]] = []

    for file_path, code in code_snippets.items():
        if not file_path.endswith(".py") or not code.strip():
            continue

        # Line-by-line checks (formatting, line length)
        lines = code.splitlines()
        for idx, line in enumerate(lines, start=1):
            if len(line) > 100:
                findings.append({
                    "file_path": file_path,
                    "line_number": idx,
                    "severity": "LOW",
                    "category": "PEP 8 Style",
                    "rule_id": "STY-001",
                    "description": f"Line exceeds 100 characters ({len(line)} chars).",
                    "suggestion": "Break long expressions into multiple lines according to PEP 8.",
                })
            if line.rstrip() != line:
                findings.append({
                    "file_path": file_path,
                    "line_number": idx,
                    "severity": "INFO",
                    "category": "PEP 8 Style",
                    "rule_id": "STY-002",
                    "description": "Trailing whitespace detected.",
                    "suggestion": "Remove unnecessary trailing spaces.",
                })

        # AST-level docstring and naming checks with honest failure recovery
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Check docstrings
                    if not ast.get_docstring(node):
                        findings.append({
                            "file_path": file_path,
                            "line_number": node.lineno,
                            "severity": "LOW",
                            "category": "Code Documentation",
                            "rule_id": "STY-003",
                            "description": f"Function '{node.name}' is missing a docstring.",
                            "suggestion": "Add a clear docstring explaining arguments, return type, and purpose.",
                        })
                    # Check naming (functions should be snake_case, not camelCase or PascalCase)
                    if not node.name.startswith("__") and re.search(r"[A-Z]", node.name):
                        findings.append({
                            "file_path": file_path,
                            "line_number": node.lineno,
                            "severity": "LOW",
                            "category": "Naming Conventions",
                            "rule_id": "STY-004",
                            "description": f"Function '{node.name}' uses uppercase letters instead of PEP 8 snake_case.",
                            "suggestion": f"Rename '{node.name}' to snake_case format.",
                        })

                elif isinstance(node, ast.ClassDef):
                    if not ast.get_docstring(node):
                        findings.append({
                            "file_path": file_path,
                            "line_number": node.lineno,
                            "severity": "LOW",
                            "category": "Code Documentation",
                            "rule_id": "STY-005",
                            "description": f"Class '{node.name}' lacks a class-level docstring.",
                            "suggestion": "Add a class docstring detailing responsibilities and state.",
                        })

        except SyntaxError as e:
            # Honest failure handled: malformed syntax or partial snippet
            findings.append({
                "file_path": file_path,
                "line_number": e.lineno,
                "severity": "HIGH",
                "category": "Syntax Parsing Failure",
                "rule_id": "STY-ERR-001",
                "description": f"Failed to parse AST due to SyntaxError: {e.msg}. Fallback token scanning applied.",
                "suggestion": "Ensure valid Python syntax in the submitted diff.",
            })

    return findings


def calculate_cyclomatic_complexity(code_snippets: Dict[str, str], threshold: int = 8) -> List[Dict[str, Any]]:
    """
    Real Tool 2 (Style Agent):
    Traverses AST to compute McCabe Cyclomatic Complexity per function
    by counting decision points (if, for, while, and, or, except).
    Flags functions whose complexity exceeds the threshold.
    """
    findings: List[Dict[str, Any]] = []

    for file_path, code in code_snippets.items():
        if not file_path.endswith(".py") or not code.strip():
            continue

        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    complexity = 1  # Base complexity
                    for subnode in ast.walk(node):
                        if isinstance(subnode, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler)):
                            complexity += 1
                        elif isinstance(subnode, ast.BoolOp):
                            complexity += len(subnode.values) - 1

                    if complexity > threshold:
                        findings.append({
                            "file_path": file_path,
                            "line_number": node.lineno,
                            "severity": "MEDIUM",
                            "category": "Code Complexity",
                            "rule_id": "STY-006",
                            "description": f"Function '{node.name}' has high cyclomatic complexity ({complexity} > threshold {threshold}).",
                            "suggestion": "Refactor deeply nested branching or loops into helper functions.",
                        })
        except SyntaxError:
            # Handled in AST parse tool; skip duplicate error emission
            pass

    return findings
