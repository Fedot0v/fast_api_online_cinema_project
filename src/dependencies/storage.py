from fastapi import Depends
from src.services.storage.minio_service import MinioService

def get_storage_service() -> MinioService:
    """
    Зависимость для получения сервиса хранилища.
    
    Returns:
        MinioService: Экземпляр сервиса для работы с MinIO
    """
    return MinioService() 