# 🔄 Code hoạt động như thế nào?

## ✅ Đúng rồi! Code dùng **SMTP** (KHÔNG phải Google API)

---

## 📋 Flow hoạt động chi tiết

### **BƯỚC 1: User Request OTP**

```
Client (Frontend/Browser)
  ↓ POST /auth/request-otp
  ↓ { "email": "user@example.com" }
Backend (FastAPI)
```

**Code xử lý (`app/api/auth.py`):**
```python
1. Kiểm tra email đã tồn tại chưa
2. Tạo mã OTP 6 số: generate_otp() → "123456"
3. Tính thời gian hết hạn: expires_at = now + 10 phút
4. Xóa OTP cũ của email này (nếu có)
5. Lưu OTP vào database (otp_verification table)
6. Gọi send_otp_email(email, otp_code) ← ĐÂY LÀ PHẦN SMTP
```

---

### **BƯỚC 2: Gửi Email qua SMTP**

**Code xử lý (`app/email_service.py`):**

```python
def send_otp_email(to_email, otp_code):
    # 1. Tạo email message
    msg = MIMEMultipart()
    msg['From'] = "your-app@gmail.com"
    msg['To'] = to_email
    msg['Subject'] = "Mã xác thực OTP"
    body = f"Mã OTP của bạn: {otp_code}"
    msg.attach(MIMEText(body))
    
    # 2. KẾT NỐI đến SMTP server của Gmail
    # smtp.gmail.com:587 - đây là server của Gmail
    server = smtplib.SMTP("smtp.gmail.com", 587)
    
    # 3. BẬT MÃ HÓA TLS (bảo mật)
    server.starttls()
    
    # 4. ĐĂNG NHẬP bằng App Password
    # Không dùng mật khẩu Gmail thường!
    # Phải dùng App Password (16 ký tự)
    server.login("your-email@gmail.com", "app-password-16-chars")
    
    # 5. GỬI EMAIL qua SMTP protocol
    server.sendmail(from_email, to_email, message)
    
    # 6. ĐÓNG KẾT NỐI
    server.quit()
```

**Sơ đồ kết nối:**
```
Backend (Python)
  ↓ smtplib.SMTP()
  ↓ Kết nối TCP đến smtp.gmail.com:587
  ↓ STARTTLS (mã hóa)
  ↓ LOGIN với App Password
Gmail SMTP Server
  ↓ Nhận email
  ↓ Xử lý và gửi
Internet
  ↓ Email được gửi
User's Email Server
  ↓ User nhận email trong inbox
```

---

### **BƯỚC 3: User Nhận Email và Nhập OTP**

```
User mở email → Thấy mã OTP: "123456"
User nhập vào form: email + OTP + password
  ↓ POST /auth/verify-otp-and-register
  ↓ {
      "email": "user@example.com",
      "otp_code": "123456",
      "password": "securepass123"
    }
Backend (FastAPI)
```

**Code xử lý (`app/api/auth.py`):**
```python
1. Kiểm tra email đã tồn tại chưa
2. Tìm OTP record trong database:
   - Email phải khớp
   - OTP code phải khớp
   - verified = False (chưa dùng)
   - expires_at > now (chưa hết hạn)
3. Nếu không tìm thấy → Lỗi "Invalid or expired OTP"
4. Nếu tìm thấy:
   - Đánh dấu OTP đã dùng: verified = True
   - Hash password
   - Tạo User mới với email_verified = True
   - Lưu vào database
   - Trả về thông tin user
```

---

## 🔑 Điểm quan trọng: SMTP vs Google API

### **SMTP (Code hiện tại):**
- ✅ Gửi email **trực tiếp** qua giao thức SMTP (như bưu điện)
- ✅ Dùng `smtplib` (built-in Python, KHÔNG cần cài thêm)
- ✅ Chỉ cần **App Password** từ Gmail
- ✅ **KHÔNG cần** OAuth, tokens, API keys
- ✅ Hoạt động với **bất kỳ email provider nào** (Gmail, Outlook, Yahoo...)

### **Google Gmail API (KHÔNG dùng):**
- ❌ Cần OAuth 2.0 flow (phức tạp)
- ❌ Cần credentials.json, tokens
- ❌ Phải dùng `google-api-python-client` library
- ❌ Nhiều bước setup hơn
- ⚠️ **CHỈ hoạt động với Gmail**, không dùng được với email khác

---

## 🎯 Tóm tắt: Code hoạt động thế nào?

```
1. User request OTP
   → Backend tạo mã OTP (6 số)
   → Lưu vào database

2. Backend gửi email
   → Kết nối SMTP đến smtp.gmail.com
   → Đăng nhập bằng App Password
   → Gửi email qua SMTP protocol
   → Gmail server nhận và gửi đến user

3. User nhận email, nhập OTP
   → Backend verify OTP từ database
   → Tạo tài khoản mới
   → Xong!
```

---

## ✅ Kết luận

**Code hiện tại:**
- ✅ Dùng **SMTP** (đúng!)
- ✅ **KHÔNG dùng** Google API (không cần thiết)
- ✅ Phù hợp cho demo/test
- ✅ Đơn giản, dễ debug
- ✅ Chỉ cần App Password

**Lưu ý:**
- SMTP chỉ để **GỬI email** (đủ cho OTP)
- Không thể **ĐỌC email** hay quản lý inbox (không cần cho OTP)
- Gmail cho phép ~500 emails/ngày với App Password (đủ cho demo)

