import uuid
from typing import Dict, Any
from core.change_state import ChangeState, Finding, Severity
from core.run_log import audit_logger
from core.config import create_sk_kernel
from tools.security_tools import scan_secrets_and_credentials, audit_code_vulnerabilities
from semantic_kernel.contents import ChatHistory


class SecurityAgent:
    """
    Agent 3: Security Agent (Separate Module)
    Inspects code changes for hardcoded credentials, SQL injection,
    eval/exec usage, and unsafe subprocess execution.
    """
    def __init__(self, agent_name: str = "SecurityAgent"):
        self.name = agent_name
        self.kernel, self.settings = create_sk_kernel(service_id=f"{self.name}_service")

    async def run(self, state: ChangeState) -> ChangeState:
        secret_findings = scan_secrets_and_credentials(state.raw_diff)
        audit_logger.append_entry(
            event_type="TOOL_CALL",
            diff_id=state.diff_id,
            agent_name=self.name,
            data={"tool": "scan_secrets_and_credentials", "secrets_detected": len(secret_findings)}
        )

        code_snippets: Dict[str, str] = {
            f.path: f.added_code
            for f in state.files
            if f.added_code.strip() and f.path.endswith(".py")
        }

        vuln_findings = audit_code_vulnerabilities(code_snippets)
        audit_logger.append_entry(
            event_type="TOOL_CALL",
            diff_id=state.diff_id,
            agent_name=self.name,
            data={"tool": "audit_code_vulnerabilities", "vulns_detected": len(vuln_findings)}
        )

        all_sec = secret_findings + vuln_findings

        for item in all_sec:
            target_file = item["file_path"]
            if target_file == "diff_stream" and state.files:
                target_file = state.files[0].path

            severity_enum = Severity(item["severity"])
            state.add_finding(
                Finding(
                    id=f"SEC-{uuid.uuid4().hex[:6]}",
                    agent=self.name,
                    file_path=target_file,
                    line_number=item.get("line_number"),
                    severity=severity_enum,
                    category=item["category"],
                    rule_id=item["rule_id"],
                    description=item["description"],
                    suggestion=item.get("suggestion"),
                )
            )

        if any(f.get("severity") == "CRITICAL" for f in all_sec):
            crit_summary = "\n".join([f"- {i['rule_id']}: {i['description']}" for i in all_sec if i.get("severity") == "CRITICAL"][:3])
            prompt = (
                f"You are the Security Agent for an Automated Code Review Board.\n"
                f"The following CRITICAL security flaws were flagged in the code diff:\n{crit_summary}\n"
                f"Write a sharp 2-sentence security risk alert explaining the threat to production."
            )
            try:
                chat_service = self.kernel.get_service(type=None)
                history = ChatHistory()
                history.add_user_message(prompt)
                response = await chat_service.get_chat_message_content(history, self.settings)
                state.log_event(self.name, "security_alert", {"alert": str(response.content).strip()})
            except Exception as e:
                state.warnings.append(f"SecurityAgent LLM alert skipped: {str(e)}")

        state.log_event(self.name, "security_scan_complete", {
            "secrets_detected": len(secret_findings),
            "vulnerabilities_detected": len(vuln_findings),
        })
        audit_logger.append_entry(
            event_type="AGENT_COMPLETE",
            diff_id=state.diff_id,
            agent_name=self.name,
            data={"total_security_findings": len(all_sec)}
        )
        return state
