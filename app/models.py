from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

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

    # Relationships
    virtual_ips = relationship("VirtualIPMapping", back_populates="user")
    organizations = relationship(
        "Organization", secondary=organization_user, back_populates="users"
    )


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


class VirtualIPMapping(Base):
    __tablename__ = "virtual_ip_mapping"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    virtual_ip = Column(String, nullable=False)
    org_id = Column(Integer, ForeignKey("organization.id"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="virtual_ips")
    organization = relationship("Organization", back_populates="virtual_ips")
