from fastapi import APIRouter, Depends, Query, Request

from boxoffice.modules.audit.contract import AuditApi
from boxoffice.shared.web import require_user

router = APIRouter(tags=["audit"], dependencies=[Depends(require_user)])


@router.get("/audit")
def list_audit(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    subject_type: str | None = None,
):
    api: AuditApi = request.app.state.audit_api
    return api.list_entries(limit, offset, subject_type)
