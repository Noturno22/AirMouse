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

    return app


app = create_app()
