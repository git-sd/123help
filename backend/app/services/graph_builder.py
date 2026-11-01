from app.models.schemas import EvidenceGraph, EvidenceNode, GraphEdge, Finding, Source


def build_graph(company_name: str | None, job_title: str | None, recruiter_email: str | None,
                findings: list[Finding], sources: list[Source]) -> EvidenceGraph:
    nodes: list[EvidenceNode] = [EvidenceNode(id="job", label=job_title or "Job listing", node_type="job", status="observed")]
    edges: list[GraphEdge] = []
    if company_name:
        nodes.append(EvidenceNode(id="company", label=company_name, node_type="company", status="unverified"))
        edges.append(GraphEdge(source="job", target="company", relation="names"))
    if recruiter_email:
        nodes.append(EvidenceNode(id="recruiter-email", label=recruiter_email, node_type="recruiter", status="observed"))
        edges.append(GraphEdge(source="job", target="recruiter-email", relation="contacted by"))
    for index, finding in enumerate(findings):
        node_id = f"finding-{index}"
        status = "warning" if finding.status == "warning" else finding.status
        nodes.append(EvidenceNode(id=node_id, label=finding.title, node_type="finding", status=status))
        edges.append(GraphEdge(source="job", target=node_id, relation="has finding"))
    for index, source in enumerate(sources):
        node_id = f"source-{index}"
        nodes.append(EvidenceNode(id=node_id, label=source.title or source.url, node_type="source", status="evidence", url=source.url))
        edges.append(GraphEdge(source="job", target=node_id, relation="supported by"))
    return EvidenceGraph(nodes=nodes, edges=edges)
