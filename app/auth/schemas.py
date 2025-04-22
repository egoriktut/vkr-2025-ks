from pydantic import BaseModel


class RegistrationSchema(BaseModel):
    password: str
    email: str


class ConfirmRegistrationSchema(BaseModel):
    email: str
    verification_code: str


class ResetPasswordSchemaCode(BaseModel):
    email: str


class ResetPasswordSchema(ConfirmRegistrationSchema):
    password: str


class ResponseSchema(BaseModel):
    token: str
