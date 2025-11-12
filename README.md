# Signaling Server API

FastAPI backend for P2P signaling server with organization management and virtual IP allocation.

## Features

- **User Authentication**: JWT-based authentication with registration and login
- **Organization Management**: Create and join organizations with subnet management
- **Virtual IP Allocation**: Automatic IP allocation within organization subnets
- **WebSocket Signaling**: Real-time peer discovery, lifecycle notifications, and communication
- **RESTful API**: Complete REST API for all operations

## Project Structure

```
signaling-server/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── api/                 # API endpoints
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── organizations.py # Organization management
│   │   ├── virtual_ip.py    # Virtual IP management
│   │   └── signaling_ws.py  # WebSocket signaling
│   ├── models.py            # SQLAlchemy database models
│   ├── schemas.py           # Pydantic schemas
│   ├── services.py          # Business logic
│   ├── db.py                # Database configuration
│   └── utils.py             # Utility functions
├── tests/                   # Test files
│   └── test_ws.py
├── requirements.txt         # Python dependencies
└── README.md
```

## Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd signaling-server
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:

   ```env
   DATABASE_URL=postgresql://user:password@localhost/signaling_db
   SECRET_KEY=your-secret-key-here
   ```

5. **Set up database**

   - Install PostgreSQL
   - Create database: `createdb signaling_db`
   - The application will automatically create tables on startup

6. **Run the application**
   ```bash
   python -m app.main
   ```
   Or using uvicorn directly:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## API Documentation

Once the server is running, visit:

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

Xem chi tiết trong phần [WebSocket API Documentation](#websocket-api-documentation) bên dưới.

## Usage Examples

### 1. Register and Login

```bash
# Register
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Login
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

### 2. Create Organization

```bash
curl -X POST "http://localhost:8000/organizations" \
  -H "Authorization: Bearer <your-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Organization", "subnet": "10.0.0.0/24"}'
```

### 3. Allocate Virtual IP

```bash
curl -X POST "http://localhost:8000/organizations/1/allocate_ip" \
  -H "Authorization: Bearer <your-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## WebSocket API Documentation

### Connection

**Endpoint:** `WS /ws/`

**Authentication:** JWT token có thể được gửi qua:
1. Query parameter: `ws://localhost:8000/ws?token=<jwt_token>`
2. Authorization header: `Authorization: Bearer <jwt_token>`

**Connection Flow:**
1. Client kết nối WebSocket với JWT token
2. Server xác thực token và accept connection
3. Client gửi registration message (bắt buộc là message đầu tiên)
4. Server xử lý registration và trả về response
5. Connection được maintain để nhận notifications

### Message Types

#### 1. Register Message (Client → Server)

**Type:** `register`

**Description:** Message đăng ký agent với signaling server. Đây là message bắt buộc đầu tiên sau khi kết nối.

**Request Format:**
```json
{
  "type": "register",
  "agent_id": "agent-123",          // Optional: ID của agent
  "public_ip": "203.0.113.1",        // Required: Public IP từ STUN server
  "public_port": 50000,              // Required: Public port từ STUN server
  "relay_ip": "203.0.113.10",        // Optional: Relay IP từ TURN server
  "relay_port": 50001                 // Optional: Relay port từ TURN server
}
```

**Field Descriptions:**
- `type`: Luôn là `"register"`
- `agent_id`: (Optional) ID tùy chỉnh của agent. Nếu không có, server sẽ tự generate
- `public_ip`: (Required) Public IP address của peer từ STUN discovery
- `public_port`: (Required) Public port của peer từ STUN discovery
- `relay_ip`: (Optional) Relay IP address từ TURN server nếu sử dụng relay
- `relay_port`: (Optional) Relay port từ TURN server nếu sử dụng relay

**Example:**
```json
{
  "type": "register",
  "agent_id": "peer-device-001",
  "public_ip": "203.0.113.1",
  "public_port": 50000,
  "relay_ip": "203.0.113.10",
  "relay_port": 50001
}
```

#### 2. Register Agent Response (Server → Client)

