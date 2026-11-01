from enum import Enum
from pydantic import BaseModel, EmailStr, Field, model_validator


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class InputType(str, Enum):
    url = "url"
    text = "text"


class Recruiter(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)


class InvestigationCreate(BaseModel):
    input_type: InputType
    job_url: str | None = Field(default=None, max_length=2048)
    job_text: str | None = Field(default=None, max_length=10000)
    recruiter: Recruiter | None = None

    @model_validator(mode="after")
    def require_matching_input(self):
        if self.input_type is InputType.url and not self.job_url:
            raise ValueError("A job URL is required.")
        if self.input_type is InputType.text and not self.job_text:
            raise ValueError("A job description is required.")
        return self


class InvestigationAccepted(BaseModel):
    id: str
    status: str = "queued"


class Finding(BaseModel):
    title: str
    detail: str
    status: str
    quote: str | None = None


class Source(BaseModel):
    url: str
    title: str = "Job listing"
    source_type: str = "job_listing"


class EvidenceNode(BaseModel):
    id: str
    label: str
    node_type: str
    status: str
    url: str | None = None


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str


class EvidenceGraph(BaseModel):
    nodes: list[EvidenceNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)


class Report(BaseModel):
    risk_level: RiskLevel
    risk_score: int
    summary: str
    fee_detected: bool
    findings: list[Finding]
    next_steps: list[str]
    sources: list[Source] = Field(default_factory=list)
    graph: EvidenceGraph = Field(default_factory=EvidenceGraph)
    disclaimer: str = "Advisory assessment based on public information, not a guarantee."
