from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional

Base = declarative_base()

# Association table for many-to-many relationship between users and organizations
organization_user = Table(
    "organization_user",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("user.id"), primary_key=True),
    Column("org_id", Integer, ForeignKey("organization.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False, index=True)

    # Relationships
    virtual_ips = relationship("VirtualIPMapping", back_populates="user")
    organizations = relationship(
        "Organization", secondary=organization_user, back_populates="users"
    )
    connection_statuses = relationship("ConnectionStatus", back_populates="user")


class OTPVerification(Base):
    __tablename__ = "otp_verification"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, index=True)
    otp_code = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    verified = Column(Boolean, default=False, nullable=False)


class Organization(Base):
    __tablename__ = "organization"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    subnet = Column(String, nullable=False)

    # Relationships
    users = relationship(
        "User", secondary=organization_user, back_populates="organizations"
    )
    virtual_ips = relationship("VirtualIPMapping", back_populates="organization")
    smtp_settings = relationship("SMTPSettings", back_populates="organization", uselist=False)
    connection_statuses = relationship("ConnectionStatus", back_populates="organization")


class VirtualIPMapping(Base):
    __tablename__ = "virtual_ip_mapping"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    virtual_ip = Column(String, nullable=False)
    org_id = Column(Integer, ForeignKey("organization.id"), nullable=False)
    last_seen_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="virtual_ips")
    organization = relationship("Organization", back_populates="virtual_ips")


class SMTPSettings(Base):
    __tablename__ = "smtp_settings"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organization.id", ondelete="CASCADE"), nullable=True)
    smtp_server = Column(String, nullable=False)
    smtp_port = Column(Integer, nullable=False)
    smtp_username = Column(String, nullable=False)
    smtp_password = Column(String, nullable=False)  # Should be encrypted in production
    from_email = Column(String, nullable=False)
    use_tls = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="smtp_settings")


class ConnectionStatus(Base):
    __tablename__ = "connection_status"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    org_id = Column(Integer, ForeignKey("organization.id", ondelete="CASCADE"), nullable=False)
    virtual_ip = Column(String, nullable=False, index=True)
    peer_id = Column(String, nullable=True)
    connection_id = Column(String, nullable=True)
    public_ip = Column(String, nullable=True)
    public_port = Column(Integer, nullable=True)
    status = Column(String, default="connected", nullable=False, index=True)  # connected, disconnected, timeout
    connected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    disconnected_at = Column(DateTime, nullable=True)
    last_ping_at = Column(DateTime, nullable=True)
    last_pong_at = Column(DateTime, nullable=True)
    last_seen_at = Column(DateTime, default=datetime.utcnow, nullable=True, index=True)

    # Relationships
    user = relationship("User", back_populates="connection_statuses")
    organization = relationship("Organization", back_populates="connection_statuses")
