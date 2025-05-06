from typing import BinaryIO
from minio import Minio
from minio.error import S3Error
from fastapi import HTTPException, status

from src.config.settings import get_settings

settings = get_settings()

class StorageService:
    def __init__(self):
        if settings.STORAGE_PROVIDER == "s3":
            self.client = Minio(
                settings.AWS_S3_ENDPOINT,
                access_key=settings.AWS_ACCESS_KEY_ID,
                secret_key=settings.AWS_SECRET_ACCESS_KEY,
                region=settings.AWS_REGION,
                secure=True
            )
            self.buckets = {
                "movies": f"{settings.AWS_S3_BUCKET_NAME}-movies",
                "avatars": f"{settings.AWS_S3_BUCKET_NAME}-avatars"
            }
        else:
            self.client = Minio(
                settings.MINIO_ENDPOINT,
                access_key=settings.MINIO_ROOT_USER,
                secret_key=settings.MINIO_ROOT_PASSWORD,
                secure=settings.MINIO_SECURE
            )
            self.buckets = {
                "movies": "movies",
                "avatars": "avatars"
            }
        self._ensure_buckets_exist()

    def _ensure_buckets_exist(self):
        try:
            for bucket in self.buckets.values():
                if not self.client.bucket_exists(bucket):
                    if settings.STORAGE_PROVIDER == "s3":
                        self.client.make_bucket(bucket, location=settings.AWS_REGION)
                    else:
                        self.client.make_bucket(bucket)
        except S3Error as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error initializing storage: {str(e)}"
            )

    def _get_public_url(self, bucket_name: str, object_name: str) -> str:
        if settings.STORAGE_PROVIDER == "s3":
            return f"https://{bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{object_name}"
        else:
            return f"http://{settings.MINIO_ENDPOINT}/{bucket_name}/{object_name}"

    async def upload_file(self, file: BinaryIO, object_name: str, bucket_type: str = "movies") -> str:
        try:
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)

            bucket_name = self.buckets.get(bucket_type, self.buckets["movies"])

            self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=file,
                length=file_size
            )

            return self._get_public_url(bucket_name, object_name)

        except S3Error as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error uploading file: {str(e)}"
            )

    async def get_file_url(self, object_name: str, bucket_type: str = "movies") -> str:
        try:
            bucket_name = self.buckets.get(bucket_type, self.buckets["movies"])
            self.client.stat_object(bucket_name, object_name)
            return self._get_public_url(bucket_name, object_name)
        except S3Error as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {str(e)}"
            )

    async def delete_file(self, object_name: str, bucket_type: str = "movies"):
        try:
            bucket_name = self.buckets.get(bucket_type, self.buckets["movies"])
            self.client.remove_object(bucket_name, object_name)
        except S3Error as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting file: {str(e)}"
            ) 