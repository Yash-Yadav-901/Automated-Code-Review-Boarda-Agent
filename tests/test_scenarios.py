import pytest
import asyncio
from core.orchestrator import CodeReviewOrchestrator
from core.change_state import Severity
from tests.sample_diffs import CLEAN_DIFF, SECURITY_VULN_DIFF, COMPLEXITY_AND_MISSING_TESTS_DIFF


@pytest.mark.asyncio
async def test_scenario_1_clean_change():
    """
    Scenario 1: Clean code change.
    - Code is well-documented with docstrings
    - PEP 8 compliant, low cyclomatic complexity
    - Accompanied by unit test file with assertions
    - Expectation: Merge verdict is 'approve', zero blocking issues.
    """
    orchestrator = CodeReviewOrchestrator()
    state = await orchestrator.review_code_change(
        raw_diff=CLEAN_DIFF,
        diff_id="TEST-SCENARIO-1-CLEAN"
    )

    assert state.merge_verdict == "approve", f"Expected approve but got {state.merge_verdict}"
    assert len(state.files) == 2, "Expected 2 files parsed (source + test)"
    
    # Assert no blocking (CRITICAL or HIGH) findings
    critical_or_high = [
        f for f in state.priority_findings
        if f.severity in (Severity.CRITICAL, Severity.HIGH)
    ]
    assert len(critical_or_high) == 0, f"Found unexpected high severity findings: {critical_or_high}"
    assert state.verdict_rationale is not None


@pytest.mark.asyncio
async def test_scenario_2_security_vulnerabilities():
    """
    Scenario 2: Critical security vulnerabilities.
    - Diff contains an exposed AWS Secret Access Key
    - Diff contains a SQL Injection via string formatting
    - Expectation:
      * Verdict is 'request-changes'
      * CRITICAL findings are recorded
      * Group-of-3 add-on (FixSuggestionAgent) produces a concrete patch for the top finding
    """
    orchestrator = CodeReviewOrchestrator()
    state = await orchestrator.review_code_change(
        raw_diff=SECURITY_VULN_DIFF,
        diff_id="TEST-SCENARIO-2-SECURITY"
    )

    assert state.merge_verdict == "request-changes", f"Expected request-changes but got {state.merge_verdict}"
    
    # Assert presence of CRITICAL findings
    critical_findings = [
        f for f in state.priority_findings
        if f.severity == Severity.CRITICAL
    ]
    assert len(critical_findings) >= 1, "Expected at least 1 CRITICAL finding"
    
    # Assert Fix-Suggestion Agent synthesized a concrete patch
    assert state.suggested_patch is not None, "Expected FixSuggestionAgent to produce a suggested patch"
    assert len(state.suggested_patch.strip()) > 0
    assert state.patch_target_finding_id is not None


@pytest.mark.asyncio
async def test_scenario_3_complexity_and_honest_failure():
    """
    Scenario 3: Missing tests, high cyclomatic complexity, and honest failure recovery.
    - Deeply nested branching logic
    - Zero accompanying unit test files
    - Intentionally malformed syntax triggers AST SyntaxError
    - Expectation:
      * System does NOT crash (honest failure handled gracefully)
      * Warning / error recorded in state
      * Test coverage gap flagged
      * Verdict is 'request-changes'
    """
    orchestrator = CodeReviewOrchestrator()
    state = await orchestrator.review_code_change(
        raw_diff=COMPLEXITY_AND_MISSING_TESTS_DIFF,
        diff_id="TEST-SCENARIO-3-FAILURE-HANDLING"
    )

    assert state.merge_verdict == "request-changes"
    
    # Assert that missing tests were flagged
    coverage_issues = [
        f for f in state.priority_findings
        if "COV" in f.rule_id or "Test" in f.category
    ]
    assert len(coverage_issues) >= 1, "Expected at least 1 test coverage finding"
    
    # Assert honest failure handled: syntax error was caught and logged gracefully
    syntax_issues = [
        f for f in state.priority_findings
        if "Syntax" in f.category or "ERR" in f.rule_id
    ]
    assert len(syntax_issues) >= 1, "Expected AST syntax error to be recorded as a handled finding"
