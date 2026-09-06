from __future__ import annotations

from dataclasses import dataclass

from telegram import Update
from telegram.constants import ChatType
from telegram.ext import Application, CommandHandler, ContextTypes

from src.config.settings import settings
from src.db.session import SessionLocal
from src.scrapers.olx import OLXScraper


@dataclass
class Alert:
    title: str
    price: float
    url: str
    margin_pct: float


async def _is_allowed(update: Update) -> bool:
    user_id = update.effective_user.id if update.effective_user else None
    if not user_id:
        return False
    allowed = {part.strip() for part in settings.telegram_allowed_user_ids.split(",") if part.strip()}
    return not allowed or str(user_id) in allowed


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _is_allowed(update):
        return
    await update.message.reply_text(
        "GPU Flip Finder is running.\nUse /deals to scan OLX and /status to check bot state."
    )


async def deals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _is_allowed(update):
        return

    await update.message.reply_text("Scanning OLX for GPU deals...")
    scraper = OLXScraper(settings.olx_base_url, max_pages=settings.scrape_max_pages)
    db = SessionLocal()
    try:
        alerts = []
        for listing in scraper.fetch_pages(["RTX", "RX", "placa gráfica", "GPU"]):
            from src.ai.valuation import margin, score_listing
            valuation = score_listing(db, listing.title, listing.price)
            m = margin(listing.price, valuation.estimated_value)
            if m >= settings.min_margin and listing.price <= settings.max_listing_price:
                alerts.append(
                    Alert(
                        title=listing.title,
                        price=listing.price,
                        url=listing.url,
                        margin_pct=round(m * 100, 1),
                    )
                )
        if not alerts:
            await update.message.reply_text("No qualifying deals in this scan.")
            return
        lines = [f"• {a.title}\n  €{a.price:.2f} | margin ~{a.margin_pct:.1f}%\n  {a.url}" for a in alerts[:10]]
        await update.message.reply_text("\n\n".join(lines))
    finally:
        db.close()


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _is_allowed(update):
        return
    await update.message.reply_text(
        f"Env={settings.app_env}\nMin margin={settings.min_margin:.0%}\nMax price={settings.max_listing_price:.0f} EUR"
    )


def build_bot() -> Application:
    application = Application.builder().token(settings.telegram_bot_token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("deals", deals))
    application.add_handler(CommandHandler("status", status))
    return application
