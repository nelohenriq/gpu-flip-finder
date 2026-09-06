from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import delete

from src.db.models import Comp
from src.db.session import SessionLocal, init_db
from src.db.comps import CompRecord, add_comps, import_csv, ingest_olx_snapshot

router = APIRouter(prefix="/comps", tags=["comps"])


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/seed/olx")
def seed_olx() -> JSONResponse:
    try:
        count = ingest_olx_snapshot()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return JSONResponse({"seeded": count, "source": "olx"})


@router.post("/import/csv")
def import_csv_endpoint(file: UploadFile = File(...), source: str = "csv") -> JSONResponse:
    from pathlib import Path
    path = Path(f"/tmp/{file.filename}")
    path.write_bytes(file.file.read())
    try:
        records = import_csv(path, source_label=source)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"CSV import failed: {exc}") from exc
    finally:
        path.unlink(missing_ok=True)

    if not records:
        return JSONResponse({"imported": 0})

    db = SessionLocal()
    try:
        comps = add_comps(db, records)
    finally:
        db.close()
    return JSONResponse({"imported": len(comps), "source": source})


@router.delete("/clear")
def clear_comps() -> JSONResponse:
    db = SessionLocal()
    try:
        result = db.execute(delete(Comp))
        db.commit()
        return JSONResponse({"deleted": result.rowcount})
    finally:
        db.close()
