"""FastAPI app for the AirMouse License Server."""
from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from storage import connect, init_db


def get_db():
    conn = connect()
    init_db(conn)
    try:
        yield conn
    finally:
        conn.close()


class KeyRequest(BaseModel):
    email: str
    admin_token: str


class KeyResponse(BaseModel):
    key: str
    email: str


class ActivateRequest(BaseModel):
    key: str
    machine_id: str


class ActivateResponse(BaseModel):
    tier: str
    lease: str
    session_id: str
    use_seq: int


class TrialRequest(BaseModel):
    machine_id: str
    used_seconds: int = 0


class TrialReportRequest(BaseModel):
    machine_id: str
    used_seconds: int


class RevalidateRequest(BaseModel):
    machine_id: str
    old_lease: str


class RevokeRequest(BaseModel):
    machine_id: str
    admin_token: str


def create_app() -> FastAPI:
    app = FastAPI(title="AirMouse License Server")

    @app.on_event("startup")
    def _startup():
        conn = connect()
        init_db(conn)
        conn.close()

    from service import authorized, issue_key

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/admin/keys")
    def admin_issue_key(req: KeyRequest, db=Depends(get_db)):
        if not authorized(req.admin_token):
            return JSONResponse(status_code=403, content={"error": "forbidden"})
        key = issue_key(db, req.email)
        return KeyResponse(key=key, email=req.email)

    from service import activate

    @app.post("/api/v1/activate")
    def api_activate(req: ActivateRequest, db=Depends(get_db)):
        try:
            lease, session_id, use_seq = activate(
                db, req.key.strip(), req.machine_id.strip())
        except ValueError as exc:
            return JSONResponse(status_code=403, content={"error": str(exc)})
        return ActivateResponse(tier="pro", lease=lease,
                                session_id=session_id, use_seq=use_seq)

    from service import trial_remaining, trial_report
    from storage import TRIAL_MAX_SECONDS

    @app.post("/api/v1/trial/start")
    def trial_start(req: TrialRequest, db=Depends(get_db)):
        from storage import get_trial, set_trial_used
        row = get_trial(db, req.machine_id)
        if row is None:
            set_trial_used(db, req.machine_id, 0)
        remaining = trial_remaining(db, req.machine_id)
        return {"machine_id": req.machine_id, "remaining_seconds": remaining,
                "trial_seconds": TRIAL_MAX_SECONDS}

    @app.post("/api/v1/trial/report")
    def api_trial_report(req: TrialReportRequest, db=Depends(get_db)):
        remaining = trial_report(db, req.machine_id, req.used_seconds)
        return {"machine_id": req.machine_id, "remaining_seconds": remaining}

    @app.get("/api/v1/trial/status")
    def trial_status(machine_id: str, db=Depends(get_db)):
        return {"machine_id": machine_id,
                "remaining_seconds": trial_remaining(db, machine_id)}

    from service import revalidate, revoke_machine

    @app.post("/api/v1/revalidate")
    def api_revalidate(req: RevalidateRequest, db=Depends(get_db)):
        try:
            lease = revalidate(db, req.machine_id.strip(), req.old_lease.strip())
        except ValueError as exc:
            return JSONResponse(status_code=403, content={"error": str(exc)})
        return {"tier": "pro", "lease": lease}

    @app.post("/api/v1/revoke")
    def api_revoke(req: RevokeRequest, db=Depends(get_db)):
        if not authorized(req.admin_token):
            return JSONResponse(status_code=403, content={"error": "forbidden"})
        revoke_machine(db, req.machine_id)
        return {"ok": True}

    return app


app = create_app()
