from pydantic import BaseModel, EmailStr, HttpUrl


class BaseRequest(BaseModel):
    pass


class RefreshTokenRequest(BaseRequest):
    refresh_token: str


class UserUpdatePasswordRequest(BaseRequest):
    password: str


class UserCreateRequest(BaseRequest):
    email: EmailStr
    password: str


class MemeCreateRequest(BaseRequest):
    description: str
    image_url: HttpUrl
    visibility: bool


class MemeUpdateRequest(BaseRequest):
    description: str | None = None
    visibility: bool | None = None