**Type:** `register_agent_response`

**Description:** Response xác nhận registration thành công, bao gồm virtual IP được assign và danh sách peers cùng subnet.

**Response Format:**
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

**Field Descriptions:**
- `type`: Luôn là `"register_agent_response"`
- `status`: Trạng thái registration, thường là `"registered"`
- `virtual_ip`: Virtual IP được assign cho peer trong organization subnet
- `connection_id`: Unique connection ID được generate bởi server
- `existing_peers`: Danh sách các peers hiện đang online **cùng subnet mask** với peer mới
  - Chỉ include peers có virtual IP cùng subnet
  - Peers khác subnet không được include

**Peer Object Structure:**
- `peer_id`: ID của peer (agent_id nếu có, hoặc auto-generated)
- `user_id`: User ID của peer
- `email`: Email của user
- `agent_id`: Agent ID (optional)
- `public_ip`: Public IP của peer
- `public_port`: Public port của peer
- `relay_ip`: Relay IP của peer (optional)
- `relay_port`: Relay port của peer (optional)
- `virtual_ip`: Virtual IP của peer trong subnet

**Lưu ý:** Client nên lưu thông tin các peers trong `existing_peers` vào bộ nhớ tạm để sử dụng cho P2P connection sau này.

#### 3. Peer Online Notification (Server → Client)

**Type:** `peer_online`

**Description:** Notification khi có peer mới online cùng subnet. Server chỉ broadcast đến các peers cùng subnet.

**Notification Format:**
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

**Field Descriptions:**
- `type`: Luôn là `"peer_online"`
- `peer`: Object chứa thông tin peer mới online

**Lưu ý:** 
- Chỉ peers cùng subnet nhận được notification này
- Client nên lưu thông tin peer mới vào bộ nhớ tạm

#### 4. Peer Offline Notification (Server → Client)

**Type:** `peer_offline`

**Description:** Notification khi một peer cùng subnet rời khỏi signaling server. Server tự động broadcast khi client chủ động disconnect hoặc bị drop khỏi cache (ví dụ: lỗi gửi message).

**Notification Format:**
```json
{
  "type": "peer_offline",
  "peer_id": "peer-device-003",
  "user_id": 3,
  "virtual_ip": "10.0.0.7"
}
```

**Field Descriptions:**
- `type`: Luôn là `"peer_offline"`
- `peer_id`: ID của peer vừa offline (có thể được generate tự động)
- `user_id`: User ID tương ứng
- `virtual_ip`: Virtual IP của peer trong subnet

**Lưu ý:**
- Notification chỉ gửi đến peers **cùng subnet**
- Client nên xóa peer khỏi bộ nhớ tạm và dừng tất cả kết nối P2P liên quan
- Nếu server phát hiện peer không còn nhận message (ví dụ lỗi gửi), notification vẫn được gửi cho các peers còn lại

#### 5. Error Messages (Server → Client)

**Error Format:**
```json
{
  "error": "Error message here"
}
```

**Common Error Messages:**
- `"No token provided"` - Không có token trong request
- `"Invalid token"` - Token không hợp lệ
- `"First message must be register"` - Message đầu tiên không phải là register
- `"Invalid JSON"` - JSON format không hợp lệ
- `"Missing required fields: public_ip, public_port"` - Thiếu required fields
- `"User not member of any organization"` - User không thuộc organization nào
- `"No virtual IP allocated for user in any organization"` - User chưa được allocate virtual IP
- `"Registration failed"` - Lỗi trong quá trình registration

### Connection Flow Example

