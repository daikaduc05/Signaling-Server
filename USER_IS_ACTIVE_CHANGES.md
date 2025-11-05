# Thêm cột `is_active` vào bảng `user`

## 📋 Tổng quan

Đã thêm cột `is_active` vào bảng `user` để đánh dấu user đã xác minh Gmail hay chưa. User chỉ có thể sử dụng hệ thống sau khi xác minh email thành công.

## ✅ Thay đổi

### 1. **Database Migration**

**File:** `alembic/versions/add_user_is_active.py`

- Thêm cột `is_active` (Boolean, default=False) vào bảng `user`
- Tự động set `is_active = true` cho các user hiện có đã có `email_verified = true`
- Tạo index `ix_user_is_active` để tối ưu query `WHERE is_active = true`

**Migration SQL tương đương:**
```sql
ALTER TABLE "user" ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT false;
UPDATE "user" SET is_active = true WHERE email_verified = true;
CREATE INDEX ix_user_is_active ON "user"(is_active);
```

### 2. **Model Update**

**File:** `app/models.py`

Thêm cột vào class `User`:
```python
is_active = Column(Boolean, default=False, nullable=False, index=True)
```

### 3. **Logic Update**

#### a. **Registration (Verify OTP)**
**File:** `app/api/auth.py`

Khi user verify OTP thành công → tạo user với `is_active=True`:
```python
db_user = User(
    email=request.email,
    password=hashed_password,
    email_verified=True,
    is_active=True  # User đã xác minh Gmail → cho phép hoạt động
)
```

#### b. **Login**
**File:** `app/api/auth.py`

Kiểm tra `is_active` trước khi cho phép login:
```python
if not db_user.is_active:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Account is not active. Please verify your email first.",
    )
```

#### c. **WebSocket Authentication**
**File:** `app/api/signaling_ws.py`

Kiểm tra `is_active` trong `get_user_from_token()`:
```python
if not user.is_active:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Account is not active. Please verify your email first.",
    )
```

#### d. **API Endpoints**
**Files:** `app/api/virtual_ip.py`, `app/api/organizations.py`

Tất cả các endpoint đều kiểm tra `is_active` trong `get_current_user()`.

### 4. **Schema Update**

**File:** `app/schemas.py`

Thêm `is_active` vào `UserResponse`:
```python
class UserResponse(BaseModel):
    id: int
    email: str
    email_verified: bool = False
    is_active: bool = False  # ← Mới thêm
```

## 🔄 Flow hoạt động

```
1. User request OTP
   ↓
2. Nhận OTP qua email
   ↓
3. Verify OTP + Register
   ↓
4. Tạo user với:
   - email_verified = True
   - is_active = True  ← Được set ở đây
   ↓
5. User có thể:
   - Login ✅
   - Sử dụng WebSocket ✅
   - Truy cập các API ✅
```

## 📊 So sánh `email_verified` vs `is_active`

| Cột | Mục đích | Khi nào set True |
|-----|----------|------------------|
| `email_verified` | Đánh dấu email đã verify qua OTP | Khi verify OTP thành công |
| `is_active` | Đánh dấu user có thể sử dụng hệ thống | Khi verify OTP thành công |

**Hiện tại:** Cả 2 đều được set cùng lúc khi verify OTP.

**Lý do giữ cả 2:**
- `email_verified`: Technical flag - email đã được verify
- `is_active`: Business logic flag - user có thể hoạt động (có thể mở rộng sau: ban user, suspend, etc.)

## 🔍 Query Examples

**Tìm tất cả user đang active:**
```sql
SELECT * FROM "user" WHERE is_active = true;
```

**Tìm user chưa verify (chưa active):**
```sql
SELECT * FROM "user" WHERE is_active = false;
```

**Tìm user đã verify email nhưng chưa active (nếu có):**
```sql
SELECT * FROM "user" WHERE email_verified = true AND is_active = false;
```

## ⚙️ Chạy Migration

```bash
# Upgrade
alembic upgrade head

# Rollback (nếu cần)
alembic downgrade -1
```

## ✅ Checklist

- [x] Migration file đã tạo
- [x] Model đã cập nhật
- [x] Registration logic đã cập nhật (set `is_active=True`)
- [x] Login đã kiểm tra `is_active`
- [x] WebSocket authentication đã kiểm tra `is_active`
- [x] Tất cả API endpoints đã kiểm tra `is_active`
- [x] Schema đã cập nhật
- [x] Index đã tạo để tối ưu query

## 🎯 Lợi ích

1. **Đơn giản**: Chỉ cần thêm 1 cột, không cần tạo bảng mới
2. **Hiệu quả**: Index được tạo để query nhanh
3. **Bảo mật**: User chưa verify không thể sử dụng hệ thống
4. **Dễ mở rộng**: Có thể dùng `is_active` để ban/suspend user sau này
5. **Backward compatible**: User hiện có đã verify sẽ tự động có `is_active=true`

