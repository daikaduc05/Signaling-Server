from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..db import get_db
from ..models import User, OTPVerification
from ..schemas import (
    UserCreate, UserResponse, UserLogin, Token,
    RequestOTPRequest, RequestOTPResponse,
    VerifyOTPRequest, VerifyOTPResponse
)
from ..utils import verify_password, get_password_hash, create_access_token
from ..email_service import generate_otp, send_otp_email
from datetime import timedelta, datetime

router = APIRouter()

# OTP expiration time: 10 minutes
OTP_EXPIRATION_MINUTES = 10


@router.post("/request-otp", response_model=RequestOTPResponse)
def request_otp(request: RequestOTPRequest, db: Session = Depends(get_db)):
    """
    Request OTP code for email verification during registration
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Generate OTP code
    otp_code = generate_otp()
    
    # Calculate expiration time
    expires_at = datetime.utcnow() + timedelta(minutes=OTP_EXPIRATION_MINUTES)
    
    # Delete old unverified OTPs for this email
    db.query(OTPVerification).filter(
        and_(
            OTPVerification.email == request.email,
            OTPVerification.verified == False
        )
    ).delete()
    
    # Create new OTP record
    otp_record = OTPVerification(
        email=request.email,
        otp_code=otp_code,
        expires_at=expires_at,
        verified=False
    )
    
    db.add(otp_record)
    db.commit()
    
    # Send OTP via email
    email_sent = send_otp_email(request.email, otp_code)
    
    if not email_sent:
        # Rollback OTP record if email failed
        db.delete(otp_record)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP email. Please try again later."
        )
    
    return RequestOTPResponse(
        message="OTP code has been sent to your email",
        expires_in=OTP_EXPIRATION_MINUTES * 60
    )


@router.post("/verify-otp-and-register", response_model=VerifyOTPResponse)
def verify_otp_and_register(
    request: VerifyOTPRequest,
    db: Session = Depends(get_db)
):
    """
    Verify OTP code and complete user registration
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Find valid OTP record
    otp_record = db.query(OTPVerification).filter(
        and_(
            OTPVerification.email == request.email,
            OTPVerification.otp_code == request.otp_code,
            OTPVerification.verified == False,
            OTPVerification.expires_at > datetime.utcnow()
        )
    ).first()
    
    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP code"
        )
    
    # Mark OTP as verified
    otp_record.verified = True
    db.commit()
    
    # Create new user with verified email and active status
    hashed_password = get_password_hash(request.password)
    db_user = User(
        email=request.email,
        password=hashed_password,
        email_verified=True,
        is_active=True  # User đã xác minh Gmail → cho phép hoạt động
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return VerifyOTPResponse(
        message="Account registered successfully",
        user=UserResponse(
            id=db_user.id,
            email=db_user.email,
            email_verified=db_user.email_verified,
            is_active=db_user.is_active
        )
    )


@router.post("/register", response_model=UserResponse, deprecated=True)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user (DEPRECATED - Use verify-otp-and-register instead)
    This endpoint is kept for backward compatibility but requires OTP verification
    """
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="This endpoint is deprecated. Please use /request-otp and /verify-otp-and-register endpoints instead."
    )


@router.post("/login", response_model=Token)
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    """Login user and return JWT token"""
    # Find user by email
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active (đã xác minh Gmail)
    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active. Please verify your email first.",
        )

    # Create access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": str(db_user.id)}, expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")
