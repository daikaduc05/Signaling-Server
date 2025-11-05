# ⚡ Test Nhanh OTP - 5 phút

## 🚀 Các bước test nhanh

### 1. Tạo Gmail App Password (5 phút)
1. Vào https://myaccount.google.com/security
2. Bật **2-Step Verification** (nếu chưa)
3. Vào **App passwords** → Chọn **Mail** → Generate
4. **SAO CHÉP** mật khẩu 16 ký tự (chỉ hiển thị 1 lần!)

### 2. Tạo file `.env`

Tạo file `.env` trong thư mục gốc:

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
FROM_EMAIL=your-email@gmail.com
DATABASE_URL=postgresql://user:password@localhost/signaling_db
SECRET_KEY=your-secret-key
```

**Thay thế:**
- `your-email@gmail.com` → Email Gmail của bạn
- `your-16-char-app-password` → App Password vừa tạo (bỏ dấu cách)

### 3. Chạy Migration

```bash
python -m alembic upgrade head
```

### 4. Start Server

```bash
python -m uvicorn app.main:app --reload
```

### 5. Test trên Browser (Dễ nhất!)

Mở: **http://localhost:8000/docs**

#### Test Step 1: Request OTP
1. Tìm `POST /auth/request-otp`
2. Click **"Try it out"**
3. Nhập:
```json
{"email": "your-email@gmail.com"}
```
4. Click **"Execute"**
5. ✅ Kiểm tra email để lấy mã OTP

#### Test Step 2: Verify OTP
1. Tìm `POST /auth/verify-otp-and-register`
2. Click **"Try it out"**
3. Nhập (thay `123456` bằng mã OTP thực):
```json
{
  "email": "your-email@gmail.com",
  "otp_code": "123456",
  "password": "testpass123"
}
```
4. Click **"Execute"**
5. ✅ Xong! Đăng ký thành công!

---

## 🐍 Hoặc dùng Script Python

```bash
# Cài requests (nếu chưa có)
pip install requests

# Chạy script
python test_otp_api.py
```

Script sẽ hỏi từng bước!

---

## ❌ Lỗi thường gặp

### "Failed to send OTP email"
- Kiểm tra App Password trong `.env` đúng chưa
- Đảm bảo đã bật 2-Step Verification

### "Invalid or expired OTP"
- Mã OTP sai hoặc đã hết hạn (10 phút)
- Request OTP mới

### Không nhận được email
- Kiểm tra thư mục Spam
- Đảm bảo App Password đúng

---

**Xem hướng dẫn chi tiết trong `HUONG_DAN_TEST.md`** 📖

