# MVP Signaling Server

Một signaling server đơn giản được xây dựng bằng FastAPI để hỗ trợ WebRTC peer-to-peer connections cho MVP Agent.

## Tính năng

- **WebSocket Signaling**: Hỗ trợ đầy đủ WebRTC signaling protocol
- **FastAPI**: Framework hiện đại, nhanh và dễ sử dụng
- **CORS Support**: Hỗ trợ cross-origin requests
- **Real-time Communication**: WebSocket cho signaling real-time
- **Simple Architecture**: Kiến trúc đơn giản, dễ hiểu và maintain

## Cài đặt

### Yêu cầu hệ thống

- Python 3.8+
- pip hoặc conda

### Cài đặt dependencies

```bash
pip install -r requirements.txt
```

## Sử dụng

### Chạy server

```bash
# Chạy với uvicorn (development)
python main.py

# Hoặc chạy trực tiếp với uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Server sẽ chạy tại: `http://localhost:8000`

### API Endpoints

#### Health Check

```
GET /
```

Trả về thông tin server và số lượng clients đang kết nối.

#### Status

```
GET /status
```

Trả về trạng thái chi tiết của server.

#### WebSocket Signaling

```
WS /ws/{client_id}
```

Endpoint chính cho WebRTC signaling.

## Signaling Protocol

Server hỗ trợ các loại message sau:

### 1. Register

```json
{
  "type": "register",
  "id": "client-123",
  "token": "optional-token"
}
```

### 2. Offer

```json
{
  "type": "offer",
  "from": "alice",
  "to": "bob",
  "sdp": "v=0\r\no=alice..."
}
```

### 3. Answer

```json
{
  "type": "answer",
  "from": "bob",
  "to": "alice",
  "sdp": "v=0\r\no=bob..."
}
```

### 4. ICE Candidate

```json
{
  "type": "candidate",
  "from": "alice",
  "to": "bob",
  "candidate": {
    "candidate": "candidate:1 1 UDP 2113667326 192.168.1.100 54400 typ host",
    "sdpMid": "0",
    "sdpMLineIndex": 0
  }
}
```

### 5. Bye

```json
{
  "type": "bye",
  "from": "alice",
  "to": "bob"
}
```

## Kết nối với MVP Agent

### Cấu hình Agent

Tạo file `.env` trong thư mục Agent:

```bash
# Required
AGENT_ID=your-unique-agent-id
SIGNALING_URL=ws://localhost:8000/ws/your-unique-agent-id

# Optional
MODE=chat
DATA_CHANNEL_LABEL=mvp
```

### Chạy Agent

```bash
# Terminal 1 - Agent A (Answerer)
cd Agent
export AGENT_ID=alice
export SIGNALING_URL=ws://localhost:8000/ws/alice
export MODE=chat
python cli.py listen

# Terminal 2 - Agent B (Offerer)
cd Agent
export AGENT_ID=bob
export SIGNALING_URL=ws://localhost:8000/ws/bob
export MODE=chat
python cli.py connect alice
```

## Kiến trúc

```
┌─────────────────┐    WebSocket     ┌─────────────────┐
│   Agent A       │◄────────────────►│  Signaling      │
│                 │   (Control)      │  Server         │
│  ┌─────────────┐│                  │                 │
│  │ Signaling   ││                  └─────────────────┘
│  │ Client      ││
│  └─────────────┘│
│                 │
│  ┌─────────────┐│    WebRTC        ┌─────────────────┐
│  │ Agent Core  ││◄────────────────►│   Agent B       │
│  │             ││   (Data)         │                 │
│  │ ┌─────────┐ ││                  │  ┌─────────────┐│
│  │ │Transport│ ││                  │  │ Agent Core  ││
│  │ └─────────┘ ││                  │  │             ││
│  └─────────────┘│                  │  │ ┌─────────┐ ││
└─────────────────┘                  │  │ │Transport│ ││
                                     │  │ └─────────┘ ││
                                     │  └─────────────┘│
                                     └─────────────────┘
```

## Development

### Cấu trúc project

```
Signaling Server/
├── main.py              # Main FastAPI application
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

### Chạy trong development mode

```bash
# Với auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Với debug logging
uvicorn main:app --reload --log-level debug
```

### Testing

```bash
# Test WebSocket connection
python -c "
import asyncio
import websockets
import json

async def test():
    uri = 'ws://localhost:8000/ws/test-client'
    async with websockets.connect(uri) as websocket:
        # Register
        await websocket.send(json.dumps({
            'type': 'register',
            'id': 'test-client'
        }))
        response = await websocket.recv()
        print('Response:', response)

asyncio.run(test())
"
```

## Troubleshooting

### Lỗi thường gặp

1. **Port đã được sử dụng**

   ```bash
   # Thay đổi port
   uvicorn main:app --port 8001
   ```

2. **CORS errors**

   - Server đã cấu hình CORS cho tất cả origins
   - Kiểm tra firewall settings

3. **WebSocket connection failed**
   - Kiểm tra URL signaling trong Agent config
   - Đảm bảo server đang chạy

### Logs

Server sử dụng Python logging. Để xem logs chi tiết:

```bash
# Chạy với debug level
uvicorn main:app --log-level debug
```

## Production Deployment

### Docker (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY main.py .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

```bash
# Production settings
export HOST=0.0.0.0
export PORT=8000
export LOG_LEVEL=info
```

## License

MIT License - Xem file LICENSE để biết thêm chi tiết.



