from sqlalchemy.orm import Session
from .models import User, Organization, VirtualIPMapping
from .utils import get_next_available_ip, log_info, log_error
from typing import List, Optional


def allocate_virtual_ip(db: Session, org_id: int, user_id: int) -> Optional[str]:
    #"""Allocate a virtual IP for a user in an organization"""
    # Get organization
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        return None

    # Check if user is already allocated an IP in this org
    existing_mapping = (
        db.query(VirtualIPMapping)
        .filter(VirtualIPMapping.user_id == user_id, VirtualIPMapping.org_id == org_id)
        .first()
    )

    if existing_mapping:
        return existing_mapping.virtual_ip

    # Get all used IPs in this organization
    used_ips = (
        db.query(VirtualIPMapping.virtual_ip)
        .filter(VirtualIPMapping.org_id == org_id)
        .all()
    )
    used_ip_list = [ip[0] for ip in used_ips]

    # Get next available IP
    next_ip = get_next_available_ip(org.subnet, used_ip_list)
    if not next_ip:
        log_error(f"No available IPs in subnet {org.subnet} for org {org_id}")
        return None

    # Create mapping
    mapping = VirtualIPMapping(user_id=user_id, org_id=org_id, virtual_ip=next_ip)

    db.add(mapping)
    db.commit()
    db.refresh(mapping)

    log_info(f"Allocated IP {next_ip} to user {user_id} in org {org_id}")
    return next_ip


def get_organization_ips(db: Session, org_id: int) -> List[dict]:
    """Get all allocated IPs in an organization"""
    mappings = (
        db.query(VirtualIPMapping).filter(VirtualIPMapping.org_id == org_id).all()
    )

    return [
        {"user_id": mapping.user_id, "virtual_ip": mapping.virtual_ip}
        for mapping in mappings
    ]


def get_user_virtual_ip(db: Session, user_id: int, org_id: int) -> Optional[str]:
    """Get user's virtual IP in a specific organization"""
    mapping = (
        db.query(VirtualIPMapping)
        .filter(VirtualIPMapping.user_id == user_id, VirtualIPMapping.org_id == org_id)
        .first()
    )

    return mapping.virtual_ip if mapping else None
