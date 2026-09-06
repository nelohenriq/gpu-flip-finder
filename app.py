from __future__ import annotations

import os
from typing import Iterable

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.api.comps import router as comps_router
from src.config.settings import settings
from src.db.session import SessionLocal, init_db
from src.scrapers.olx import Listing
from src.scrapers.pipeline import run_pipeline
from src.ai.valuation import margin, score_listing

app = FastAPI(title="gpu-flip-finder", version="0.1.0")
app.include_router(comps_router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "env": settings.app_env})


@app.get("/deals")
def deals() -> JSONResponse:
    db = SessionLocal()
    try:
        results = []
        for listing in run_pipeline(["RTX", "RX", "placa gráfica", "GPU"], max_pages=settings.scrape_max_pages):
            persisted = _persist_listing(db, listing)
            valuation = score_listing(db, persisted.title, persisted.price)
            m = margin(persisted.price, valuation.estimated_value)
            if m >= settings.min_margin and persisted.price <= settings.max_listing_price:
                results.append(
                    {
                        "id": persisted.id,
                        "title": persisted.title,
                        "price": persisted.price,
                        "estimated_value": valuation.estimated_value,
                        "margin": round(m, 4),
                        "confidence": valuation.confidence,
                        "comps_used": valuation.comps_used,
                        "url": persisted.url,
                        "source": persisted.source,
                        "location": persisted.location,
                        "condition": persisted.condition,
                        "last_seen_at": persisted.last_seen_at.isoformat() if persisted.last_seen_at else None,
                    }
                )
        return JSONResponse({"deals": results[:50], "count": len(results)})
    finally:
        db.close()


@app.get("/stats")
def stats() -> JSONResponse:
    db = SessionLocal()
    try:
        from sqlalchemy import func
        from src.db.models import Comp, Listing

        model_rows = (
            db.query(Comp.model, func.count().label("count"), func.avg(Comp.price).label("avg"), func.median(Comp.price).label("median"))
            .group_by(Comp.model)
            .order_by(func.count().desc())
            .all()
        )

        recent_listings = (
            db.query(Listing.source, func.count().label("count"), func.avg(Listing.price).label("avg_price"))
            .group_by(Listing.source)
            .all()
        )

        return JSONResponse(
            {
                "comps_by_model": [
                    {
                        "model": row.model,
                        "count": int(row.count),
                        "avg": float(row.avg) if row.avg is not None else None,
                        "median": float(row.median) if row.median is not None else None,
                    }
                    for row in model_rows
                ],
                "listings_by_source": [
                    {
                        "source": row.source,
                        "count": int(row.count),
                        "avg_price": float(row.avg_price) if row.avg_price is not None else None,
                    }
                    for row in recent_listings
                ],
            }
        )
    finally:
        db.close()


def _persist_listing(db, listing: Listing):
    from src.db.models import Listing as ORMListing
    from datetime import datetime
    import uuid

    existing = db.query(ORMListing).filter_by(source=listing.source, external_id=listing.external_id).first()
    if existing:
        existing.price = listing.price
        existing.last_seen_at = datetime.utcnow()
        existing.is_active = True
        db.flush()
        return existing

    record = ORMListing(
        id=str(uuid.uuid4()),
        source=listing.source,
        external_id=listing.external_id,
        title=listing.title,
        url=listing.url,
        price=listing.price,
        currency=listing.currency,
        condition=listing.condition,
        location=listing.location,
        seller=listing.seller,
    )
    db.add(record)
    db.flush()
    return record


def run() -> None:
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), reload=settings.app_env != "prod")
