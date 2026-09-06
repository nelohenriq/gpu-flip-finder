from __future__ import annotations

import os
import uvicorn

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.config.settings import settings
from src.db.session import init_db


app = FastAPI(title="gpu-flip-finder", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "env": settings.app_env})


@app.get("/deals")
def deals() -> JSONResponse:
    from src.scrapers.pipeline import run_pipeline
    from src.ai.valuation import margin, score_listing
    from src.db.session import SessionLocal

    results = []
    db = SessionLocal()
    try:
        for listing in run_pipeline(["RTX", "RX", "placa gráfica", "GPU"], max_pages=settings.scrape_max_pages):
            valuation = score_listing(db, listing.title, listing.price)
            m = margin(listing.price, valuation.estimated_value)
            if m >= settings.min_margin and listing.price <= settings.max_listing_price:
                results.append(
                    {
                        "title": listing.title,
                        "price": listing.price,
                        "estimated_value": valuation.estimated_value,
                        "margin": round(m, 4),
                        "url": listing.url,
                        "source": listing.source,
                    }
                )
    finally:
        db.close()
    return JSONResponse({"deals": results[:20], "count": len(results)})


def run() -> None:
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), reload=settings.app_env != "prod")
