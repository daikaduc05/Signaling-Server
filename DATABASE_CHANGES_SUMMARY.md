# Tóm tắt thay đổi Database cho SMTP, Ping-Pong và Disconnect Check

## 📋 Tổng quan

Sau khi thêm các tính năng SMTP, ping-pong và disconnect check, database đã được cập nhật với các bảng và cột mới để hỗ trợ các tính năng này.

## 🆕 Các thay đổi chính

### 1. **Bảng `smtp_settings`** (MỚI)

Bảng này lưu trữ cấu hình SMTP cho email. Có thể cấu hình:
- **Global**: `org_id = NULL` - Cấu hình SMTP mặc định cho toàn hệ thống
- **Per-Organization**: `org_id` không NULL - Cấu hình SMTP riêng cho từng organization

**Các cột:**
- `id`: Primary key
- `org_id`: Foreign key tới `organization.id` (NULL = global, NOT NULL = per-org)
- `smtp_server`: Địa chỉ SMTP server (ví dụ: smtp.gmail.com)
- `smtp_port`: Cổng SMTP (ví dụ: 587)
- `smtp_username`: Username để đăng nhập SMTP
- `smtp_password`: Password để đăng nhập SMTP (nên mã hóa trong production)
- `from_email`: Email người gửi
- `use_tls`: Có sử dụng TLS/SSL không (mặc định: true)
- `is_active`: Cấu hình có đang active không (mặc định: true)
- `created_at`: Thời gian tạo
- `updated_at`: Thời gian cập nhật lần cuối

**Indexes:**
- `ix_smtp_settings_org_id`: Index trên `org_id` để tìm kiếm nhanh
- Unique constraint: Mỗi organization chỉ có 1 SMTP config (hoặc 1 global config với `org_id = NULL`)

**Lợi ích:**
- Cho phép mỗi organization có SMTP server riêng
- Có thể fallback về global config nếu organization không có config riêng
- Dễ dàng thay đổi cấu hình SMTP mà không cần restart server

---

### 2. **Bảng `connection_status`** (MỚI)

Bảng này theo dõi trạng thái kết nối WebSocket và heartbeat (ping-pong) của các agent.

**Các cột:**
- `id`: Primary key
- `user_id`: Foreign key tới `user.id` - User nào đang kết nối
- `org_id`: Foreign key tới `organization.id` - Organization nào
- `virtual_ip`: Virtual IP được gán cho connection này
- `peer_id`: ID của peer/agent
- `connection_id`: UUID của connection session
- `public_ip`: Public IP của agent
- `public_port`: Public port của agent
- `status`: Trạng thái connection (`connected`, `disconnected`, `timeout`)
- `connected_at`: Thời gian kết nối
- `disconnected_at`: Thời gian ngắt kết nối (NULL nếu đang connected)
- `last_ping_at`: Thời gian gửi ping lần cuối
- `last_pong_at`: Thời gian nhận pong lần cuối
- `last_seen_at`: Thời gian hoạt động lần cuối (updated khi có ping/pong)

**Indexes:**
- `ix_connection_status_user_id`: Tìm connections theo user
- `ix_connection_status_org_id`: Tìm connections theo organization
- `ix_connection_status_virtual_ip`: Tìm connection theo virtual IP
- `ix_connection_status_status`: Tìm connections theo trạng thái
- `ix_connection_status_last_seen_at`: Tìm connections cũ/không hoạt động

**Lợi ích:**
- **Persistence**: Lưu trữ lịch sử kết nối, không mất khi server restart
- **Monitoring**: Có thể query để xem ai đang online, ai đã disconnect
- **Debugging**: Track được ping/pong để debug connection issues
- **Analytics**: Phân tích thời gian kết nối, số lần timeout, etc.

**Cách sử dụng:**
- Khi agent connect: Tạo record mới với `status = 'connected'`, `connected_at = now()`
- Khi nhận pong: Update `last_pong_at` và `last_seen_at`
- Khi gửi ping: Update `last_ping_at`
- Khi disconnect: Update `status = 'disconnected'`, `disconnected_at = now()`
- Khi timeout: Update `status = 'timeout'`, `disconnected_at = now()`

---

### 3. **Cột `last_seen_at` trong bảng `virtual_ip_mapping`** (THÊM)

Thêm cột `last_seen_at` vào bảng `virtual_ip_mapping` để track lần cuối virtual IP được sử dụng.

**Cột:**
- `last_seen_at`: DateTime, nullable - Thời gian lần cuối virtual IP được sử dụng

**Lợi ích:**
- Quick lookup: Không cần join với `connection_status` để biết virtual IP có đang được dùng không
- Cleanup: Có thể xóa các virtual IP không được dùng trong thời gian dài

---

## 📊 Sơ đồ quan hệ (ERD)

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       │ 1:N
       │
┌──────▼──────────────────┐
│  ConnectionStatus        │
│  - user_id (FK)         │
│  - org_id (FK)          │
│  - virtual_ip           │
│  - status               │
│  - last_ping_at         │
│  - last_pong_at         │
│  - last_seen_at         │
└──────┬──────────────────┘
       │
       │ N:1
       │
┌──────▼─────────────┐
│  Organization      │
└──────┬─────────────┘
       │
       │ 1:1
       │
