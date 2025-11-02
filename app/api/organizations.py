from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..db import get_db
from ..models import User, Organization, organization_user
from ..schemas import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationMember,
    JoinOrganizationResponse,
)
from ..utils import verify_token, validate_subnet
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
# """get current user from token"""    
    token = credentials.credentials
    payload = verify_token(token)
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user


@router.post("/organizations", response_model=OrganizationResponse)
def create_organization(
    org: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new organization"""
    # Validate subnet format
    if not validate_subnet(org.subnet):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid subnet format"
        )

    # Create organization
    db_org = Organization(name=org.name, subnet=org.subnet)

    db.add(db_org)
    db.commit()
    db.refresh(db_org)

    # Add creator as member
    db_org.users.append(current_user)
    db.commit()

    return OrganizationResponse(id=db_org.id, name=db_org.name, subnet=db_org.subnet)


@router.get("/organizations", response_model=List[OrganizationResponse])
def list_organizations(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """List organizations that the user is a member of"""
    return current_user.organizations


@router.post("/organizations/{org_id}/join", response_model=JoinOrganizationResponse)
def join_organization(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Join an organization"""
    # Check if organization exists
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    # Check if user is already a member
    if current_user in org.users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this organization",
        )

    # Add user to organization
    org.users.append(current_user)
    db.commit()

    return JoinOrganizationResponse(status="joined")


@router.get("/organizations/{org_id}/members", response_model=List[OrganizationMember])
def list_organization_members(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List members of an organization"""
    # Check if organization exists
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    # Check if user is a member
    if current_user not in org.users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this organization",
        )

    # Return members
    members = []
    for user in org.users:
        members.append(OrganizationMember(user_id=user.id, email=user.email))

    return members
