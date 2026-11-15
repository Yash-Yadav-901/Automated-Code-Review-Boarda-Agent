import ast
import re
from typing import Any, Dict, List


SECRET_PATTERNS = [
    (r"(?i)aws_secret_access_key\s*=\s*['\"][A-Za-z0-9/+=]{30,}['\"]", "AWS Secret Access Key", "SEC-001"),
    (r"(?i)AKIA[0-9A-Z]{16}", "AWS Access Key ID", "SEC-002"),
    (r"(?i)(api[_-]?key|secret[_-]?key|auth[_-]?token)\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"]", "Hardcoded API/Auth Token", "SEC-003"),
    (r"(?i)password\s*=\s*['\"][^'\"]{6,}['\"]", "Hardcoded Plaintext Password", "SEC-004"),
    (r"-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----", "Hardcoded Private Key Header", "SEC-005"),
]


def scan_secrets_and_credentials(diff_text: str) -> List[Dict[str, Any]]:
    """
    Real Tool 1 (Security Agent):
    Scans additions in the diff for committed credentials, AWS secret keys,
    API keys, authorization tokens, and private keys using regular expression patterns.
    """
    findings: List[Dict[str, Any]] = []
    lines = diff_text.splitlines()

    for idx, line in enumerate(lines, start=1):
        # Focus on added code in diff
        if line.startswith("+") and not line.startswith("+++"):
            code_line = line[1:].strip()
            for pattern, name, rule_id in SECRET_PATTERNS:
                if re.search(pattern, code_line):
                    findings.append({
                        "file_path": "diff_stream",
                        "line_number": idx,
                        "severity": "CRITICAL",
                        "category": "Hardcoded Credential",
                        "rule_id": rule_id,
                        "description": f"Exposed secret detected: {name} committed directly in code change.",
                        "suggestion": "Remove secret immediately, rotate the credential, and use environment variables.",
                    })
    return findings


def audit_code_vulnerabilities(code_snippets: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Real Tool 2 (Security Agent):
    Analyzes Python AST and patterns for dangerous security anti-patterns:
    - SQL injection via raw string formatting or concatenation
    - Unsafe evaluation via eval() or exec()
    - Insecure subprocess execution with shell=True
    - Insecure deserialization via pickle.loads()
    """
    findings: List[Dict[str, Any]] = []

    for file_path, code in code_snippets.items():
        if not file_path.endswith(".py") or not code.strip():
            continue

        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                # 1. Detect eval() or exec()
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

                    # 2. Insecure subprocess shell=True
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

                    # 3. Insecure deserialization (pickle.loads)
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

                    # 4. Raw SQL queries formatted with f-strings or concatenation
                    if func_name in ("execute", "executemany", "raw"):
                        if node.args:
                            first_arg = node.args[0]
                            # Detect f-string query
                            if isinstance(first_arg, ast.JoinedStr):
                                findings.append({
                                    "file_path": file_path,
                                    "line_number": node.lineno,
                                    "severity": "CRITICAL",
                                    "category": "SQL Injection",
                                    "rule_id": "SEC-013",
                                    "description": "SQL query built via formatted string (f-string) in execute() statement.",
                                    "suggestion": "Use parameterized queries with placeholders (? or %s) to eliminate SQL injection.",
                                })
                            # Detect concatenation (+)
                            elif isinstance(first_arg, ast.BinOp) and isinstance(first_arg.op, ast.Add):
                                findings.append({
                                    "file_path": file_path,
                                    "line_number": node.lineno,
                                    "severity": "CRITICAL",
                                    "category": "SQL Injection",
                                    "rule_id": "SEC-014",
                                    "description": "SQL query built via string concatenation (+) in execute() statement.",
                                    "suggestion": "Use parameterized queries with query parameters passed as a tuple/dict.",
                                })

        except SyntaxError:
            # Fallback regex scanning if AST fails
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
