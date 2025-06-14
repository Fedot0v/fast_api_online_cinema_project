from datetime import date
from typing import Annotated, Optional

from src.database.models.accounts import GenderEnum
from src.database.validators.accounts import validate_email
from fastapi import UploadFile, Form, File, HTTPException
from pydantic import BaseModel, field_validator, HttpUrl, EmailStr, ConfigDict, AfterValidator, Field

from src.database.validators.accounts import validate_password_strength
from src.database.validators.profile import (
    validate_name,
    validate_image,
    validate_gender,
    validate_birth_date
)


class BaseTokenSchema(BaseModel):
    token: str


class BaseEmailSchema(BaseModel):
    email: Annotated[
        EmailStr,
        AfterValidator(validate_email)
    ]


class BasePasswordSchema(BaseModel):
    password: Annotated[
        str,
        AfterValidator(validate_password_strength)
    ]


class ChangeGroupRequest(BaseModel):
    user_id: int
    new_group_id: int


class MessageSchema(BaseModel):
    message: str


class BasePasswordEmailSchema(BaseEmailSchema, BasePasswordSchema):
    model_config = ConfigDict(from_attributes=True)


class UserRegistrationSchema(BasePasswordEmailSchema):
    group_id: int = 1


class UserRegistrationResponseSchema(BaseModel):
    id: int
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)


class PasswordResetCompleteRequestSchema(BasePasswordSchema):
    token: str


class LoginRequestSchema(BaseEmailSchema, BasePasswordSchema):
    pass


class RefreshTokenSchema(BaseModel):
    refresh_token: str


class AccessTokenSchema(BaseModel):
    access_token: str


class LoginResponseSchema(RefreshTokenSchema, AccessTokenSchema):
    token_type: str


class ProfileCreateSchema(BaseModel):
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    gender: GenderEnum
    date_of_birth: Optional[date] = None
    info: Optional[str] = None
    avatar: Optional[UploadFile] = None

    @classmethod
    def from_form(
        cls,
        first_name: str = Form(...),
        last_name: str = Form(...),
        gender: GenderEnum = Form(...),
        date_of_birth: Optional[date] = Form(None),
        info: Optional[str] = Form(None),
        avatar: Optional[UploadFile] = File(None, description="Avatar image")
    ) -> "ProfileCreateSchema":
        return cls(
            first_name=first_name,
            last_name=last_name,
            gender=GenderEnum(gender),
            date_of_birth=date_of_birth,
            info=info,
            avatar=avatar
        )

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name_field(cls, name: str) -> str:
        try:
            validate_name(name)
            return name.lower()
        except ValueError as e:
            raise HTTPException(
                status_code=422,
                detail=[{
                    "type": "value_error",
                    "loc": ["first_name" if "first_name" in name else "last_name"],
                    "msg": str(e),
                    "input": name
                }]
            )

    @field_validator("avatar")
    @classmethod
    def validate_avatar(cls, avatar: Optional[UploadFile]) -> Optional[UploadFile]:
        if avatar is None:
            return None

        try:
            validate_image(avatar)
            return avatar
        except ValueError as e:
            raise HTTPException(
                status_code=422,
                detail=[{
                    "type": "value_error",
                    "loc": ["avatar"],
                    "msg": str(e),
                    "input": avatar.filename
                }]
            )

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, gender: str) -> str:
        try:
            validate_gender(gender)
            return gender
        except ValueError as e:
            raise HTTPException(
                status_code=422,
                detail=[{
                    "type": "value_error",
                    "loc": ["gender"],
                    "msg": str(e),
                    "input": gender
                }]
            )

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, date_of_birth: date) -> date:
        try:
            validate_birth_date(date_of_birth)
            return date_of_birth
        except ValueError as e:
            raise HTTPException(
                status_code=422,
                detail=[{
                    "type": "value_error",
                    "loc": ["date_of_birth"],
                    "msg": str(e),
                    "input": str(date_of_birth)
                }]
            )

    @field_validator("info")
    @classmethod
    def validate_info(cls, info: str) -> str:
        cleaned_info = info.strip()
        if not cleaned_info:
            raise HTTPException(
                status_code=422,
                detail=[{
                    "type": "value_error",
                    "loc": ["info"],
                    "msg": "Info field cannot be empty or contain only spaces.",
                    "input": info
                }]
            )
        return cleaned_info


class UpdateProfileSchema(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[GenderEnum] = None
    date_of_birth: Optional[date] = None
    info: Optional[str] = None
    avatar: Optional[UploadFile] = None

    @classmethod
    def from_form(
        cls,
        first_name: Optional[str] = Form(None),
        last_name: Optional[str] = Form(None),
        gender: Optional[GenderEnum] = Form(None),
        date_of_birth: Optional[date] = Form(None),
        info: Optional[str] = Form(None),
        avatar: Optional[UploadFile] = File(None)
    ) -> "UpdateProfileSchema":
        return cls(
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            date_of_birth=date_of_birth,
            info=info,
            avatar=avatar
        )

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name_field(cls, name: Optional[str], field) -> Optional[str]:
        if name is None:
            return None
        try:
            validate_name(name)
            return name.lower()
        except ValueError as e:
            raise HTTPException(
                status_code=422,
                detail=[{
                    "type": "value_error",
                    "loc": [field.name],
                    "msg": str(e),
                    "input": name
                }]
            )

    @field_validator("avatar")
    @classmethod
    def validate_avatar(cls, avatar: Optional[UploadFile]) -> Optional[UploadFile]:
        if avatar is None:
            return None
        try:
            validate_image(avatar)
            return avatar
        except ValueError as e:
            raise HTTPException(
                status_code=422,
                detail=[{
                    "type": "value_error",
                    "loc": ["avatar"],
                    "msg": str(e),
                    "input": avatar.filename
                }]
            )

    @field_validator("gender")
    @classmethod
    def validate_gender_field(cls, gender: Optional[GenderEnum]) -> Optional[GenderEnum]:
        if gender is None:
            return None
        try:
            validate_gender(gender)
            return gender
        except ValueError as e:
            raise HTTPException(
                status_code=422,
                detail=[{
                    "type": "value_error",
                    "loc": ["gender"],
                    "msg": str(e),
                    "input": gender
                }]
            )

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, date_of_birth: Optional[date]) -> Optional[date]:
        if date_of_birth is None:
            return None
        try:
            validate_birth_date(date_of_birth)
            return date_of_birth
        except ValueError as e:
            raise HTTPException(
                status_code=422,
                detail=[{
                    "type": "value_error",
                    "loc": ["date_of_birth"],
                    "msg": str(e),
                    "input": str(date_of_birth)
                }]
            )

    @field_validator("info")
    @classmethod
    def validate_info(cls, info: Optional[str]) -> Optional[str]:
        if info is None:
            return None
        cleaned_info = info.strip()
        if not cleaned_info:
            raise HTTPException(
                status_code=422,
                detail=[{
                    "type": "value_error",
                    "loc": ["info"],
                    "msg": "Info field cannot be empty or contain only spaces.",
                    "input": info
                }]
            )
        return cleaned_info


class ProfileResponseSchema(BaseModel):
    id: int
    user_id: int
    first_name: str
    last_name: str
    gender: str
    date_of_birth: date
    info: str
    avatar: str | None

    model_config = ConfigDict(from_attributes=True)
