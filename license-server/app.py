"""FastAPI app for the AirMouse License Server."""
from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from storage import connect, init_db


def get_db():
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


def create_app() -> FastAPI:
    app = FastAPI(title="AirMouse License Server")

    @app.on_event("startup")
    def _startup():
        conn = connect()
        init_db(conn)
        conn.close()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
