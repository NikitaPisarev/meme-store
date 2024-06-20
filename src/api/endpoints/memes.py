from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.api.models import User, Meme
from src.api.schemas.responses import MemeResponse
from src.api.schemas.requests import MemeCreateRequest, MemeUpdateRequest
from src.api.endpoints import api_utils

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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    offset = (page - 1) * page_size
    result = await session.execute(
        select(Meme)
        .where(Meme.owner_id == user_id, Meme.visibility.is_(True))
        .offset(offset)
        .limit(page_size)
    )
    memes = result.scalars().all()
    return [MemeResponse.model_validate(meme) for meme in memes]


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    result = await session.execute(
        select(Meme).where(Meme.id == meme_id, Meme.owner_id == user_id, Meme.visibility.is_(True))
    )
    meme = result.scalars().first()
    if meme is None:
        raise HTTPException(status_code=404, detail="Meme not found or not public.")
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
    return memes


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
    return meme


@router.post(
    "/me/memes",
    response_model=MemeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_meme(
    meme_data: MemeCreateRequest,
    session: AsyncSession = Depends(api_utils.get_session),
    current_user: User = Depends(api_utils.get_current_user)
) -> MemeResponse:
    new_meme = Meme(
        description=meme_data.description,
        image_url=str(meme_data.image_url),
        visibility=meme_data.visibility,
        owner_id=current_user.user_id
    )
    session.add(new_meme)
    await session.commit()
    await session.refresh(new_meme)
    return new_meme


@router.delete("/me/memes/{meme_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meme(
    meme_id: int,
    current_user: User = Depends(api_utils.get_current_user),
    session: AsyncSession = Depends(api_utils.get_session)
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

    await session.delete(meme)
    await session.commit()


@router.put("/me/memes/{meme_id}", response_model=MemeResponse)
async def update_meme(
    meme_id: int,
    meme_data: MemeUpdateRequest,
    current_user: User = Depends(api_utils.get_current_user),
    session: AsyncSession = Depends(api_utils.get_session)
) -> MemeResponse:
    result = await session.execute(
        select(Meme).where(Meme.id == meme_id, Meme.owner_id == current_user.user_id)
    )
    meme = result.scalars().first()

    if not meme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meme not found or you do not have permission to edit it."
        )

    for var, value in vars(meme_data).items():
        if value is not None:
            setattr(meme, var, value)

    session.add(meme)
    await session.commit()
    await session.refresh(meme)

    return meme
