from typing import Dict, Any, List
from core.change_state import ChangeState, Finding, Severity
from core.run_log import audit_logger
from core.config import create_sk_kernel
from tools.review_tools import deduplicate_and_rank_findings, compute_merge_verdict
from semantic_kernel.contents import ChatHistory


class ReviewerManagerAgent:
    """
    Agent 5: Reviewer Manager (Separate Module)
    Fans in findings from parallel review specialists, deduplicates redundant signals,
    sorts findings by severity priority order, and issues the definitive merge verdict.
    """
    def __init__(self, agent_name: str = "ReviewerManager"):
        self.name = agent_name
        self.kernel, self.settings = create_sk_kernel(service_id=f"{self.name}_service")

    async def run(self, state: ChangeState) -> ChangeState:
        raw_findings_dict: List[Dict[str, Any]] = [
            {
                "id": f.id,
                "agent": f.agent,
                "file_path": f.file_path,
                "line_number": f.line_number,
                "severity": f.severity.value,
                "category": f.category,
                "rule_id": f.rule_id,
                "description": f.description,
                "suggestion": f.suggestion,
            }
            for f in state.findings
        ]

        ranked_dicts = deduplicate_and_rank_findings(raw_findings_dict)
        audit_logger.append_entry(
            event_type="TOOL_CALL",
            diff_id=state.diff_id,
            agent_name=self.name,
            data={"tool": "deduplicate_and_rank_findings", "input_count": len(raw_findings_dict), "output_count": len(ranked_dicts)}
        )

        severity_counts: Dict[str, int] = {}
        for item in ranked_dicts:
            sev = item["severity"]
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        has_cov_blocker = any(
            f["severity"] in ("CRITICAL", "HIGH") and "COV" in f.get("rule_id", "")
            for f in ranked_dicts
        )

        verdict_res = compute_merge_verdict(
            severity_counts=severity_counts,
            has_test_coverage_blocker=has_cov_blocker
        )
        audit_logger.append_entry(
            event_type="TOOL_CALL",
            diff_id=state.diff_id,
            agent_name=self.name,
            data={"tool": "compute_merge_verdict", "verdict": verdict_res.get("verdict")}
        )

        state.merge_verdict = verdict_res["verdict"]
        state.priority_findings = [
            Finding(
                id=d["id"],
                agent=d["agent"],
                file_path=d["file_path"],
                line_number=d.get("line_number"),
                severity=Severity(d["severity"]),
                category=d["category"],
                rule_id=d["rule_id"],
                description=d["description"],
                suggestion=d.get("suggestion"),
            )
            for d in ranked_dicts
        ]

        findings_breakdown = "\n".join([
            f"[{f.severity.value}] {f.rule_id} ({f.file_path}:{f.line_number or 'N/A'}) - {f.description}"
            for f in state.priority_findings[:5]
        ]) or "No defects detected."

        prompt = (
            f"You are the Lead Reviewer Manager on the Automated Code Review Board.\n"
            f"Change Summary: {state.summary}\n"
            f"Verdict: {state.merge_verdict.upper()}\n"
            f"Severity Breakdown: {severity_counts}\n"
            f"Top Issues:\n{findings_breakdown}\n"
            f"Draft a formal, professional 2-3 sentence executive review note justifying this decision."
        )

        try:
            chat_service = self.kernel.get_service(type=None)
            history = ChatHistory()
            history.add_user_message(prompt)
            response = await chat_service.get_chat_message_content(history, self.settings)
            state.verdict_rationale = str(response.content).strip()
        except Exception as e:
            state.verdict_rationale = verdict_res["summary"]
            state.warnings.append(f"ReviewerManager LLM rationale fallback: {str(e)}")

        state.log_event(self.name, "verdict_adjudicated", {
            "verdict": state.merge_verdict,
            "severity_counts": severity_counts,
            "rationale": state.verdict_rationale,
        })
        audit_logger.append_entry(
            event_type="DECISION",
            diff_id=state.diff_id,
            agent_name=self.name,
            data={
                "verdict": state.merge_verdict,
                "severity_counts": severity_counts,
                "rationale": state.verdict_rationale,
            }
        )
        return state
