# 📋 Hướng dẫn Test OTP - Từng bước chi tiết

## 🎯 Mục tiêu
Test tính năng OTP đăng ký tài khoản từ đầu đến cuối.

---

## ✅ BƯỚC 1: Cấu hình Gmail SMTP

### 1.1. Tạo Gmail App Password

1. Vào [Google Account](https://myaccount.google.com/)
2. Chọn **Security** (Bảo mật) ở menu bên trái
3. Kéo xuống tìm **2-Step Verification** → Bật nếu chưa bật
4. Sau khi bật, quay lại **Security** → Tìm **App passwords**
5. Click **App passwords**
6. Chọn:
   - **App**: Mail
   - **Device**: Other (Custom name) → Nhập "Signaling Server"
7. Click **Generate**
8. **LƯU Ý**: Sao chép ngay mật khẩu 16 ký tự (chỉ hiển thị 1 lần!)
   - Ví dụ: `abcd efgh ijkl mnop`

### 1.2. Tạo file `.env`

Tạo file `.env` trong thư mục gốc của project:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost/signaling_db

# JWT
SECRET_KEY=your-secret-key-here

# Gmail SMTP (QUAN TRỌNG!)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=abcdefghijklmnop
FROM_EMAIL=your-email@gmail.com
```

**Thay thế:**
- `your-email@gmail.com` → Email Gmail của bạn
- `abcdefghijklmnop` → App Password 16 ký tự vừa tạo (bỏ dấu cách)
- `postgresql://user:password@localhost/signaling_db` → Database URL của bạn

---

## ✅ BƯỚC 2: Cập nhật Database

### Cách 1: Dùng Alembic (Khuyên dùng)

```bash
# Đảm bảo đang ở thư mục gốc của project
cd D:\TaiLieuNam3_DUT\PBL4\Signaling-Server

# Chạy migration
python -m alembic upgrade head
```

**Kết quả mong đợi:**
```
INFO  [alembic.runtime.migration] Running upgrade 7e72e27993c0 -> add_otp_email_verified, Add OTP verification and email verified
```

### Cách 2: Chạy SQL trực tiếp (Nếu không có Alembic)

Mở PostgreSQL và chạy:

```sql
-- Thêm cột email_verified vào bảng user
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE NOT NULL;

-- Tạo bảng otp_verification
CREATE TABLE IF NOT EXISTS otp_verification (
    id SERIAL PRIMARY KEY,
    email VARCHAR NOT NULL,
    otp_code VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    verified BOOLEAN DEFAULT FALSE NOT NULL
);

-- Tạo index
CREATE INDEX IF NOT EXISTS ix_otp_verification_email ON otp_verification(email);
```

---

## ✅ BƯỚC 3: Khởi động Server

```bash
# Đảm bảo đang ở thư mục gốc
python -m uvicorn app.main:app --reload
```

**Kết quả:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Database initialized successfully
INFO:     Application startup complete.
```

Server đang chạy tại: **http://localhost:8000**

---

## ✅ BƯỚC 4: Test API

Bạn có **3 cách** để test:

---

### 🌐 CÁCH 1: Dùng Swagger UI (Dễ nhất, khuyên dùng)

#### Mở browser:
```
http://localhost:8000/docs
```

Bạn sẽ thấy giao diện Swagger UI với danh sách các API endpoints.

#### Test Step 1: Request OTP

1. Tìm endpoint **`POST /auth/request-otp`**
2. Click **"Try it out"** (nút màu xanh)
3. Trong phần **Request body**, xóa code mẫu và nhập:
```json
{
  "email": "test@example.com"
}
```
   (Thay `test@example.com` bằng email của bạn - email mà bạn muốn nhận OTP)
4. Click **"Execute"** (nút màu xanh ở dưới)
5. Xem kết quả:
   - **Status Code**: `200` → ✅ Thành công!
   - **Response**: 
     ```json
     {
       "message": "OTP code has been sent to your email",
       "expires_in": 600
     }
     ```
6. ✅ **Kiểm tra email của bạn** (có thể trong thư mục Spam)
   - Subject: "Mã xác thực OTP đăng ký tài khoản"
   - Body: Chứa mã OTP 6 chữ số (ví dụ: `123456`)

#### Test Step 2: Verify OTP và Đăng ký

1. Tìm endpoint **`POST /auth/verify-otp-and-register`**
2. Click **"Try it out"**
3. Nhập JSON (thay `123456` bằng mã OTP thực từ email):
```json
{
  "email": "test@example.com",
  "otp_code": "123456",
  "password": "mypassword123"
}
```
4. Click **"Execute"**
5. Xem kết quả:
   - **Status Code**: `200` → ✅ Đăng ký thành công!
   - **Response**:
     ```json
     {
       "message": "Account registered successfully",
       "user": {
         "id": 1,
         "email": "test@example.com",
         "email_verified": true
       }
     }
     ```

---

### 🐍 CÁCH 2: Dùng Script Python

#### Cài requests (nếu chưa có):
```bash
pip install requests
```

#### Chạy script:
```bash
python test_otp_api.py
```

#### Script sẽ hỏi từng bước:
```
TEST OTP VERIFICATION API
============================================================

📝 Nhập thông tin để test:
Email: test@example.com

============================================================
BƯỚC 1: Gửi yêu cầu OTP
============================================================
POST http://localhost:8000/auth/request-otp
...
Status Code: 200

✅ Thành công! Kiểm tra email của bạn để lấy mã OTP
   Mã OTP có hiệu lực trong 600 giây

------------------------------------------------------------
📧 Kiểm tra email của bạn để lấy mã OTP
------------------------------------------------------------

Nhập mã OTP từ email: 123456
Nhập password cho tài khoản: mypassword123

============================================================
BƯỚC 2: Xác thực OTP và Đăng ký
============================================================
...
✅ TEST THÀNH CÔNG!
```

---

### 💻 CÁCH 3: Dùng cURL (Command Line)

#### Test Request OTP:

**Windows PowerShell:**
```powershell
curl -X POST http://localhost:8000/auth/request-otp `
  -H "Content-Type: application/json" `
  -d '{\"email\": \"test@example.com\"}'
```

**Linux/Mac:**
```bash
curl -X POST http://localhost:8000/auth/request-otp \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

#### Test Verify OTP:

**Windows PowerShell:**
```powershell
curl -X POST http://localhost:8000/auth/verify-otp-and-register `
  -H "Content-Type: application/json" `
  -d '{\"email\": \"test@example.com\", \"otp_code\": \"123456\", \"password\": \"mypassword123\"}'
```

**Linux/Mac:**
```bash
curl -X POST http://localhost:8000/auth/verify-otp-and-register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "otp_code": "123456", "password": "mypassword123"}'
```

---

## ✅ BƯỚC 5: Kiểm tra Database (Tùy chọn)

Mở PostgreSQL và kiểm tra:

```sql
-- Xem user mới được tạo
SELECT * FROM "user" WHERE email = 'test@example.com';

-- Xem OTP records
SELECT * FROM otp_verification WHERE email = 'test@example.com';
```

Bạn sẽ thấy:
- User mới với `email_verified = true`
- OTP record với `verified = true`

---

## ❌ Xử lý lỗi thường gặp

### 1. "Failed to send OTP email"
**Nguyên nhân:**
- App Password sai hoặc chưa tạo
- SMTP config trong `.env` sai
- 2-Step Verification chưa bật

**Giải pháp:**
- Kiểm tra lại App Password trong `.env`
- Đảm bảo đã bật 2-Step Verification
- Kiểm tra log của server để xem lỗi chi tiết

### 2. "Invalid or expired OTP code"
**Nguyên nhân:**
- Mã OTP sai
- Mã OTP đã hết hạn (quá 10 phút)
- Mã OTP đã được sử dụng

**Giải pháp:**
- Request OTP mới
- Nhập lại mã OTP đúng

### 3. "Email already registered"
**Nguyên nhân:**
- Email đã được đăng ký trước đó

**Giải pháp:**
- Dùng email khác
- Hoặc xóa user trong database:
  ```sql
  DELETE FROM "user" WHERE email = 'test@example.com';
  ```

### 4. Không nhận được email
**Kiểm tra:**
- Thư mục Spam/Junk
- Email có bị chặn không
- Kiểm tra log server xem có lỗi không
- Thử request OTP lại

### 5. Server không chạy được
**Kiểm tra:**
- Database có đang chạy không?
- DATABASE_URL trong `.env` đúng chưa?
- Đã cài đủ packages chưa? (`pip install -r requirements.txt`)

---

## 🎯 Checklist trước khi test

- [ ] Đã tạo Gmail App Password
- [ ] Đã tạo file `.env` với SMTP config đúng
- [ ] Đã chạy migration database
- [ ] Server đang chạy (`python -m uvicorn app.main:app --reload`)
- [ ] Có thể truy cập `http://localhost:8000/docs`

---

## 📝 Lưu ý quan trọng

1. **App Password**: Là mật khẩu 16 ký tự (KHÔNG phải mật khẩu Gmail thường)
2. **OTP hết hạn sau 10 phút**: Request OTP mới nếu quá lâu
3. **Mỗi email chỉ có 1 OTP chưa verify**: Request OTP mới sẽ xóa OTP cũ
4. **Gmail quota**: ~500 emails/ngày với App Password (đủ cho demo/test)

---

## ✅ Kết quả mong đợi

Sau khi test thành công, bạn sẽ:
- ✅ Nhận được email chứa mã OTP
- ✅ Đăng ký tài khoản thành công
- ✅ User trong database có `email_verified = true`

---

## 🎉 Hoàn thành!

Bạn đã test thành công tính năng OTP! 🚀

