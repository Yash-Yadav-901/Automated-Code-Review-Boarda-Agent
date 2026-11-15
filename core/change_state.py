from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

    @property
    def rank(self) -> int:
        """Numerical rank for sorting: lower number = higher severity."""
        mapping = {
            "CRITICAL": 1,
            "HIGH": 2,
            "MEDIUM": 3,
            "LOW": 4,
            "INFO": 5,
        }
        return mapping.get(self.value, 99)


class Finding(BaseModel):
    """Represents an issue discovered by any specialized review agent."""
    id: str = Field(description="Unique identifier for the finding")
    agent: str = Field(description="Agent module name that produced the finding")
    file_path: str = Field(description="Target file path")
    line_number: Optional[int] = Field(default=None, description="Line number if identifiable")
    severity: Severity = Field(description="Finding severity level")
    category: str = Field(description="Classification e.g. 'Security Vulnerability', 'PEP 8 Style', 'Missing Test'")
    rule_id: str = Field(description="Unique rule code e.g. SEC-001, STY-002, COV-003")
    description: str = Field(description="Detailed explanation of the issue")
    suggestion: Optional[str] = Field(default=None, description="Suggested remedy or best practice")


class TouchedFile(BaseModel):
    """Metadata regarding a file modified in the diff."""
    path: str
    change_type: str = "modified"  # modified, added, deleted
    additions: int = 0
    deletions: int = 0
    added_code: str = ""
    deleted_code: str = ""
    is_test_file: bool = False


class ChangeState(BaseModel):
    """
    Central shared state object for the Automated Code Review Board.
    Every agent reads from and writes updates to this object during execution.
    """
    diff_id: str
    raw_diff: str
    files: List[TouchedFile] = Field(default_factory=list)
    summary: str = ""
    total_additions: int = 0
    total_deletions: int = 0
    
    # Shared findings list where review agents append observations
    findings: List[Finding] = Field(default_factory=list)
    
    # Merge adjudication fields populated by ReviewerManager
    merge_verdict: Optional[str] = Field(default=None)  # "approve" | "request-changes"
    verdict_rationale: Optional[str] = Field(default=None)
    priority_findings: List[Finding] = Field(default_factory=list)
    
    # Suggested patch for single highest-severity issue (Group-of-3 add-on)
    suggested_patch: Optional[str] = Field(default=None)
    patch_target_finding_id: Optional[str] = Field(default=None)
    
    # Non-crashing warnings / honest failure notifications
    warnings: List[str] = Field(default_factory=list)
    
    # Chronological execution trace
    execution_trace: List[Dict[str, Any]] = Field(default_factory=list)

    def add_finding(self, finding: Finding) -> None:
        """Thread-safe append of a finding to shared state."""
        self.findings.append(finding)

    def log_event(self, agent_name: str, action: str, details: Dict[str, Any]) -> None:
        """Append an event to the internal trace."""
        self.execution_trace.append({
            "agent": agent_name,
            "action": action,
            "details": details,
        })
