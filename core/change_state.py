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
        mapping = {
            "CRITICAL": 1,
            "HIGH": 2,
            "MEDIUM": 3,
            "LOW": 4,
            "INFO": 5,
        }
        return mapping.get(self.value, 99)


class Finding(BaseModel):
    id: str = Field(description="Unique identifier for the finding")
    agent: str = Field(description="Agent module name that produced the finding")
    file_path: str = Field(description="Target file path")
    line_number: Optional[int] = Field(default=None, description="Line number if identifiable")
    severity: Severity = Field(description="Finding severity level")
    category: str = Field(description="Classification e.g. 'Security Vulnerability'")
    rule_id: str = Field(description="Rule identifier")
    description: str = Field(description="Detailed explanation of the issue")
    suggestion: Optional[str] = Field(default=None, description="Suggested remedy")


class TouchedFile(BaseModel):
    path: str
    change_type: str = "modified"
    additions: int = 0
    deletions: int = 0
    added_code: str = ""
    deleted_code: str = ""
    is_test_file: bool = False


class ChangeState(BaseModel):
    diff_id: str
    raw_diff: str
    files: List[TouchedFile] = Field(default_factory=list)
    summary: str = ""
    total_additions: int = 0
    total_deletions: int = 0
    findings: List[Finding] = Field(default_factory=list)
    merge_verdict: Optional[str] = Field(default=None)
    verdict_rationale: Optional[str] = Field(default=None)
    priority_findings: List[Finding] = Field(default_factory=list)
    suggested_patch: Optional[str] = Field(default=None)
    patch_target_finding_id: Optional[str] = Field(default=None)
    warnings: List[str] = Field(default_factory=list)
    execution_trace: List[Dict[str, Any]] = Field(default_factory=list)

    def add_finding(self, finding: Finding) -> None:
        self.findings.append(finding)

    def log_event(self, agent_name: str, action: str, details: Dict[str, Any]) -> None:
        self.execution_trace.append({
            "agent": agent_name,
            "action": action,
            "details": details,
        })
