# ~/Documents/WealthTrackr/backend/routes/email_verification.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from backend.database import get_db
# Import the new functions for verification
from backend.crud_user import get_user_by_verification_token, mark_email_as_verified

# Define the router
router = APIRouter(prefix="/verify-email", tags=["Email Verification"])

@router.get("/{token}")
async def verify_email_route(token: str, db: Session = Depends(get_db)):
    """
    Verifies a user's email address using a token sent to their email.
    """
    # Use get_user_by_verification_token to find the user
    user = get_user_by_verification_token(db, token)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token")

    # Optional: Check for token expiry. Assuming verification_sent_at is stored in UTC.
    # If your token validity period is, say, 24 hours.
    if user.verification_sent_at and (datetime.now(timezone.utc) - user.verification_sent_at) > timedelta(hours=24):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification token expired")

    if user.is_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified")

    # Use mark_email_as_verified to update the user's status
    if mark_email_as_verified(db, user):
        return {"message": "Email verified successfully!"}
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to verify email")
