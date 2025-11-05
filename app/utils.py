import logging
import ipaddress
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import os
from dotenv import load_dotenv

load_dotenv()

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_next_available_ip(subnet: str, used_ips: list) -> Optional[str]:
    """Get next available IP in subnet"""
    try:
        network = ipaddress.IPv4Network(subnet, strict=False)

        # Convert used IPs to IPv4Address objects
        used_addresses = []
        for ip_str in used_ips:
            try:
                used_addresses.append(ipaddress.IPv4Address(ip_str))
            except ipaddress.AddressValueError:
                continue

        # Find first available IP (skip network and broadcast addresses)
        for host in network.hosts():
            if host not in used_addresses:
                return str(host)

        return None
    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError) as e:
        logger.error(f"Invalid subnet {subnet}: {e}")
        return None


def validate_subnet(subnet: str) -> bool:
    """Validate if subnet string is valid"""
    try:
        ipaddress.IPv4Network(subnet, strict=False)
        return True
    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError):
        return False


def log_info(message: str):
    """Log info message"""
    logger.info(message)


def log_error(message: str):
    """Log error message"""
    logger.error(message)


def is_same_subnet(ip1: str, ip2: str, subnet: str) -> bool:
    """Check if two IPs are in the same subnet"""
    try:
        network = ipaddress.IPv4Network(subnet, strict=False)
        addr1 = ipaddress.IPv4Address(ip1)
        addr2 = ipaddress.IPv4Address(ip2)
        
        # Check if both IPs are in the network
        return addr1 in network and addr2 in network
    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError) as e:
        logger.error(f"Error checking subnet: {e}")
        return False