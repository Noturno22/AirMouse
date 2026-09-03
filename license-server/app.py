"""FastAPI app for the AirMouse License Server."""
import json
import os

from fastapi import Depends, FastAPI, Request
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


class MobileEntitleRequest(BaseModel):
    purchase_token: str
    product_id: str
    package_name: str
    device_id: str


def create_app() -> FastAPI:
    app = FastAPI(title="Mãouse License Server")

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

    from service import mobile_entitle

    @app.post("/api/v1/mobile/entitle")
    def api_mobile_entitle(req: MobileEntitleRequest, db=Depends(get_db)):
        expected_product = os.getenv("AIRMOUSE_MOBILE_PRODUCT_ID",
                                     "maouse_mobile_pro")
        from playstore import PlayValidationError, validate_purchase
        try:
            lease, session_id, first_time = mobile_entitle(
                db, req.purchase_token, req.product_id, req.package_name,
                req.device_id, expected_product, validate_purchase)
        except ValueError as exc:
            return JSONResponse(status_code=422, content={"error": str(exc)})
        except PlayValidationError as exc:
            return JSONResponse(status_code=403, content={"error": str(exc)})
        return {"tier": "mobile_pro", "lease": lease,
                "session_id": session_id, "first_time": first_time}

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

    from emailer import send_key_email
    from paddle import event_info, verify_signature
    from storage import connect as storage_connect
    from storage import init_db, purchase_for_event, record_purchase

    @app.post("/webhooks/paddle")
    async def paddle_webhook(request: Request):
        secret = os.getenv("AIRMOUSE_PADDLE_WEBHOOK_SECRET", "")
        if not secret:
            return JSONResponse(status_code=503,
                                content={"error": "paddle_nao_configurado"})
        raw = (await request.body()).decode("utf-8")
        sig = request.headers.get("Paddle-Signature", "")
        if not verify_signature(raw, sig, secret):
            return JSONResponse(status_code=401, content={"error": "assinatura_invalida"})
        try:
            event = json.loads(raw)
        except ValueError:
            return JSONResponse(status_code=400, content={"error": "json_invalido"})
        info = event_info(event)
        if info is None:
            # evento irrelevante (ex.: transaction.paid) -> reconhecer, nada a fazer
            return {"ok": True, "handled": False}
        # ligação local criada e usada no mesmo thread (async handler)
        conn = storage_connect()
        init_db(conn)
        try:
            existing = purchase_for_event(conn, info["event_id"])
            if existing is not None:
                return {"ok": True, "handled": True, "key": existing["key_hash"]}
            key = issue_key(conn, info["email"])
            record_purchase(conn, info["event_id"], info["email"],
                            key, info["product_id"])
        finally:
            conn.close()
        send_key_email(info["email"], key)
        return {"ok": True, "handled": True, "key": key, "email": info["email"]}

    return app


app = create_app()