┌──────▼─────────────┐
│  SMTPSettings      │
│  - org_id (FK)     │
│  - smtp_server     │
│  - smtp_port       │
│  - smtp_username   │
│  - smtp_password   │
│  - from_email      │
└────────────────────┘
```

---

## 🔄 Migration

File migration: `alembic/versions/add_smtp_and_connection_tracking.py`

**Để chạy migration:**
```bash
alembic upgrade head
```

**Để rollback:**
```bash
alembic downgrade -1
```

---

## 💡 Gợi ý sử dụng

### 1. SMTP Settings

**Tạo global SMTP config:**
```sql
INSERT INTO smtp_settings (org_id, smtp_server, smtp_port, smtp_username, smtp_password, from_email)
VALUES (NULL, 'smtp.gmail.com', 587, 'your-email@gmail.com', 'password', 'your-email@gmail.com');
```

**Tạo SMTP config cho organization:**
```sql
INSERT INTO smtp_settings (org_id, smtp_server, smtp_port, smtp_username, smtp_password, from_email)
VALUES (1, 'smtp.company.com', 587, 'noreply@company.com', 'password', 'noreply@company.com');
```

**Query SMTP config (ưu tiên org config, fallback global):**
```sql
SELECT * FROM smtp_settings 
WHERE (org_id = 1 OR org_id IS NULL) AND is_active = true
ORDER BY org_id DESC NULLS LAST  -- Org config trước, global sau
LIMIT 1;
```

### 2. Connection Status

**Tạo connection record khi agent connect:**
```python
connection = ConnectionStatus(
    user_id=user.id,
    org_id=org_id,
    virtual_ip=virtual_ip,
    peer_id=peer_id,
    connection_id=connection_id,
    public_ip=public_ip,
    public_port=public_port,
    status='connected'
)
db.add(connection)
db.commit()
```

**Update khi nhận pong:**
```python
connection.last_pong_at = datetime.utcnow()
connection.last_seen_at = datetime.utcnow()
db.commit()
```

**Update khi disconnect:**
```python
connection.status = 'disconnected'
connection.disconnected_at = datetime.utcnow()
db.commit()
```

**Query active connections:**
```sql
SELECT * FROM connection_status 
WHERE status = 'connected' 
AND org_id = 1
ORDER BY last_seen_at DESC;
```

**Query connections timeout (không có pong > 60s):**
```sql
SELECT * FROM connection_status 
WHERE status = 'connected' 
AND last_pong_at < NOW() - INTERVAL '60 seconds';
```

### 3. Virtual IP Mapping

**Update last_seen_at khi connection active:**
```python
mapping = db.query(VirtualIPMapping).filter(
    VirtualIPMapping.user_id == user_id,
    VirtualIPMapping.org_id == org_id
).first()
if mapping:
    mapping.last_seen_at = datetime.utcnow()
    db.commit()
```

---

## ⚠️ Lưu ý quan trọng

1. **SMTP Password**: Trong production, nên mã hóa `smtp_password` trước khi lưu vào database
2. **Connection Status**: Có thể có nhiều records cho cùng user (nhiều lần connect/disconnect). Cần cleanup các records cũ định kỳ
3. **Performance**: Indexes đã được tạo để tối ưu query, nhưng nếu có nhiều connections, nên có cleanup job để xóa records cũ
4. **Unique Constraint**: `smtp_settings` có unique constraint trên `org_id`, nghĩa là mỗi org chỉ có 1 config (hoặc 1 global config)

---

## 🔍 Các query hữu ích

**Xem tất cả connections đang active:**
```sql
SELECT cs.*, u.email, o.name as org_name
FROM connection_status cs
JOIN "user" u ON cs.user_id = u.id
JOIN organization o ON cs.org_id = o.id
WHERE cs.status = 'connected'
ORDER BY cs.last_seen_at DESC;
```

**Xem connections có thể timeout (không có pong > 60s):**
```sql
SELECT cs.*, u.email
FROM connection_status cs
JOIN "user" u ON cs.user_id = u.id
WHERE cs.status = 'connected'
AND (cs.last_pong_at IS NULL OR cs.last_pong_at < NOW() - INTERVAL '60 seconds');
```

**Xem SMTP config của organization (ưu tiên org, fallback global):**
```sql
SELECT * FROM smtp_settings
WHERE (org_id = 1 OR org_id IS NULL)
AND is_active = true
ORDER BY org_id DESC NULLS LAST
LIMIT 1;
```

**Xem virtual IPs không được dùng trong 24h:**
```sql
SELECT v.*, u.email, o.name as org_name
FROM virtual_ip_mapping v
JOIN "user" u ON v.user_id = u.id
JOIN organization o ON v.org_id = o.id
WHERE v.last_seen_at IS NULL 
OR v.last_seen_at < NOW() - INTERVAL '24 hours';
```

---

## ✅ Checklist sau khi migrate

- [ ] Chạy migration: `alembic upgrade head`
- [ ] Tạo global SMTP config (hoặc per-org configs)
- [ ] Cập nhật code để ghi `connection_status` khi connect/disconnect
- [ ] Cập nhật code để update `last_ping_at`, `last_pong_at`, `last_seen_at`
- [ ] Test ping-pong và disconnect check
- [ ] Setup cleanup job để xóa `connection_status` records cũ (optional)

