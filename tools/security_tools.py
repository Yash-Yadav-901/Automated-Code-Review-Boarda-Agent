import ast
import re
from typing import Any, Dict, List

SECRET_PATTERNS = [
    (r"(?i)aws_secret_access_key\s*=\s*['\"][A-Za-z0-9/+=]{16,}['\"]", "AWS Secret Access Key", "SEC-001"),
    (r"(?i)AKIA[0-9A-Z]{16}", "AWS Access Key ID", "SEC-002"),
    (r"(?i)(api[_-]?key|secret[_-]?key|auth[_-]?token)\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"]", "Hardcoded API/Auth Token", "SEC-003"),
    (r"(?i)password\s*=\s*['\"][^'\"]{6,}['\"]", "Hardcoded Plaintext Password", "SEC-004"),
    (r"-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----", "Hardcoded Private Key Header", "SEC-005"),
]


def scan_secrets_and_credentials(diff_text: str) -> List[Dict[str, Any]]:
    """
    Scans additions and diff context for committed credentials, AWS keys,
    API tokens, and private keys using regular expression patterns.
    """
    findings: List[Dict[str, Any]] = []
    lines = diff_text.splitlines()

    for idx, line in enumerate(lines, start=1):
        clean_line = line.lstrip("+- ").strip()
        for pattern, name, rule_id in SECRET_PATTERNS:
            if re.search(pattern, clean_line):
                findings.append({
                    "file_path": "diff_stream",
                    "line_number": idx,
                    "severity": "CRITICAL",
                    "category": "Hardcoded Credential",
                    "rule_id": rule_id,
                    "description": f"Exposed secret detected: {name} found in code change.",
                    "suggestion": "Remove secret immediately, rotate the credential, and load secrets from environment variables or a vault.",
                })
    return findings


def audit_code_vulnerabilities(code_snippets: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Analyzes Python AST for security vulnerabilities:
    SQL injection, dynamic eval/exec, insecure subprocess with shell=True, and pickle.loads.
    """
    findings: List[Dict[str, Any]] = []

    for file_path, code in code_snippets.items():
        if not file_path.endswith(".py") or not code.strip():
            continue

        try:
            tree = ast.parse(code)
            tainted_sql_vars = set()

            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    is_sql_formatted = False
                    if isinstance(node.value, ast.JoinedStr):
                        for part in node.value.values:
                            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                                if re.search(r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)\b", part.value, re.IGNORECASE):
                                    is_sql_formatted = True
                                    break
                    elif isinstance(node.value, ast.BinOp) and isinstance(node.value.op, ast.Add):
                        for sub in (node.value.left, node.value.right):
                            if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                                if re.search(r"\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)\b", sub.value, re.IGNORECASE):
                                    is_sql_formatted = True
                                    break

                    if is_sql_formatted:
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                tainted_sql_vars.add(target.id)
                        findings.append({
                            "file_path": file_path,
                            "line_number": node.lineno,
                            "severity": "CRITICAL",
                            "category": "SQL Injection",
                            "rule_id": "SEC-013",
                            "description": "SQL statement dynamically constructed using formatted f-string or concatenation.",
                            "suggestion": "Use parameterized queries with placeholder substitution (e.g., 'WHERE id = ?', (user_id,)).",
                        })

                if isinstance(node, ast.Call):
                    func_name = ""
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        func_name = node.func.attr

                    if func_name in ("eval", "exec"):
                        findings.append({
                            "file_path": file_path,
                            "line_number": node.lineno,
                            "severity": "CRITICAL",
                            "category": "Dynamic Code Execution",
                            "rule_id": "SEC-010",
                            "description": f"Dangerous call to '{func_name}()' allows arbitrary remote code execution.",
                            "suggestion": "Replace dynamic code execution with structured parsing or safe data dispatch.",
                        })

                    if func_name in ("system", "popen", "run", "Popen"):
                        for kw in node.keywords:
                            if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                                findings.append({
                                    "file_path": file_path,
                                    "line_number": node.lineno,
                                    "severity": "CRITICAL",
                                    "category": "Command Injection",
                                    "rule_id": "SEC-011",
                                    "description": "Subprocess execution with 'shell=True' vulnerable to OS command injection.",
                                    "suggestion": "Set shell=False and pass arguments as an explicit list.",
                                })

                    if func_name in ("loads", "load"):
                        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                            if node.func.value.id == "pickle":
                                findings.append({
                                    "file_path": file_path,
                                    "line_number": node.lineno,
                                    "severity": "HIGH",
                                    "category": "Insecure Deserialization",
                                    "rule_id": "SEC-012",
                                    "description": "Usage of pickle.loads() on untrusted data can lead to arbitrary code execution.",
                                    "suggestion": "Use safe serialization formats like JSON, Protocol Buffers, or msgpack.",
                                })

                    if func_name in ("execute", "executemany", "raw"):
                        if node.args:
                            first_arg = node.args[0]
                            is_tainted_arg = False
                            if isinstance(first_arg, ast.Name) and first_arg.id in tainted_sql_vars:
                                is_tainted_arg = True
                            elif isinstance(first_arg, ast.JoinedStr):
                                is_tainted_arg = True

                            if is_tainted_arg:
                                findings.append({
                                    "file_path": file_path,
                                    "line_number": node.lineno,
                                    "severity": "CRITICAL",
                                    "category": "SQL Injection Execution",
                                    "rule_id": "SEC-014",
                                    "description": f"Database execute() called with dynamic/unparameterized query.",
                                    "suggestion": "Pass query parameters as a tuple/dictionary argument to execute().",
                                })

        except SyntaxError:
            # Fallback regex scanning when AST parsing fails
            lines = code.splitlines()
            for idx, line in enumerate(lines, start=1):
                if re.search(r"\bexecute\s*\(\s*f['\"].*SELECT|INSERT|UPDATE|DELETE", line, re.IGNORECASE):
                    findings.append({
                        "file_path": file_path,
                        "line_number": idx,
                        "severity": "CRITICAL",
                        "category": "SQL Injection (Heuristic)",
                        "rule_id": "SEC-013",
                        "description": "Probable SQL injection via formatted query string detected by regex fallback.",
                        "suggestion": "Refactor to parameterized SQL query.",
                    })

    return findings