```javascript
// 1. Kết nối WebSocket với JWT token
const ws = new WebSocket("ws://localhost:8000/ws?token=<jwt_token>");

ws.onopen = function() {
  console.log("WebSocket connected");
  
  // 2. Gửi registration message (bắt buộc là message đầu tiên)
  const registerMessage = {
    type: "register",
    agent_id: "my-agent-001",
    public_ip: "203.0.113.1",
    public_port: 50000,
    relay_ip: "203.0.113.10",
    relay_port: 50001
  };
  
  ws.send(JSON.stringify(registerMessage));
};

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  
  // 3. Xử lý registration response
  if (data.type === "register_agent_response") {
    console.log("Registered successfully!");
    console.log("Virtual IP:", data.virtual_ip);
    console.log("Connection ID:", data.connection_id);
    console.log("Existing peers:", data.existing_peers);
    
    // Lưu thông tin peers vào bộ nhớ tạm
    storePeersInMemory(data.existing_peers);
  }
  
  // 4. Xử lý peer online notification
  else if (data.type === "peer_online") {
    console.log("New peer online:", data.peer);
    
    // Lưu peer mới vào bộ nhớ tạm
    addPeerToMemory(data.peer);
  }
  
  // 5. Xử lý error messages
  else if (data.error) {
    console.error("Error:", data.error);
  }
};

ws.onerror = function(error) {
  console.error("WebSocket error:", error);
};

ws.onclose = function() {
  console.log("WebSocket disconnected");
};
```

### Subnet Filtering

**Quan trọng:** Server tự động filter peers theo subnet mask:

1. **Registration Response**: Chỉ trả về peers có virtual IP cùng subnet với peer mới
2. **Peer Online Notification**: Chỉ broadcast đến peers cùng subnet

**Ví dụ:**
- Organization subnet: `10.0.0.0/24`
- Peer A virtual IP: `10.0.0.5` ✅ (cùng subnet)
- Peer B virtual IP: `10.0.0.6` ✅ (cùng subnet)
- Peer C virtual IP: `192.168.1.5` ❌ (khác subnet)

Khi Peer A register:
- Chỉ nhận Peer B trong `existing_peers`
- Peer C không được include

Khi Peer B online:
- Peer A nhận được `peer_online` notification
- Peer C không nhận được notification

### Keep-Alive & Connection Management

- **Connection Timeout**: Connection sẽ timeout sau một khoảng thời gian không hoạt động
- **Auto-reconnect**: Client nên implement auto-reconnect logic khi connection bị drop
- **Error Handling**: Client nên handle tất cả error messages và đóng connection gracefully nếu cần
- **Offline Cleanup**: Server tự động cleanup peers offline khỏi cache và broadcast `peer_offline` để các clients đồng bộ trạng thái

### Example: Python Client

```python
import asyncio
import websockets
import json

async def connect_and_register(token, public_ip, public_port):
    uri = f"ws://localhost:8000/ws?token={token}"
    
    async with websockets.connect(uri) as websocket:
        # Send registration message
        register_msg = {
            "type": "register",
            "agent_id": "python-agent-001",
            "public_ip": public_ip,
            "public_port": public_port,
            "relay_ip": None,
            "relay_port": None
        }
        await websocket.send(json.dumps(register_msg))
        
        # Listen for messages
        async for message in websocket:
            data = json.loads(message)
            
            if data.get("type") == "register_agent_response":
                print(f"Registered! Virtual IP: {data['virtual_ip']}")
                print(f"Connection ID: {data['connection_id']}")
                print(f"Existing peers: {len(data['existing_peers'])}")
                
                # Store peers in memory
                for peer in data['existing_peers']:
                    print(f"  - Peer: {peer['peer_id']} ({peer['virtual_ip']})")
            
            elif data.get("type") == "peer_online":
                print(f"New peer online: {data['peer']['peer_id']}")
            
            elif data.get("error"):
                print(f"Error: {data['error']}")

# Usage
asyncio.run(connect_and_register(
    token="<jwt_token>",
    public_ip="203.0.113.1",
    public_port=50000
))
```

## Testing

Run tests with pytest:

```bash
pytest tests/
```

## Development

### Database Migrations

The application uses SQLAlchemy with automatic table creation. For production, consider using Alembic for migrations.

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key for token signing

### Security Notes

- Change the default SECRET_KEY in production
- Configure CORS origins properly for production
- Use HTTPS in production
- Implement proper rate limiting

## License

This project is part of PBL4 - University of Technology.
