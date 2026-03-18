import os
import re
import logging
import httpx
from urllib.parse import quote, urlparse
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── Cấu hình ──────────────────────────────────────────────────────────────────
BOT_TOKEN    = os.environ["BOT_TOKEN"]
WEBHOOK_URL  = os.environ["WEBHOOK_URL"].rstrip("/")   # VD: https://xxx.koyeb.app
PORT         = int(os.environ.get("PORT", 8000))

AFF_ID       = os.environ.get("AFF_ID",       "17325690040")
SUB_ID       = os.environ.get("SUB_ID",       "fb-voucher")
FACEBOOK_URL = os.environ.get("FACEBOOK_URL", "https://www.facebook.com/share/p/1EAjKXe3mr/")
WORKER_API   = os.environ.get("WORKER_API",   "https://shopee-link.lamtypre.workers.dev/")

# Regex bắt mọi dạng link Shopee trong tin nhắn
SHOPEE_RE = re.compile(
    r"https?://(?:s\.shopee\.vn|shope\.ee|shopee\.vn|shopee\.com)/[^\s]+"
)

# ── Xử lý link ────────────────────────────────────────────────────────────────

async def resolve_short_url(url: str) -> str:
    """Gọi Worker API để giải ngắn link s.shopee.vn / shope.ee → URL dài."""
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(WORKER_API, params={"url": url})
        resp.raise_for_status()
        data = resp.json()
        return data.get("final_url", url)


def clean_url(url: str) -> str:
    """Giữ lại origin + pathname, bỏ toàn bộ query params & fragment."""
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}{p.path}"


async def to_affiliate_link(raw_url: str) -> str:
    """Chuyển link Shopee bất kỳ → link affiliate."""
    p = urlparse(raw_url)
    if p.netloc in ("s.shopee.vn", "shope.ee"):
        raw_url = await resolve_short_url(raw_url)

    cleaned = clean_url(raw_url)
    encoded = quote(cleaned, safe="")
    aff_link = (
        f"https://s.shopee.vn/an_redir"
        f"?origin_link={encoded}"
        f"&affiliate_id={AFF_ID}"
        f"&sub_id={SUB_ID}"
    )
    return aff_link

# ── Handlers ──────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Gửi link Shopee cho tôi!\n"
        "Tôi sẽ tạo link affiliate để bạn lấy mã giảm giá 🎁"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or update.message.caption or ""
    links = SHOPEE_RE.findall(text)

    if not links:
        return  # không có link shopee → bỏ qua

    results = []
    for raw in links:
        # Bỏ dấu câu thừa ở cuối (.,;!?)
        raw = raw.rstrip(".,;!?)")
        try:
            aff = await to_affiliate_link(raw)
            results.append(aff)
        except Exception as e:
            logger.error("Lỗi xử lý %s: %s", raw, e)

    if not results:
        await update.message.reply_text("❌ Không thể xử lý link. Vui lòng thử lại.")
        return

    lines = []
    for i, aff in enumerate(results, 1):
        prefix = f"🔗 Link {i}:\n" if len(results) > 1 else "🔗 Link affiliate:\n"
        # <code> cho phép tap-to-copy trên Telegram mobile
        lines.append(f"{prefix}<code>{aff}</code>")

    reply = "\n\n".join(lines)
    reply += f'\n\n💬 <a href="{FACEBOOK_URL}">👉 Vào Facebook lấy mã giảm giá</a>'

    await update.message.reply_text(
        reply,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )

# ── PTB Application ───────────────────────────────────────────────────────────

ptb = Application.builder().token(BOT_TOKEN).build()
ptb.add_handler(CommandHandler("start", cmd_start))
ptb.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
ptb.add_handler(MessageHandler(filters.CAPTION & ~filters.COMMAND, handle_message))

# ── FastAPI + Lifespan ────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    await ptb.initialize()
    webhook_endpoint = f"{WEBHOOK_URL}/webhook"
    await ptb.bot.set_webhook(url=webhook_endpoint, allowed_updates=["message"])
    logger.info("Webhook đã đặt: %s", webhook_endpoint)
    await ptb.start()
    yield
    await ptb.stop()
    await ptb.shutdown()


app = FastAPI(lifespan=lifespan)


@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, ptb.bot)
    await ptb.process_update(update)
    return {"ok": True}


@app.get("/")
async def health():
    return {"status": "running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
