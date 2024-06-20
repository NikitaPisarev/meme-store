from fastapi import APIRouter

from . import api_messages, auth, users, memes


auth_router = APIRouter()
auth_router.include_router(auth.router, prefix="/auth", tags=["auth"])

users_router = APIRouter(
    responses={
        401: {
            "description": "No `Authorization` access token header, token is invalid or user removed",
            "content": {
                "application/json": {
                    "examples": {
                        "not authenticated": {
                            "summary": "No authorization token header",
                            "value": {"detail": "Not authenticated"},
                        },
                        "invalid token": {
                            "summary": "Token validation failed, decode failed, it may be expired or malformed",
                            "value": {"detail": "Token invalid: {detailed error msg}"},
                        },
                        "removed user": {
                            "summary": api_messages.JWT_ERROR_USER_REMOVED,
                            "value": {"detail": api_messages.JWT_ERROR_USER_REMOVED},
                        },
                    }
                }
            },
        },
    }
)
users_router.include_router(users.router, prefix="/users", tags=["users"])

meme_router = APIRouter()
meme_router.include_router(memes.router, tags=["memes"])
