# Signaling Server API

FastAPI backend for P2P signaling server with organization management and virtual IP allocation.

## Features

- **User Authentication**: JWT-based authentication with registration and login
- **Organization Management**: Create and join organizations with subnet management
- **Virtual IP Allocation**: Automatic IP allocation within organization subnets
- **WebSocket Signaling**: Real-time peer discovery, lifecycle notifications, and communication
- **RESTful API**: Complete REST API for all operations

## Installation

1. **Clone repository and setup environment**
   ```bash
   git clone <repository-url>
   cd signaling-server
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment variables**
   Create `.env` file:
   ```env
   DATABASE_URL=postgresql://user:password@localhost/signaling_db
   SECRET_KEY=your-secret-key-here
   ```

3. **Setup database and run**
   ```bash
   createdb signaling_db
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /register` - Register new user
- `POST /login` - Login user and get JWT token

### Organizations
- `POST /organizations` - Create organization (requires auth)
- `GET /organizations` - List user's organizations (requires auth)
- `POST /organizations/{org_id}/join` - Join organization (requires auth)
- `GET /organizations/{org_id}/members` - List organization members (requires auth)

### Virtual IP Management
- `POST /organizations/{org_id}/allocate_ip` - Allocate virtual IP (requires auth)
- `GET /organizations/{org_id}/ips` - List allocated IPs (requires auth)

### WebSocket Signaling
- `WS /ws?token=<jwt_token>` - WebSocket endpoint for peer signaling

## WebSocket API

### Connection

**Endpoint:** `WS /ws/`

**Authentication:** JWT token via query parameter `?token=<jwt_token>` or header `Authorization: Bearer <jwt_token>`

**Connection Flow:**
1. Client connects with JWT token
2. Server authenticates and accepts connection
3. Client sends `register` message (required first message)
4. Server processes registration and returns response
5. Connection maintained for notifications

### Message Types

#### 1. Register (Client → Server)

```json
{
  "type": "register",
  "agent_id": "agent-123",        // Optional
  "public_ip": "203.0.113.1",      // Required
  "public_port": 50000,            // Required
  "relay_ip": "203.0.113.10",      // Optional
  "relay_port": 50001              // Optional
}
```

#### 2. Register Response (Server → Client)

```json
{
  "type": "register_agent_response",
  "status": "registered",
  "virtual_ip": "10.0.0.5",
  "connection_id": "550e8400-e29b-41d4-a716-446655440000",
  "existing_peers": [
    {
      "peer_id": "peer-device-002",
      "user_id": 2,
      "email": "user2@example.com",
      "agent_id": "peer-device-002",
      "public_ip": "203.0.113.2",
      "public_port": 50000,
      "relay_ip": "203.0.113.11",
      "relay_port": 50001,
      "virtual_ip": "10.0.0.6"
    }
  ]
}
```

**Note:** `existing_peers` chỉ chứa peers cùng subnet với peer mới.

#### 3. Peer Online Notification (Server → Client)

```json
{
  "type": "peer_online",
  "peer": {
    "peer_id": "peer-device-003",
    "user_id": 3,
    "email": "user3@example.com",
    "agent_id": "peer-device-003",
    "public_ip": "203.0.113.3",
    "public_port": 50000,
    "relay_ip": "203.0.113.12",
    "relay_port": 50001,
    "virtual_ip": "10.0.0.7"
  }
}
```

**Note:** Chỉ broadcast đến peers cùng subnet.

#### 4. Peer Offline Notification (Server → Client)

```json
{
  "type": "peer_offline",
  "peer_id": "peer-device-003",
  "user_id": 3,
  "virtual_ip": "10.0.0.7"
}
```

**Note:** 
- Tự động gửi khi peer disconnect hoặc bị remove khỏi cache
- Chỉ broadcast đến peers cùng subnet
- Client nên xóa peer khỏi cache và dừng P2P connections

#### 5. Error Messages (Server → Client)

```json
{
  "error": "Error message here"
}
```

**Common Errors:**
- `"No token provided"` - Thiếu token
- `"Invalid token"` - Token không hợp lệ
- `"First message must be register"` - Message đầu tiên không phải register
- `"Missing required fields: public_ip, public_port"` - Thiếu required fields
- `"User not member of any organization"` - User không thuộc organization nào
- `"No virtual IP allocated for user in any organization"` - Chưa allocate virtual IP
- `"Registration failed"` - Lỗi registration

### Subnet Filtering

Server tự động filter peers theo subnet:
- **Registration Response**: Chỉ trả về peers cùng subnet
- **Peer Online/Offline Notifications**: Chỉ broadcast đến peers cùng subnet

**Ví dụ:** Organization subnet `10.0.0.0/24`
- Peer A: `10.0.0.5` ✅ (cùng subnet)
- Peer B: `10.0.0.6` ✅ (cùng subnet)
- Peer C: `192.168.1.5` ❌ (khác subnet)

Peer A chỉ nhận thông tin về Peer B, không nhận Peer C.

### Connection Management

- **Auto-reconnect**: Client nên implement auto-reconnect khi connection bị drop
- **Error Handling**: Handle tất cả error messages và đóng connection gracefully
- **Offline Cleanup**: Server tự động cleanup peers offline khỏi cache và broadcast `peer_offline`

## Testing

```bash
pytest tests/
```

## Development

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key for token signing

### Security Notes
- Change default SECRET_KEY in production
- Configure CORS origins properly
- Use HTTPS in production
- Implement rate limiting

## License

This project is part of PBL4 - University of Technology.
