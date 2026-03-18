# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Telegram bot nhận link Shopee từ người dùng, chuyển thành link affiliate (có thể lấy mã giảm giá), và trả về kèm link Facebook. Thiết kế để deploy trên Koyeb dùng webhook (không dùng polling).

## Architecture

- `main.py` — toàn bộ logic: FastAPI app + python-telegram-bot webhook handler
- Dùng `lifespan` của FastAPI để khởi tạo PTB và đăng ký webhook với Telegram khi app start
- Webhook endpoint: `POST /webhook` nhận update từ Telegram
- Health check: `GET /`

## Conversion Flow

1. Regex tìm link Shopee trong tin nhắn (`s.shopee.vn`, `shope.ee`, `shopee.vn`)
2. Nếu là link rút gọn → gọi Worker API `WORKER_API?url={encoded}` → lấy `final_url`
3. Clean URL: giữ `origin + pathname`, bỏ query params
4. Build affiliate link: `https://s.shopee.vn/an_redir?origin_link={encoded}&affiliate_id={AFF_ID}&sub_id={SUB_ID}`
5. Reply bằng HTML parse mode: link affiliate trong `<code>` (tap-to-copy), link Facebook dạng `<a href>`

## Environment Variables

| Var | Bắt buộc | Mô tả |
|-----|----------|-------|
| `BOT_TOKEN` | ✅ | Token từ @BotFather |
| `WEBHOOK_URL` | ✅ | URL public của app (vd: https://xxx.koyeb.app) |
| `AFF_ID` | | Affiliate ID (default: 17325690040) |
| `SUB_ID` | | Sub ID tracking (default: fb-voucher) |
| `FACEBOOK_URL` | | Link Facebook post (default đã cấu hình) |
| `WORKER_API` | | Worker API giải link rút gọn |

## Deploy lên Koyeb

1. Push code lên GitHub
2. Tạo app mới trên Koyeb → chọn repo → Runtime: Python
3. Build command: `pip install -r requirements.txt`
4. Run command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Thêm environment variables (BOT_TOKEN + WEBHOOK_URL = URL Koyeb cấp)

## Run local (để test)

```bash
pip install -r requirements.txt
BOT_TOKEN=xxx WEBHOOK_URL=https://your-ngrok-url uvicorn main:app --reload
```

Dùng ngrok để có HTTPS public URL khi test local: `ngrok http 8000`
