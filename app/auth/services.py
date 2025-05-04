from auth.schemas import (
    ConfirmRegistrationSchema,
    RegistrationSchema,
    ResetPasswordSchema,
)
from auth.utils import (
    generate_token,
    generate_verification_code,
    get_password_hash,
    send_verification_email,
    verify_password,
)
from db.models import User
from fastapi import HTTPException, status
from sqlalchemy.orm import Session


class AuthService:

    @staticmethod
    def login_user(db: Session, credentials: RegistrationSchema):
        user = db.query(User).filter(User.email == credentials.email).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        elif not user.activated:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not activated"
            )
        elif not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="bad password"
            )
        elif not user.token:
            user.token = generate_token()
            db.commit()
            db.refresh(user)

        return user.token

    @staticmethod
    def register_user(db: Session, credentials: RegistrationSchema):
        if db.query(User).filter(User.email == credentials.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        if len(credentials.password) < 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Small password required",
            )

        hashed_password = get_password_hash(credentials.password)
        verification_code = generate_verification_code()

        new_user = User(
            email=credentials.email,
            hashed_password=hashed_password,
            verification_code=verification_code,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        send_verification_email(credentials.email, verification_code)

        return new_user

    @staticmethod
    def resend_verification_code(db: Session, confirmation: RegistrationSchema):
        verification_code = generate_verification_code()
        user = db.query(User).filter(User.email == confirmation.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="user not found"
            )

        user.verification_code = verification_code
        db.commit()
        db.refresh(user)

        send_verification_email(confirmation.email, verification_code)

    @staticmethod
    def confirm_registration(db: Session, confirmation: ConfirmRegistrationSchema):
        user = db.query(User).filter(User.email == confirmation.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        if user.verification_code != confirmation.verification_code.strip().upper():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code",
            )

        user.verification_code = ""
        user.activated = True
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def send_code_verification_email(db: Session, email: str):
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Email not registered"
            )
        verification_code = generate_verification_code()

        user.verification_code = verification_code
        db.commit()
        db.refresh(user)

        send_verification_email(email, verification_code)

    @staticmethod
    def confirm_code(db: Session, configuration: ResetPasswordSchema):
        user = db.query(User).filter(User.email == configuration.email).first()
        if user.verification_code != configuration.verification_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code",
            )
        return user

    @staticmethod
    def reset_password(db: Session, configuration: ResetPasswordSchema):
        user = db.query(User).filter(User.email == configuration.email).first()
        if not user.activated:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not activated"
            )
        if user.verification_code != configuration.verification_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code",
            )

        if len(configuration.password) < 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Small password required",
            )
        hashed_password = get_password_hash(configuration.password)
        user.hashed_password = hashed_password
        user.verification_code = ""

        db.commit()
        db.refresh(user)

        return user
