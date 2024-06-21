from typing import Optional
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.api.models import User, Meme
from src.api.schemas.responses import MemeResponse
from src.api.endpoints import api_utils
from src.core.s3 import get_image_url, upload_image, delete_image

router = APIRouter()


@router.get(
    "/users/{user_id}/memes",
    response_model=list[MemeResponse],
    description="Get all public memes of a user.",
)
async def get_public_memes_of_user(
    user_id: str,
    session: AsyncSession = Depends(api_utils.get_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
) -> list[MemeResponse]:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    offset = (page - 1) * page_size
    result = await session.execute(
        select(Meme)
        .where(Meme.owner_id == user_id, Meme.visibility.is_(True))
        .offset(offset)
        .limit(page_size)
    )
    memes = result.scalars().all()

    response = []
    for meme in memes:
        presigned_url = await get_image_url(meme.image_url)
        response.append(
            MemeResponse(
                id=meme.id,
                description=meme.description,
                image_url=presigned_url,
                visibility=meme.visibility,
                owner_id=meme.owner_id,
            )
        )

    return response


@router.get(
    "/users/{user_id}/memes/{meme_id}",
    response_model=MemeResponse,
    description="Get a specific public meme of a user.",
)
async def get_specific_public_meme(
    user_id: str,
    meme_id: int,
    session: AsyncSession = Depends(api_utils.get_session),
) -> MemeResponse:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    result = await session.execute(
        select(Meme).where(
            Meme.id == meme_id, Meme.owner_id == user_id, Meme.visibility.is_(True)
        )
    )
    meme = result.scalars().first()
    if meme is None:
        raise HTTPException(status_code=404, detail="Meme not found or not public.")
    meme.image_url = await get_image_url(meme.image_url)
    return meme


@router.get(
    "/me/memes",
    response_model=list[MemeResponse],
    description="Get all memes of the current user.",
)
async def get_all_memes_of_current_user(
    current_user: User = Depends(api_utils.get_current_user),
    session: AsyncSession = Depends(api_utils.get_session),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
) -> list[MemeResponse]:
    offset = (page - 1) * page_size
    result = await session.execute(
        select(Meme)
        .where(Meme.owner_id == current_user.user_id)
        .offset(offset)
        .limit(page_size)
    )
    memes = result.scalars().all()

    response = []
    for meme in memes:
        presigned_url = await get_image_url(meme.image_url)
        response.append(
            MemeResponse(
                id=meme.id,
                description=meme.description,
                image_url=presigned_url,
                visibility=meme.visibility,
                owner_id=meme.owner_id,
            )
        )

    return response


@router.get(
    "/me/memes/{meme_id}",
    response_model=MemeResponse,
    description="Get a specific meme of the current user.",
)
async def get_specific_meme_of_current_user(
    meme_id: int,
    current_user: User = Depends(api_utils.get_current_user),
    session: AsyncSession = Depends(api_utils.get_session),
) -> MemeResponse:
    result = await session.execute(
        select(Meme).where(Meme.id == meme_id, Meme.owner_id == current_user.user_id)
    )
    meme = result.scalars().first()
    if meme is None:
        raise HTTPException(status_code=404, detail="Meme not found.")

    meme.image_url = await get_image_url(meme.image_url)

    return meme


@router.post(
    "/me/memes",
    response_model=MemeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_meme(
    description: str = Form(...),
    visibility: bool = Form(...),
    image: UploadFile = File(...),
    session: AsyncSession = Depends(api_utils.get_session),
    current_user: User = Depends(api_utils.get_current_user),
) -> MemeResponse:
    image_path = await upload_image(image)

    new_meme = Meme(
        description=description,
        image_url=image_path,
        visibility=visibility,
        owner_id=current_user.user_id,
    )

    session.add(new_meme)
    await session.commit()
    await session.refresh(new_meme)
    return new_meme


@router.delete("/me/memes/{meme_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meme(
    meme_id: int,
    current_user: User = Depends(api_utils.get_current_user),
    session: AsyncSession = Depends(api_utils.get_session),
) -> None:
    result = await session.execute(
        select(Meme).where(Meme.id == meme_id, Meme.owner_id == current_user.user_id)
    )
    meme = result.scalars().first()

    if not meme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meme not found or you do not have permission to delete it.",
        )

    await delete_image(meme.image_url.split("/")[-1])
    await session.delete(meme)
    await session.commit()


@router.put("/me/memes/{meme_id}", response_model=MemeResponse)
async def update_meme(
    meme_id: int,
    description: str = Form(...),
    visibility: bool = Form(...),
    image: Optional[UploadFile] = File(...),
    current_user: User = Depends(api_utils.get_current_user),
    session: AsyncSession = Depends(api_utils.get_session),
) -> MemeResponse:
    result = await session.execute(
        select(Meme).where(Meme.id == meme_id, Meme.owner_id == current_user.user_id)
    )
    meme = result.scalars().first()

    if not meme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meme not found or you do not have permission to edit it.",
        )

    if image:
        old_image_path = meme.image_url.split("/")[-1]
        await delete_image(old_image_path)
        new_image_path = await upload_image(image)
        meme.image_url = new_image_path

    if description:
        meme.description = description
    if visibility:
        meme.visibility = visibility

    session.add(meme)
    await session.commit()
    await session.refresh(meme)

    return meme
