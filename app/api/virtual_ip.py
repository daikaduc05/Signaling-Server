from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..db import get_db
from ..models import User, Organization
from ..schemas import AllocateIPRequest, AllocateIPResponse, VirtualIPInfo
from ..utils import verify_token
from ..services import allocate_virtual_ip, get_organization_ips
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Get current authenticated user"""
    token = credentials.credentials
    payload = verify_token(token)
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user


@router.post("/organizations/{org_id}/allocate_ip", response_model=AllocateIPResponse)
def allocate_ip(
    org_id: int,
    request: AllocateIPRequest = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Allocate virtual IP for a user in an organization"""
    # Check if organization exists
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    # Check if user is a member of the organization
    if current_user not in org.users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this organization",
        )

    # Determine target user (default to current user if not specified)
    target_user_id = request.user_id if request and request.user_id else current_user.id

    # If requesting IP for another user, check if current user has permission
    if target_user_id != current_user.id:
        # For now, only allow users to allocate IPs for themselves
        # In a real system, you might have admin roles
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only allocate IP for yourself",
        )

    # Allocate IP
    virtual_ip = allocate_virtual_ip(db, org_id, target_user_id)
    if not virtual_ip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No available IPs in this organization's subnet",
        )

    return AllocateIPResponse(
        user_id=target_user_id, org_id=org_id, virtual_ip=virtual_ip
    )


@router.get("/organizations/{org_id}/ips", response_model=List[VirtualIPInfo])
def list_allocated_ips(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all allocated IPs in an organization"""
    # Check if organization exists
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    # Check if user is a member of the organization
    if current_user not in org.users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this organization",
        )

    # Get allocated IPs
    ips = get_organization_ips(db, org_id)
    return [VirtualIPInfo(**ip) for ip in ips]
