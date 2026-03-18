import os
import re
import logging
import httpx
from urllib.parse import quote, urlparse

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
PW_CONFIG    = os.environ.get("PW_CONFIG", "")          # mật khẩu để đổi Facebook URL

AFF_ID       = os.environ.get("AFF_ID",       "17325690040")
SUB_ID       = os.environ.get("SUB_ID",       "fb-voucher")
WORKER_API   = os.environ.get("WORKER_API",   "https://shopee-link.lamtypre.workers.dev/")

# Dùng dict để có thể thay đổi trong runtime
config = {
    "facebook_url": os.environ.get("FACEBOOK_URL", "https://www.facebook.com/share/p/1EAjKXe3mr/")
}

SHOPEE_RE = re.compile(
    r"https?://(?:s\.shopee\.vn|shope\.ee|shopee\.vn|shopee\.com)/[^\s]+"
)

# ── Xử lý link ────────────────────────────────────────────────────────────────

async def resolve_short_url(url: str) -> str:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(WORKER_API, params={"url": url})
        resp.raise_for_status()
        return resp.json().get("final_url", url)


def clean_url(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}{p.path}"


async def to_affiliate_link(raw_url: str) -> str:
    p = urlparse(raw_url)
    if p.netloc in ("s.shopee.vn", "shope.ee"):
        raw_url = await resolve_short_url(raw_url)
    cleaned = clean_url(raw_url)
    encoded = quote(cleaned, safe="")
    return (
        f"https://s.shopee.vn/an_redir"
        f"?origin_link={encoded}"
        f"&affiliate_id={AFF_ID}"
        f"&sub_id={SUB_ID}"
    )

# ── Handlers ──────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Gửi link Shopee cho tôi!\n"
        "Tôi sẽ tạo link affiliate để bạn lấy mã giảm giá 🎁"
    )


async def handle_set_facebook(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý lệnh /{PW_CONFIG} <url> để cập nhật Facebook URL."""
    if not PW_CONFIG:
        return

    text = update.message.text or ""
    # Lấy phần URL sau command
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text("❌ Thiếu URL. Dùng: /" + PW_CONFIG + " <facebook_url>")
        return

    new_url = parts[1].strip()
    parsed = urlparse(new_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        await update.message.reply_text("❌ URL không hợp lệ.")
        return

    config["facebook_url"] = new_url
    logger.info("Facebook URL đã cập nhật: %s", new_url)
    await update.message.reply_text(f"✅ Đã cập nhật Facebook URL:\n{new_url}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or update.message.caption or ""
    links = SHOPEE_RE.findall(text)

    if not links:
        return

    results = []
    for raw in links:
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
        lines.append(f"{prefix}<code>{aff}</code>")

    reply = "\n\n".join(lines)
    reply += f'\n\n💬 <a href="{config["facebook_url"]}">👉 Vào Facebook lấy mã giảm giá</a>'

    await update.message.reply_text(
        reply,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))

    # Đăng ký command bí mật để đổi Facebook URL
    if PW_CONFIG:
        app.add_handler(CommandHandler(PW_CONFIG, handle_set_facebook))
        logger.info("Command bí mật đã đăng ký: /%s", PW_CONFIG)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.CAPTION & ~filters.COMMAND, handle_message))

    logger.info("Bot đang chạy (polling)...")
    app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
