import asyncio
import uuid
from typing import Optional
from core.change_state import ChangeState
from core.run_log import audit_logger
from agents.diff_agent import DiffAgent
from agents.style_agent import StyleAgent
from agents.security_agent import SecurityAgent
from agents.test_coverage_agent import TestCoverageAgent
from agents.reviewer_manager import ReviewerManagerAgent
from agents.fix_suggestion_agent import FixSuggestionAgent


class CodeReviewOrchestrator:
    """
    Coordinates the Automated Code Review Board using a Fan-out / Fan-in
    architecture with Reviewer Manager and Group-of-3 Fix-Suggestion add-on.
    """
    def __init__(self):
        self.diff_agent = DiffAgent()
        self.style_agent = StyleAgent()
        self.security_agent = SecurityAgent()
        self.test_coverage_agent = TestCoverageAgent()
        self.reviewer_manager = ReviewerManagerAgent()
        self.fix_suggestion_agent = FixSuggestionAgent()

    async def review_code_change(self, raw_diff: str, diff_id: Optional[str] = None) -> ChangeState:
        if not diff_id:
            diff_id = f"DIFF-{uuid.uuid4().hex[:8].upper()}"

        state = ChangeState(diff_id=diff_id, raw_diff=raw_diff)

        audit_logger.append_entry(
            event_type="WORKFLOW_START",
            diff_id=diff_id,
            agent_name="Orchestrator",
            data={"raw_diff_length": len(raw_diff)}
        )

        state = await self.diff_agent.run(state)

        if not state.files and not state.raw_diff.strip():
            audit_logger.append_entry(
                event_type="WORKFLOW_ABORT",
                diff_id=diff_id,
                agent_name="Orchestrator",
                data={"reason": "Empty or unparseable diff"}
            )
            return state

        await asyncio.gather(
            self.style_agent.run(state),
            self.security_agent.run(state),
            self.test_coverage_agent.run(state),
        )

        state = await self.reviewer_manager.run(state)

        if state.priority_findings:
            state = await self.fix_suggestion_agent.run(state)

        audit_logger.append_entry(
            event_type="WORKFLOW_COMPLETE",
            diff_id=diff_id,
            agent_name="Orchestrator",
            data={
                "verdict": state.merge_verdict,
                "total_findings": len(state.priority_findings),
                "has_patch": bool(state.suggested_patch),
            }
        )

        return state
