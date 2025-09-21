# Signaling Server API

FastAPI backend for P2P signaling server with organization management and virtual IP allocation.

## Features

- **User Authentication**: JWT-based authentication with registration and login
- **Organization Management**: Create and join organizations with subnet management
- **Virtual IP Allocation**: Automatic IP allocation within organization subnets
- **WebSocket Signaling**: Real-time peer discovery and communication
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

### 4. WebSocket Connection

```javascript
const ws = new WebSocket("ws://localhost:8000/ws?token=<your-jwt-token>");

ws.onopen = function () {
  // Register agent
  ws.send(
    JSON.stringify({
      type: "register",
      agent_id: "agent-123",
      public_ip: "1.2.3.4",
      public_port: 50000,
      org_id: 1,
    })
  );
};

ws.onmessage = function (event) {
  const data = JSON.parse(event.data);
  console.log("Received:", data);
};
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
