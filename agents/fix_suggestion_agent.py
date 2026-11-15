import re
from typing import Dict, Any, Optional
from core.change_state import ChangeState, Finding, Severity
from core.run_log import audit_logger
from core.config import create_sk_kernel
from tools.patch_tools import extract_code_context, generate_unified_patch
from semantic_kernel.contents import ChatHistory


class FixSuggestionAgent:
    """
    Agent 6: Fix-Suggestion Agent (Group-of-3 Add-on / Separate Module)
    Identifies the single highest-severity defect and synthesizes a concrete,
    ready-to-apply patch (unified diff) to resolve it.
    """
    def __init__(self, agent_name: str = "FixSuggestionAgent"):
        self.name = agent_name
        self.kernel, self.settings = create_sk_kernel(service_id=f"{self.name}_service")

    async def run(self, state: ChangeState) -> ChangeState:
        if not state.priority_findings:
            state.log_event(self.name, "skipped", {"reason": "No findings to generate fixes for."})
            return state

        top_finding: Finding = state.priority_findings[0]
        state.patch_target_finding_id = top_finding.id

        matched_file = None
        for f in state.files:
            if f.path == top_finding.file_path or top_finding.file_path.endswith(f.path):
                matched_file = f
                break

        original_code = matched_file.added_code if matched_file else ""
        if not original_code:
            original_code = state.raw_diff

        context = extract_code_context(
            file_content=original_code,
            target_line=top_finding.line_number,
            window=4
        )
        audit_logger.append_entry(
            event_type="TOOL_CALL",
            diff_id=state.diff_id,
            agent_name=self.name,
            data={"tool": "extract_code_context", "target_line": top_finding.line_number}
        )

        prompt = (
            f"You are the Fix-Suggestion Agent on an Automated Code Review Board.\n"
            f"A high-priority issue was flagged in '{top_finding.file_path}':\n"
            f"- Severity: {top_finding.severity.value}\n"
            f"- Rule: {top_finding.rule_id} ({top_finding.category})\n"
            f"- Description: {top_finding.description}\n"
            f"- Suggestion: {top_finding.suggestion}\n\n"
            f"Here is the code block around line {top_finding.line_number or 1}:\n"
            f"```python\n{context['snippet']}\n```\n\n"
            f"Please output ONLY the corrected Python replacement for this code block. "
            f"Do not include conversational preamble. Ensure it fixes the vulnerability/defect completely."
        )

        replacement_code = ""
        try:
            chat_service = self.kernel.get_service(type=None)
            history = ChatHistory()
            history.add_user_message(prompt)
            response = await chat_service.get_chat_message_content(history, self.settings)
            raw_text = str(response.content).strip()
            if "```" in raw_text:
                parts = raw_text.split("```")
                code_part = parts[1]
                if code_part.startswith("python"):
                    code_part = code_part[6:]
                replacement_code = code_part.strip()
            else:
                replacement_code = raw_text
        except Exception as e:
            replacement_code = f"# Fallback auto-fix: Replace with secure implementation\n# {top_finding.suggestion}"
            state.warnings.append(f"FixSuggestionAgent LLM fallback: {str(e)}")

        target_path = top_finding.file_path if top_finding.file_path != "diff_stream" else "src/module.py"
        patch = generate_unified_patch(
            file_path=target_path,
            original_code=context["snippet"] or original_code,
            replacement_code=replacement_code
        )
        audit_logger.append_entry(
            event_type="TOOL_CALL",
            diff_id=state.diff_id,
            agent_name=self.name,
            data={"tool": "generate_unified_patch", "patch_length": len(patch)}
        )

        state.suggested_patch = patch
        state.log_event(self.name, "patch_generated", {
            "target_finding_id": top_finding.id,
            "target_file": target_path,
            "patch_preview": patch[:300],
        })
        audit_logger.append_entry(
            event_type="AGENT_COMPLETE",
            diff_id=state.diff_id,
            agent_name=self.name,
            data={"patch_target_finding_id": top_finding.id}
        )
        return state
