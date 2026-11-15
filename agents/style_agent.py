import uuid
from typing import Dict, Any
from core.change_state import ChangeState, Finding, Severity
from core.run_log import audit_logger
from core.config import create_sk_kernel
from tools.style_tools import check_pep8_and_docstrings, calculate_cyclomatic_complexity
from semantic_kernel.contents import ChatHistory


class StyleAgent:
    """
    Agent 2: Style Agent (Separate Module)
    Reviews code additions for PEP 8 styling conventions, missing documentation,
    naming violations, and cyclomatic complexity limits.
    """
    def __init__(self, agent_name: str = "StyleAgent"):
        self.name = agent_name
        self.kernel, self.settings = create_sk_kernel(service_id=f"{self.name}_service")

    async def run(self, state: ChangeState) -> ChangeState:
        code_snippets: Dict[str, str] = {
            f.path: f.added_code
            for f in state.files
            if f.added_code.strip() and f.path.endswith(".py")
        }

        if not code_snippets:
            state.log_event(self.name, "skipped", {"reason": "No Python additions to check"})
            return state

        pep8_issues = check_pep8_and_docstrings(code_snippets)
        audit_logger.append_entry(
            event_type="TOOL_CALL",
            diff_id=state.diff_id,
            agent_name=self.name,
            data={"tool": "check_pep8_and_docstrings", "findings_found": len(pep8_issues)}
        )

        complexity_issues = calculate_cyclomatic_complexity(code_snippets, threshold=8)
        audit_logger.append_entry(
            event_type="TOOL_CALL",
            diff_id=state.diff_id,
            agent_name=self.name,
            data={"tool": "calculate_cyclomatic_complexity", "findings_found": len(complexity_issues)}
        )

        for item in pep8_issues + complexity_issues:
            severity_enum = Severity(item["severity"])
            state.add_finding(
                Finding(
                    id=f"STY-{uuid.uuid4().hex[:6]}",
                    agent=self.name,
                    file_path=item["file_path"],
                    line_number=item.get("line_number"),
                    severity=severity_enum,
                    category=item["category"],
                    rule_id=item["rule_id"],
                    description=item["description"],
                    suggestion=item.get("suggestion"),
                )
            )

        if pep8_issues or complexity_issues:
            issue_summary = "\n".join([f"- {i['rule_id']}: {i['description']}" for i in (pep8_issues + complexity_issues)[:5]])
            prompt = (
                f"You are the Style Agent on a Code Review Board.\n"
                f"We discovered the following style/complexity flags:\n{issue_summary}\n"
                f"Provide a 1-sentence developer feedback comment encouraging clean code standards."
            )
            try:
                chat_service = self.kernel.get_service(type=None)
                history = ChatHistory()
                history.add_user_message(prompt)
                response = await chat_service.get_chat_message_content(history, self.settings)
                state.log_event(self.name, "style_advice", {"advice": str(response.content).strip()})
            except Exception as e:
                state.warnings.append(f"StyleAgent advice skipped: {str(e)}")

        state.log_event(self.name, "analysis_complete", {
            "style_findings": len(pep8_issues),
            "complexity_findings": len(complexity_issues),
        })
        audit_logger.append_entry(
            event_type="AGENT_COMPLETE",
            diff_id=state.diff_id,
            agent_name=self.name,
            data={"total_findings_added": len(pep8_issues) + len(complexity_issues)}
        )
        return state
