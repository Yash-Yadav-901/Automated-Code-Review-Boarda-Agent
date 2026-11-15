# LOVELY PROFESSIONAL UNIVERSITY
## School of Computer Science and Engineering
### Academic Task 2 (Project 2) — Course Code: CSE476
### Course Title: AGENTIC AI AND INTELLIGENT AUTOMATION
**Course Instructor:** Rohit Bharti  
**Mapped Course Outcomes:** CO3, CO4 | **Bloom's Levels:** L4, L5, L6 | **Maximum Marks:** 30  

---

# COMPREHENSIVE PROJECT REPORT
## Group 14: AUTOMATED CODE REVIEW BOARD
### A Production-Ready Multi-Agent System for Autonomous Code Review, Security Auditing, Test Coverage Verification, and Patch Synthesis

---

## 1. Executive Summary

Modern enterprise software engineering environments rely heavily on asynchronous pull request (PR) reviews to safeguard code quality, prevent vulnerabilities, and maintain software reliability. However, human code review represents one of the most prominent bottlenecks in agile pipelines, frequently resulting in prolonged cycle times, inconsistent adherence to standards, and undetected security vulnerabilities.

This project designs, constructs, and evaluates the **Automated Code Review Board**, a production-grade multi-agent system built on **Microsoft Semantic Kernel** and powered by Groq's high-speed **`openai/gpt-oss-120b`** language model lane. Operating under a **Fan-Out / Fan-In with Reviewer Manager** coordination architecture, the system coordinates six distinct single-responsibility agents reading from and updating a centralized, shared `ChangeState` memory structure:

1. **Diff Agent** (`diff_agent.py`): Ingests unified git diffs, isolates modified file hunks, and computes churn metrics.
2. **Style Agent** (`style_agent.py`): Enforces PEP 8 compliance, docstring completeness, and cyclomatic complexity limits.
3. **Security Agent** (`security_agent.py`): Audits code changes for leaked credentials (e.g., AWS tokens) and critical AST vulnerabilities (e.g., SQL injections, `eval()`, command injection).
4. **Test-Coverage Agent** (`test_coverage_agent.py`): Assesses test file presence and evaluates unit test adequacy for modified public functions.
5. **Reviewer Manager** (`reviewer_manager.py`): Aggregates findings, deduplicates redundant signals, sorts findings by strict severity hierarchy (`CRITICAL` $\rightarrow$ `INFO`), and issues an enforceable merge verdict (`approve` or `request-changes`).
6. **Fix-Suggestion Agent** (`fix_suggestion_agent.py` — *Group-of-3 Add-on*): Pinpoints the single highest-severity defect and autonomously synthesizes a ready-to-apply unified git patch.

The system was evaluated against three real-world pull request scenarios. It demonstrated a 100% test pass rate, robust graceful recovery from malformed syntax (honest failure handling), and fully traceable audit logging in an append-only JSONL event stream.

---

## 2. Project Objectives & Scope

### 2.1 Academic Alignment
* **CO3:** Design and implement coordinated multi-agent workflows using structured orchestration frameworks.
* **CO4:** Integrate domain-specific computational tools, shared memory models, and grounded intelligence into autonomous software engineering agents.
* **Bloom's Taxonomy:** **L4 (Analyzing)** code churn and security threat vectors, **L5 (Evaluating)** pull request quality gates and merge readiness, and **L6 (Creating)** autonomous patch repairs and multi-agent coordination topologies.

### 2.2 Functional Scope
* Accept raw unified git diffs or patch streams.
* Execute parallel, decoupled static analysis across style, security, and test dimensions.
* Maintain a single source of truth (`ChangeState`) with strict typed severity scoring.
* Enforce automated enterprise governance gates (zero tolerance for `CRITICAL` and `HIGH` security/test defects).
* Produce human-readable executive reviews accompanied by concrete git diff repair patches.
* Maintain an append-only, tamper-evident audit trail for full enterprise compliance.

---

## 3. System Architecture & Coordination Architecture

### 3.1 Coordination Pattern: Fan-Out / Fan-In with Reviewer Manager
The project employs a hybrid pipeline and fan-out/fan-in topology:

