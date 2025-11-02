
### **Flow hoạt động:**

```
1. User request OTP
   ↓
2. Backend tạo mã OTP (6 số ngẫu nhiên)
   ↓
3. Backend lưu OTP vào database (otp_verification table)
   ↓
4. Backend gọi send_otp_email()
   ↓
5. Code kết nối đến smtp.gmail.com:587 (SMTP server)
   ↓
6. Xác thực bằng App Password
   ↓
7. Gửi email với mã OTP qua SMTP protocol
   ↓
8. Gmail server nhận và gửi email đến người dùng
   ↓
9. User nhận email, nhập OTP
   ↓
10. Backend verify OTP và tạo tài khoản
```

### **Chi tiết code SMTP:**

```python
# 1. Tạo email message
msg = MIMEMultipart()
msg['From'] = "your-email@gmail.com"
msg['To'] = "user@example.com"
msg['Subject'] = "Mã xác thực OTP"
msg.attach(MIMEText("Mã OTP: 123456"))

# 2. Kết nối đến SMTP server của Gmail
server = smtplib.SMTP("smtp.gmail.com", 587)
server.starttls()  # Bật mã hóa TLS

# 3. Đăng nhập bằng App Password
server.login("your-email@gmail.com", "app-password-16-chars")

# 4. Gửi email
server.sendmail(from_email, to_email, message)

# 5. Đóng kết nối
server.quit()
```

---

## 📊 So sánh SMTP vs Google API


**Code hiện tại đã ĐÚNG và PHÙ HỢP cho demo/test!**

- ✅ Dùng **SMTP** (đơn giản, nhanh)
- ✅ KHÔNG cần Google API (phức tạp, không cần thiết)
- ✅ Chỉ cần App Password từ Gmail
- ✅ Hoạt động ngay sau khi config `.env`

**Chỉ cần đổi sang Google API khi:**
- Cần đọc email từ inbox
- Cần quản lý labels, threads
- Cần gửi số lượng lớn (hàng triệu emails)
- Production với yêu cầu cao về security

