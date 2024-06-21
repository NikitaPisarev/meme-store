from aiobotocore.session import ClientCreatorContext, get_session
from botocore.exceptions import ClientError
from minio.error import S3Error
from fastapi import HTTPException, UploadFile
import uuid

from src.config import get_settings


async def create_minio_client() -> ClientCreatorContext:
    settings = get_settings()
    session = get_session()
    return session.create_client(
        "s3",
        endpoint_url=str(settings.minio.endpoint_url),
        region_name="us-east-1",
        aws_access_key_id=settings.minio.access_key_id,
        aws_secret_access_key=settings.minio.secret_access_key.get_secret_value(),
        use_ssl=False
    )


async def ensure_bucket_exists(client: ClientCreatorContext, bucket_name: str) -> None:
    try:
        await client.create_bucket(Bucket=bucket_name)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "BucketAlreadyOwnedByYou":
            pass
        elif error_code == "BucketAlreadyExists":
            raise HTTPException(status_code=409, detail="Bucket name already in use by another account.")
        else:
            print(f"Error checking/creating bucket: {e}")
            raise HTTPException(status_code=500, detail="Error checking/creating bucket.")
    except Exception as e:
        print(f"Unexpected error when checking/creating bucket: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error checking/creating bucket.")


async def get_image_url(file_path: str, bucket_name: str = get_settings().minio.bucket_name, expires: int = 900) -> str:
    client = await create_minio_client()
    try:
        async with client as minio:
            presigned_url = await minio.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket_name, "Key": file_path},
                ExpiresIn=expires)
        return presigned_url
    except S3Error as e:
        print(f"Error getting image URL: {e}")
        raise HTTPException(status_code=500, detail="Error getting image URL.")


async def upload_image(file: UploadFile) -> str:
    try:
        client = await create_minio_client()
        bucket_name = get_settings().minio.bucket_name
        file_path = f"{uuid.uuid4()}/{file.filename}"

        async with client as minio:
            await ensure_bucket_exists(minio, bucket_name)
            await minio.put_object(
                Bucket=bucket_name,
                Key=file_path,
                Body=file.file.read(),
                ContentType=file.content_type
            )
        return file_path
    except S3Error as e:
        print(f"Error uploading image: {e}")
        raise HTTPException(status_code=500, detail="Error uploading image.")


async def delete_image(file_path: str) -> None:
    try:
        client = await create_minio_client()
        async with client as minio:
            await minio.delete_object(Bucket=get_settings().minio.bucket_name, Key=file_path)
    except S3Error as e:
        print(f"Failed to delete image from MINIO: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete image")
