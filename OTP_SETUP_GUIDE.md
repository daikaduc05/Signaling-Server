# Hướng dẫn cấu hình OTP Email Verification

## Tổng quan

Tính năng OTP (One-Time Password) đã được tích hợp vào quá trình đăng ký tài khoản. Người dùng cần xác thực email bằng mã OTP trước khi có thể hoàn tất đăng ký.

## Các bước cấu hình

### 1. Cấu hình Gmail SMTP

Để gửi email OTP qua Gmail, bạn cần:

#### a. Bật 2-Step Verification trên Google Account
1. Vào [Google Account](https://myaccount.google.com/)
2. Chọn **Security** (Bảo mật)
3. Bật **2-Step Verification** (Xác minh 2 bước) nếu chưa bật

#### b. Tạo App Password
1. Vào **Security** > **2-Step Verification**
2. Cuộn xuống và chọn **App passwords**
3. Chọn app: **Mail**
4. Chọn device: **Other (Custom name)** - nhập tên như "Signaling Server"
5. Nhấn **Generate**
6. Sao chép mật khẩu 16 ký tự được tạo (chỉ hiển thị 1 lần)

### 2. Cấu hình file .env

Tạo file `.env` từ `config.env.example` và điền thông tin:

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-character-app-password
FROM_EMAIL=your-email@gmail.com
```

**Lưu ý:** 
- `SMTP_PASSWORD` là **App Password** (16 ký tự), KHÔNG phải mật khẩu Gmail thường
- `SMTP_USERNAME` và `FROM_EMAIL` thường là cùng một email

### 3. Cập nhật Database

Thêm bảng mới vào database để lưu trữ OTP:

```sql
-- Thêm cột email_verified vào bảng user
ALTER TABLE "user" ADD COLUMN email_verified BOOLEAN DEFAULT FALSE NOT NULL;

-- Tạo bảng otp_verification
CREATE TABLE otp_verification (
    id SERIAL PRIMARY KEY,
    email VARCHAR NOT NULL,
    otp_code VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    verified BOOLEAN DEFAULT FALSE NOT NULL
);

CREATE INDEX ix_otp_verification_email ON otp_verification(email);
```

Hoặc nếu bạn đang dùng Alembic, tạo migration:

```bash
alembic revision -m "Add OTP verification table"
```

Sau đó cập nhật file migration với các thay đổi trên.

## API Endpoints

### 1. Request OTP
**POST** `/auth/request-otp`

Request body:
```json
{
  "email": "user@example.com"
}
```

Response:
```json
{
  "message": "OTP code has been sent to your email",
  "expires_in": 600
}
```

### 2. Verify OTP and Register
**POST** `/auth/verify-otp-and-register`

Request body:
```json
{
  "email": "user@example.com",
  "otp_code": "123456",
  "password": "securepassword123"
}
```

Response:
```json
{
  "message": "Account registered successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "email_verified": true
  }
}
```

## Quy trình đăng ký mới

1. **Người dùng nhập email** → Gọi `/auth/request-otp`
2. **Hệ thống gửi OTP** → Gửi mã 6 chữ số đến email
3. **Người dùng nhập OTP + password** → Gọi `/auth/verify-otp-and-register`
4. **Hệ thống xác thực và tạo tài khoản** → Trả về thông tin user

## Tính năng bảo mật

- OTP có thời hạn 10 phút
- OTP chỉ được sử dụng 1 lần
- Mỗi email chỉ có 1 OTP chưa verify tại một thời điểm
- Tự động xóa OTP cũ khi request OTP mới

## Troubleshooting

### Lỗi: "Failed to send OTP email"
- Kiểm tra lại App Password đã đúng chưa
- Đảm bảo 2-Step Verification đã bật
- Kiểm tra kết nối internet và firewall

### Lỗi: "Invalid or expired OTP code"
- OTP đã hết hạn (10 phút)
- OTP đã được sử dụng
- Nhập sai mã OTP

### Không nhận được email
- Kiểm tra thư mục Spam/Junk
- Đảm bảo email không bị chặn bởi Google
- Thử request OTP lại

