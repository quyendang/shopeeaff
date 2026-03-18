# Shopee Affiliate Telegram Bot

Bot Telegram tự động chuyển link Shopee thành link affiliate kèm voucher giảm giá.

## Tính năng

- Nhận link Shopee bất kỳ (link đầy đủ hoặc link rút gọn `s.shopee.vn`, `shope.ee`)
- Trả về link affiliate — tap vào để **copy nhanh** trên mobile
- Kèm nút bấm mở thẳng bài viết Facebook để lấy mã giảm giá
- Hỗ trợ nhiều link trong cùng 1 tin nhắn
- Cập nhật link Facebook ngay runtime bằng lệnh bí mật (không cần restart)

---

## Deploy lên Koyeb (khuyến nghị)

### Bước 1 — Tạo bot Telegram

1. Nhắn tin `@BotFather` trên Telegram
2. Gõ `/newbot` và làm theo hướng dẫn
3. Lưu lại **Bot Token** (dạng `123456789:ABCdef...`)

### Bước 2 — Fork/clone repo này lên GitHub của bạn

### Bước 3 — Tạo app trên Koyeb

1. Đăng nhập [koyeb.com](https://www.koyeb.com) → **Create App**
2. Chọn **GitHub** → chọn repo này
3. Chọn loại service: **Worker**
4. **Build command:**
   ```
   pip install -r requirements.txt
   ```
5. **Run command:**
   ```
   python main.py
   ```
6. Chuyển sang tab **Environment variables**, thêm các biến bên dưới
7. Bấm **Deploy**

### Biến môi trường

| Biến | Bắt buộc | Mô tả | Mặc định |
|------|----------|-------|----------|
| `BOT_TOKEN` | ✅ | Token lấy từ @BotFather | — |
| `PW_CONFIG` | ✅ | Mật khẩu để đổi link Facebook qua lệnh bot | — |
| `FACEBOOK_URL` | | Link bài viết Facebook chứa mã giảm giá | link mặc định |
| `AFF_ID` | | Affiliate ID của bạn | `17325690040` |
| `SUB_ID` | | Sub ID tracking | `fb-voucher` |
| `WORKER_API` | | API giải link rút gọn Shopee | link mặc định |

---

## Chạy local (để test)

```bash
# Cài dependencies
pip install -r requirements.txt

# Chạy bot
BOT_TOKEN=your_token PW_CONFIG=your_password python main.py
```

Dùng file `.env` cho tiện:
```bash
cp .env.example .env
# Sửa .env điền BOT_TOKEN và PW_CONFIG
python -m dotenv run python main.py
```

---

## Sử dụng

### Chuyển link Shopee
Chỉ cần gửi link Shopee vào chat với bot:

```
https://shopee.vn/product/123456/789
```

Bot sẽ trả về:
```
🔗 Link affiliate:
[link dài — tap để copy]

💬 👉 Vào Facebook lấy mã giảm giá
```

### Cập nhật link Facebook
Dùng lệnh bí mật (thay `your_password` bằng giá trị `PW_CONFIG` bạn đã cài):

```
/your_password https://www.facebook.com/share/p/xxxxx
```

Bot xác nhận thành công và từ tin nhắn kế tiếp sẽ dùng link mới ngay.
