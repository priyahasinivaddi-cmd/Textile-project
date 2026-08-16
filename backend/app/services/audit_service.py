import json
from app.models.operations import AuditLog


def record_audit(db, *, user_id, action, entity_type, entity_id=None, details=None, request_id=None):
    db.add(AuditLog(user_id=user_id, action=action, entity_type=entity_type, entity_id=str(entity_id) if entity_id is not None else None, details_json=json.dumps(details or {}, default=str), request_id=request_id))
