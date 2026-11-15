import uuid
from typing import Dict, Any, List
from core.change_state import ChangeState, Finding, Severity
from core.run_log import audit_logger
from core.config import create_sk_kernel
from tools.coverage_tools import detect_test_file_presence, evaluate_test_adequacy
from semantic_kernel.contents import ChatHistory


class TestCoverageAgent:
    """
    Agent 4: Test-Coverage Agent (Separate Module)
    Role: Verifies whether code changes are backed by corresponding unit tests,
    ensures test coverage presence, and detects untested public function definitions.
    Calls 2 real Python tools:
      1. detect_test_file_presence
      2. evaluate_test_adequacy
    """
    def __init__(self, agent_name: str = "TestCoverageAgent"):
        self.name = agent_name
        self.kernel, self.settings = create_sk_kernel(service_id=f"{self.name}_service")

    async def run(self, state: ChangeState) -> ChangeState:
        all_paths = [f.path for f in state.files]
        modified_code_files = [f.path for f in state.files if not f.is_test_file and f.path.endswith(".py")]

        if not modified_code_files:
            state.log_event(self.name, "skipped", {"reason": "No non-test Python files to verify coverage for."})
            return state

        # Tool Call 1: Check presence of accompanying test files
        presence_res = detect_test_file_presence(
            modified_files=modified_code_files,
            all_diff_files=all_paths
        )
        audit_logger.append_entry(
            event_type="TOOL_CALL",
            diff_id=state.diff_id,
            agent_name=self.name,
            data={"tool": "detect_test_file_presence", "presence_score": presence_res.get("test_presence_score")}
        )

        # Prepare code vs test snippets
        code_snippets: Dict[str, str] = {
            f.path: f.added_code
            for f in state.files
            if not f.is_test_file and f.added_code.strip() and f.path.endswith(".py")
        }
        test_snippets: Dict[str, str] = {
            f.path: f.added_code
            for f in state.files
            if f.is_test_file and f.added_code.strip() and f.path.endswith(".py")
        }

        # Tool Call 2: Evaluate test adequacy for newly added public functions
        adequacy_findings = evaluate_test_adequacy(code_snippets, test_snippets)
        audit_logger.append_entry(
            event_type="TOOL_CALL",
            diff_id=state.diff_id,
            agent_name=self.name,
            data={"tool": "evaluate_test_adequacy", "adequacy_gaps": len(adequacy_findings)}
        )

        # If completely missing tests for code files, record a high-severity finding
        if presence_res.get("uncovered_files") and not presence_res.get("has_tests"):
            for unc_file in presence_res["uncovered_files"]:
                state.add_finding(
                    Finding(
                        id=f"COV-{uuid.uuid4().hex[:6]}",
                        agent=self.name,
                        file_path=unc_file,
                        line_number=1,
                        severity=Severity.HIGH,
                        category="Missing Unit Tests",
                        rule_id="COV-001",
                        description=f"File '{unc_file}' modified without any accompanying unit test suite in changeset.",
                        suggestion=f"Provide unit tests in tests/test_{unc_file.split('/')[-1]} to validate logic.",
                    )
                )

        # Append adequacy gaps
        for item in adequacy_findings:
            state.add_finding(
                Finding(
                    id=f"COV-{uuid.uuid4().hex[:6]}",
                    agent=self.name,
                    file_path=item["file_path"],
                    line_number=item.get("line_number"),
                    severity=Severity(item["severity"]),
                    category=item["category"],
                    rule_id=item["rule_id"],
                    description=item["description"],
                    suggestion=item.get("suggestion"),
                )
            )

        # Semantic Kernel LLM reasoning on coverage posture
        total_cov_issues = len(presence_res.get("uncovered_files", [])) + len(adequacy_findings)
        if total_cov_issues > 0:
            prompt = (
                f"You are the Test-Coverage Agent on a Code Review Board.\n"
                f"The diff modifies {len(modified_code_files)} code file(s) with {total_cov_issues} test coverage gaps.\n"
                f"Write a 1-sentence prompt to the author on what tests are required before merge."
            )
            try:
                chat_service = self.kernel.get_service(type=None)
                history = ChatHistory()
                history.add_user_message(prompt)
                response = await chat_service.get_chat_message_content(history, self.settings)
                state.log_event(self.name, "coverage_advice", {"advice": str(response.content).strip()})
            except Exception as e:
                state.warnings.append(f"TestCoverageAgent advice skipped: {str(e)}")

        state.log_event(self.name, "coverage_check_complete", {
            "uncovered_files": presence_res.get("uncovered_files", []),
            "adequacy_gaps": len(adequacy_findings),
        })
        audit_logger.append_entry(
            event_type="AGENT_COMPLETE",
            diff_id=state.diff_id,
            agent_name=self.name,
            data={"coverage_gaps": total_cov_issues}
        )
        return state
