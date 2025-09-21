from pydantic import BaseModel, EmailStr
from typing import List, Optional


# User schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


# Organization schemas
class OrganizationCreate(BaseModel):
    name: str
    subnet: str


class OrganizationResponse(BaseModel):
    id: int
    name: str
    subnet: str

    class Config:
        from_attributes = True


class OrganizationMember(BaseModel):
    user_id: int
    email: str

    class Config:
        from_attributes = True


class JoinOrganizationResponse(BaseModel):
    status: str


# Virtual IP schemas
class AllocateIPRequest(BaseModel):
    user_id: Optional[int] = None


class AllocateIPResponse(BaseModel):
    user_id: int
    org_id: int
    virtual_ip: str

    class Config:
        from_attributes = True


class VirtualIPInfo(BaseModel):
    user_id: int
    virtual_ip: str

    class Config:
        from_attributes = True


# WebSocket schemas
class RegisterAgentRequest(BaseModel):
    type: str = "register"
    agent_id: str
    public_ip: str
    public_port: int
    org_id: int


class PeerInfo(BaseModel):
    user_id: int
    email: str
    agent_id: str
    public_ip: str
    public_port: int
    virtual_ip: str


class RegisterAgentResponse(BaseModel):
    status: str
    peers: List[PeerInfo]


class PeerOnlineNotification(BaseModel):
    type: str = "peer_online"
    user_id: int
    email: str
    agent_id: str
    public_ip: str
    public_port: int
    virtual_ip: str
