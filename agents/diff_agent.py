import uuid
from typing import Dict, Any
from core.change_state import ChangeState, TouchedFile
from core.run_log import audit_logger
from core.config import create_sk_kernel
from tools.diff_tools import parse_unified_diff, compute_diff_metrics
from semantic_kernel.contents import ChatHistory


class DiffAgent:
    """
    Agent 1: Diff Agent (Separate Module)
    Analyzes raw diffs, extracts touched files, hunks, and metrics,
    and generates an executive change summary.
    """
    def __init__(self, agent_name: str = "DiffAgent"):
        self.name = agent_name
        self.kernel, self.settings = create_sk_kernel(service_id=f"{self.name}_service")

    async def run(self, state: ChangeState) -> ChangeState:
        parse_res = parse_unified_diff(state.raw_diff)
        audit_logger.append_entry(
            event_type="TOOL_CALL",
            diff_id=state.diff_id,
            agent_name=self.name,
            data={"tool": "parse_unified_diff", "file_count": len(parse_res.get("files", []))}
        )

        if not parse_res.get("success", False):
            state.warnings.append(f"DiffAgent: {parse_res.get('error', 'Malformed diff')}")
            state.summary = "Diff parsing aborted: invalid or empty diff."
            return state

        state.files = [
            TouchedFile(
                path=f["path"],
                change_type=f["change_type"],
                additions=f["additions"],
                deletions=f["deletions"],
                added_code=f["added_code"],
                deleted_code=f["deleted_code"],
                is_test_file=f["is_test_file"],
            )
            for f in parse_res.get("files", [])
        ]
        state.total_additions = parse_res.get("total_additions", 0)
        state.total_deletions = parse_res.get("total_deletions", 0)

        metrics = compute_diff_metrics(parse_res.get("files", []))
        audit_logger.append_entry(
            event_type="TOOL_CALL",
            diff_id=state.diff_id,
            agent_name=self.name,
            data={"tool": "compute_diff_metrics", "metrics": metrics}
        )

        file_list_str = ", ".join([f.path for f in state.files]) or "None"
        prompt = (
            f"You are the Diff Analysis Agent for an Automated Code Review Board.\n"
            f"Summarize the following code modification in 2-3 concise sentences:\n"
            f"- Files touched: {file_list_str}\n"
            f"- Lines added: {state.total_additions}, Lines deleted: {state.total_deletions}\n"
            f"- Risk footprint: {metrics.get('risk_footprint')}\n"
            f"- Diff excerpt:\n{state.raw_diff[:1200]}\n"
            f"Provide a direct technical summary of intent and scope."
        )

        try:
            chat_service = self.kernel.get_service(type=None)
            history = ChatHistory()
            history.add_user_message(prompt)
            response = await chat_service.get_chat_message_content(history, self.settings)
            state.summary = str(response.content).strip()
        except Exception as e:
            state.summary = (
                f"Change touches {len(state.files)} file(s) with +{state.total_additions}/-{state.total_deletions} churn. "
                f"Modified files: {file_list_str}."
            )
            state.warnings.append(f"DiffAgent LLM call fell back to heuristic: {str(e)}")

        state.log_event(self.name, "diff_analyzed", {
            "files_count": len(state.files),
            "additions": state.total_additions,
            "deletions": state.total_deletions,
            "summary": state.summary,
        })
        audit_logger.append_entry(
            event_type="AGENT_COMPLETE",
            diff_id=state.diff_id,
            agent_name=self.name,
            data={"summary": state.summary}
        )
        return state
