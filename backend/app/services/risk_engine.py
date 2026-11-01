import re
from app.models.schemas import Finding, Report, RiskLevel

FEE_PATTERNS = [
    r"(?:registration|reg\.?|processing)\s*(?:fee|charge|charges)",
    r"security\s+deposit", r"mandatory\s+(?:paid\s+)?training",
    r"pay\s+(?:rs\.?|inr|₹)?\s*\d+", r"transfer\s+(?:money|amount)",
    r"upi\s+(?:id|payment|transfer)", r"seat\s+(?:confirmation|booking)\s*(?:fee|amount)?",
]
NEGATIONS = [r"no\s+fees?", r"never\s+charge", r"without\s+(?:any\s+)?fee"]


def assess_listing(text: str) -> Report:
    normalized = re.sub(r"\s+", " ", text.lower())
    findings: list[Finding] = []
    fee_match = next((re.search(pattern, normalized, re.I) for pattern in FEE_PATTERNS), None)
    no_fee = any(re.search(pattern, normalized, re.I) for pattern in NEGATIONS)
    if fee_match and not no_fee:
        start, end = max(0, fee_match.start() - 48), min(len(text), fee_match.end() + 90)
        findings.append(Finding(title="Payment request detected", detail="This listing appears to ask an applicant for money.", status="warning", quote=text[start:end].strip()))
        return Report(risk_level=RiskLevel.high, risk_score=82, fee_detected=True,
            summary="A payment-related warning was found. Verify independently before paying anything.", findings=findings,
            next_steps=["Do not send money or UPI payments.", "Contact the company using its official website.", "Save the listing and evidence in case you need to report it."])
    if re.search(r"guaranteed\s+(?:selection|job)|urgent(?:ly)?|limited\s+seats", normalized, re.I):
        findings.append(Finding(title="Pressure language detected", detail="Urgency or guaranteed-selection language deserves extra verification.", status="unverified"))
        return Report(risk_level=RiskLevel.medium, risk_score=48, fee_detected=False,
            summary="We found claims that need independent verification before you apply.", findings=findings,
            next_steps=["Check the role on the official careers page.", "Confirm the recruiter using an official company contact."])
    return Report(risk_level=RiskLevel.low, risk_score=18, fee_detected=False,
        summary="No major warning signs were found in the supplied text. Continue to verify details independently.", findings=[],
        next_steps=["Verify the company domain before responding.", "Never share financial or identity documents early in a process."])
