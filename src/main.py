from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.endpoints.api_router import users_router, auth_router, meme_router
from .config import get_settings

app = FastAPI(
    title="meme-store",
    version="1.0.0",
    description="Meme store using s3 storage",
    openapi_url="/openapi.json",
    docs_url="/",
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(meme_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        str(origin).rstrip("/")
        for origin in get_settings().security.backend_cors_origins
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
