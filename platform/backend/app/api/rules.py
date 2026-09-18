"""Read-only view of the LMPC rules database + engine connectivity."""
import json

from fastapi import APIRouter, Depends, HTTPException

from app.config import PLATFORM_ROOT, get_settings
from app.core.engine_client import engine_client
from app.core.security import require_roles
from app.models.user import ROLE_ADMIN, ROLE_OFFICER, ROLE_REVIEWER, User

router = APIRouter(prefix="/rules", tags=["rules"])

_AUTH = Depends(require_roles(ROLE_OFFICER, ROLE_REVIEWER, ROLE_ADMIN))

_RULES_PATH = (
    PLATFORM_ROOT.parent
    / "Compliance_Engine_CV_NLP"
    / "rules"
    / "lmpc_rules_database.json"
)


@router.get("")
def get_rules(
    _: User = _AUTH,
):
    """Return the digitized LMPC rule database (read-only reference)."""
    if not _RULES_PATH.is_file():
        raise HTTPException(status_code=404, detail="rules database not found")
    with open(_RULES_PATH, encoding="utf-8") as fh:
        return json.load(fh)


@router.get("/health")
async def rules_health(
    _: User = _AUTH,
):
    return {
        "rules_file": str(_RULES_PATH),
        "rules_present": _RULES_PATH.is_file(),
        "engine_online": (await engine_client.health()) is not None,
        "engine_base_url": get_settings().engine_base_url,
    }