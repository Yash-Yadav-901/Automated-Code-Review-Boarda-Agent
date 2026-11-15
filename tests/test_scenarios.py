import pytest
from core.orchestrator import CodeReviewOrchestrator
from core.change_state import Severity
from tests.sample_diffs import CLEAN_DIFF, SECURITY_VULN_DIFF, COMPLEXITY_AND_MISSING_TESTS_DIFF


@pytest.mark.asyncio
async def test_scenario_1_clean_change():
    """Validates approval for clean, well-documented and tested code."""
    orchestrator = CodeReviewOrchestrator()
    state = await orchestrator.review_code_change(
        raw_diff=CLEAN_DIFF,
        diff_id="TEST-SCENARIO-1-CLEAN"
    )

    assert state.merge_verdict == "approve", f"Expected approve but got {state.merge_verdict}"
    assert len(state.files) == 2
    critical_or_high = [
        f for f in state.priority_findings
        if f.severity in (Severity.CRITICAL, Severity.HIGH)
    ]
    assert len(critical_or_high) == 0
    assert state.verdict_rationale is not None


@pytest.mark.asyncio
async def test_scenario_2_security_vulnerabilities():
    """Validates request-changes and patch synthesis for security vulnerabilities."""
    orchestrator = CodeReviewOrchestrator()
    state = await orchestrator.review_code_change(
        raw_diff=SECURITY_VULN_DIFF,
        diff_id="TEST-SCENARIO-2-SECURITY"
    )

    assert state.merge_verdict == "request-changes", f"Expected request-changes but got {state.merge_verdict}"
    critical_findings = [
        f for f in state.priority_findings
        if f.severity == Severity.CRITICAL
    ]
    assert len(critical_findings) >= 1
    assert state.suggested_patch is not None
    assert len(state.suggested_patch.strip()) > 0
    assert state.patch_target_finding_id is not None


@pytest.mark.asyncio
async def test_scenario_3_complexity_and_honest_failure():
    """Validates test coverage gating and honest failure recovery on malformed syntax."""
    orchestrator = CodeReviewOrchestrator()
    state = await orchestrator.review_code_change(
        raw_diff=COMPLEXITY_AND_MISSING_TESTS_DIFF,
        diff_id="TEST-SCENARIO-3-FAILURE-HANDLING"
    )

    assert state.merge_verdict == "request-changes"
    coverage_issues = [
        f for f in state.priority_findings
        if "COV" in f.rule_id or "Test" in f.category
    ]
    assert len(coverage_issues) >= 1
    syntax_issues = [
        f for f in state.priority_findings
        if "Syntax" in f.category or "ERR" in f.rule_id
    ]
    assert len(syntax_issues) >= 1
