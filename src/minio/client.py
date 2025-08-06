from collections.abc import AsyncGenerator

import aioboto3

from .. import get_settings

settings = get_settings()


async def get_minio_client() -> AsyncGenerator:
    """
    :return: Асинхронный S3 клиент для работы с minio
    """
    session = aioboto3.Session()
    async with session.client(
        service_name="s3",
        endpoint_url=f"minio:{settings.minio_storage_port}",
        aws_access_key_id=settings.minio_root_user,
        aws_secret_access_key=settings.minio_root_key,
        use_ssl=False,
        verify=False,
    ) as client:
        yield client
