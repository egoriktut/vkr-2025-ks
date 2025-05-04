from auth.schemas import (
    ConfirmRegistrationSchema,
    RegistrationSchema,
    ResetPasswordSchema,
    ResetPasswordSchemaCode,
)
from auth.services import AuthService
from db.dependencies import get_db
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

router = APIRouter()


@router.put("/login", status_code=status.HTTP_200_OK)
async def login(credentials: RegistrationSchema, db: Session = Depends(get_db)):
    return AuthService.login_user(db, credentials)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(credentials: RegistrationSchema, db: Session = Depends(get_db)):
    AuthService.register_user(db, credentials)
    return {
        "message": "Registration successful. Please check your email for verification code."
    }


@router.put("/confirm_registration")
async def confirm_register(
    confirmation: ConfirmRegistrationSchema, db: Session = Depends(get_db)
):
    AuthService.confirm_registration(db, confirmation)
    return {"message": "Registration confirmed successfully. You can now login."}


@router.put("/resend_code")
async def resend_code(confirmation: RegistrationSchema, db: Session = Depends(get_db)):
    AuthService.resend_verification_code(db, confirmation)
    return {"message": "Registration confirmed successfully. You can now login."}


@router.put("/reset_password")
async def reset_password(
    confirmation: ResetPasswordSchema, db: Session = Depends(get_db)
):
    AuthService.reset_password(db, confirmation)
    return {"message": "password changed successfully. You can now login."}


@router.put("/confirm_code")
async def confirm_code(
    confirmation: ResetPasswordSchema, db: Session = Depends(get_db)
):
    AuthService.confirm_code(db, confirmation)
    return {"message": "successfully. You can change your password."}


@router.put("/reset_password_code")
async def reset_password_code(
    email: ResetPasswordSchemaCode, db: Session = Depends(get_db)
):
    AuthService.send_code_verification_email(db, email.email)
    return {"message": "code sent"}