```
[Submitted Code Change / Git Diff]
              │
              ▼
       ┌──────────────┐
       │  Diff Agent  │ (Ingestion, Hunk Splitting, Metric Computation)
       └──────┬───────┘
              │ (Populates initial state)
              ▼
   ┌────────────────────────────────────────────────────────┐
   │                  Shared ChangeState                    │
   │   (Touched Files, AST Trees, Append-Only Findings)     │
   └──────┬───────────────────┬───────────────────┬─────────┘
          │                   │                   │
   [FAN-OUT PARALLEL EXECUTION VIA asyncio.gather()]
          │                   │                   │
          ▼                   ▼                   ▼
   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
   │ Style Agent  │    │Security Agent│    │Test-Coverage │
   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘
          │                   │                   │
   [FAN-IN COLLECTION BACK TO SHARED STATE]
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                   ┌──────────────────────┐
                   │   Reviewer Manager   │
                   │(Deduplicate & Rank)  │
                   └──────────┬───────────┘
                              │
             ┌────────────────┴────────────────┐
             ▼                                 ▼
      [Verdict: APPROVE]             [Verdict: REQUEST-CHANGES]
             │                                 │
             ▼                                 ▼
      [Clean Note Logged]             ┌──────────────────────┐
                                      │ Fix-Suggestion Agent │
                                      │ (Group-of-3 Add-on)  │
                                      └──────────┬───────────┘
                                                 │
                                                 ▼
                                      [Unified Diff Patch]
```

### 3.2 Why This Architecture Fits
1. **Separation of Concerns:** Diff parsing, style auditing, security vulnerability scanning, and coverage analysis are independent tasks. A single agent handling all dimensions suffers from context pollution and high latency.
2. **Parallel Performance:** Through `asyncio.gather()`, the Style, Security, and Coverage agents execute concurrently, slashing overall wall-clock evaluation time.
3. **Centralized Adjudication:** The Reviewer Manager acts as an impartial gatekeeper, preventing any single specialized agent from having unchecked authority over the merge decision.

---

## 4. Multi-Agent Roster & Plain Python Tools

In strict accordance with project rules, **each agent is implemented in an independent Python module** and calls **at least two real tools written as plain Python functions**:

### Summary Table of Agents and Tools

| Agent Name | Module File | Core Role | Plain Python Tool 1 | Plain Python Tool 2 |
| :--- | :--- | :--- | :--- | :--- |
| **Diff Agent** | `agents/diff_agent.py` | Ingests diff, extracts hunks, computes churn. | `parse_unified_diff(raw_diff)` | `compute_diff_metrics(files)` |
| **Style Agent** | `agents/style_agent.py` | Enforces PEP 8, docstrings, and complexity. | `check_pep8_and_docstrings(code_snippets)` | `calculate_cyclomatic_complexity(code_snippets)` |
| **Security Agent** | `agents/security_agent.py` | Scans for leaked keys, SQLi, and unsafe calls. | `scan_secrets_and_credentials(diff_text)` | `audit_code_vulnerabilities(code_snippets)` |
| **Test-Coverage Agent** | `agents/test_coverage_agent.py` | Validates test suite existence and public API assertions. | `detect_test_file_presence(modified_files)` | `evaluate_test_adequacy(code, tests)` |
| **Reviewer Manager** | `agents/reviewer_manager.py` | Deduplicates findings, ranks by severity, issues verdict. | `deduplicate_and_rank_findings(findings)` | `compute_merge_verdict(severity_counts)` |
| **Fix-Suggestion Agent** | `agents/fix_suggestion_agent.py` | *Group-of-3 Add-on:* Synthesizes patch for top finding. | `extract_code_context(file_content, target_line)` | `generate_unified_patch(path, orig, fix)` |

---

## 5. Shared Memory Model (`ChangeState`)

Rather than passing untyped messages, all agents interact via a strongly-typed shared memory object built using Pydantic:

* **State Model Fields:**
  * `diff_id` (`str`): Unique tracking identifier for the pull request.
  * `raw_diff` (`str`): The raw incoming git diff payload.
  * `files` (`List[TouchedFile]`): Parsed file records with addition/deletion counts and isolated added code.
  * `summary` (`str`): High-level executive description produced by the Diff Agent.
  * `findings` (`List[Finding]`): Central blackboard where review specialists append identified issues.
  * `merge_verdict` (`str`): Definitive decision: `"approve"` or `"request-changes"`.
  * `verdict_rationale` (`str`): Reviewer Manager's executive justification.
  * `priority_findings` (`List[Finding]`): Deduplicated findings strictly sorted by severity.
  * `suggested_patch` (`str`): Concrete unified diff synthesized by the Fix-Suggestion Agent.
  * `warnings` (`List[str]`): Handled failures and system recovery events.
  * `execution_trace` (`List[Dict]`): Chronological record of internal agent steps.

