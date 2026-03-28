from datetime import datetime
from app.models import AuditEntry


def create_audit_entry(envelope_id: str, result: str, details: dict) -> AuditEntry:
    return AuditEntry(
        timestamp=datetime.utcnow().isoformat(),
        service="validation_service",
        action="validate",
        envelope_id=envelope_id,
        result=result,
        details=details,
    )