* **Severity Hierarchy:**
  $$\text{CRITICAL (Rank 1)} \succ \text{HIGH (Rank 2)} \succ \text{MEDIUM (Rank 3)} \succ \text{LOW (Rank 4)} \succ \text{INFO (Rank 5)}$$

---

## 6. Honest Failure Handled

### 6.1 Description of Failure
In production pipelines, pull requests often contain truncated diffs, unparseable code snippets, syntax errors, or non-Python files. If an agent naively calls Python's `ast.parse()`, an unhandled `SyntaxError` will immediately crash the entire review pipeline.

### 6.2 Implementation of Failure Recovery
1. Both `tools/style_tools.py` and `tools/security_tools.py` wrap AST generation inside structured exception boundaries.
2. When a `SyntaxError` occurs:
   * The exception is caught cleanly.
   * An explicit diagnostic finding is added:
     `STY-ERR-001 (HIGH): Failed to parse AST due to SyntaxError: ... Fallback token scanning applied.`
   * The agent automatically degrades to a **lexical regex token scanner**, scanning lines for dangerous patterns without requiring a complete syntax tree.
   * The event is recorded in `state.warnings` and logged to the append-only audit trail.
3. The Reviewer Manager flags this degradation in its final report, preventing crashes while alerting human reviewers to defective code.

---

## 7. Empirical Test Scenarios & Results

The system was evaluated using automated integration tests in `tests/test_scenarios.py`:

### Scenario 1: Clean & Compliant Pull Request
* **Input:** New mathematical utility function with full docstrings, PEP 8 compliance, and an accompanying unit test file (`test_math_utils.py`) with assertions.
* **Findings:** 0 Critical, 0 High, 0 Medium findings.
* **Merge Verdict:** `APPROVE`
* **Result:** **PASSED**

### Scenario 2: Severe Security Vulnerabilities & Credential Leak
* **Input:** Code containing an exposed AWS Secret Key (`AKIAIOSFODNN7EXAMPLE...`) and a raw SQL query formatted via f-strings (`f"SELECT ... WHERE id = '{user_id}'"`).
* **Findings:** 2 `CRITICAL` findings (Hardcoded Credential, SQL Injection).
* **Merge Verdict:** `REQUEST-CHANGES`
* **Fix-Suggestion Output:** Concrete unified patch replacing raw SQL with parameterized queries.
* **Result:** **PASSED**

### Scenario 3: Missing Tests, High Complexity & Honest Failure
* **Input:** Code with deeply nested branching logic (McCabe complexity > 8), zero test files, and an unparseable syntax error (`if defective syntax line here (broken indentation`).
* **Findings:** `HIGH` (Missing Unit Tests), `MEDIUM` (Code Complexity), `HIGH` (Syntax Parsing Handled).
* **Merge Verdict:** `REQUEST-CHANGES`
* **Result:** **PASSED**

```
============================= test session starts =============================
platform win32 -- Python 3.13.2, pytest-9.2.0, pluggy-1.7.0
rootdir: D:\2.0 pictures\Automated Code Review Board Agent
collected 3 items

tests/test_scenarios.py::test_scenario_1_clean_change PASSED             [ 33%]
tests/test_scenarios.py::test_scenario_2_security_vulnerabilities PASSED [ 66%]
tests/test_scenarios.py::test_scenario_3_complexity_and_honest_failure PASSED [100%]

======================== 3 passed, 1 warning in 27.81s ========================
```

---

## 8. Append-Only Audit Run Log

The system maintains an append-only JSON Lines log in `logs/audit_run_log.jsonl`. Every event is immutably recorded with:
* Universal UTC Timestamp (`ISO 8601`)
* Event Type (`WORKFLOW_START`, `TOOL_CALL`, `AGENT_COMPLETE`, `DECISION`, `WORKFLOW_COMPLETE`)
* Agent Name and Target `diff_id`
* Detailed data payload (inputs, tool parameters, detected findings, verdicts)

---

## 9. Conclusion

The **Automated Code Review Board** demonstrates how agentic AI and multi-agent coordination architectures can automate complex, multi-faceted enterprise workflows. By decoupling concerns into specialized agents, enforcing deterministic governance gates, handling unexpected failures honestly, and providing automated patch remediation, the system eliminates code review bottlenecks while significantly enhancing software security and test coverage standards.
