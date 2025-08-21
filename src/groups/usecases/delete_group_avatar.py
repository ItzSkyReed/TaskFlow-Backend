from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ...minio import get_minio_client, AVATARS_BUCKET_NAME
from ..exceptions import NotEnoughPermissionsException
from ..models import GroupPermission
from ..services import get_group_with_members, group_member_has_permission


async def delete_group_avatar(
        group_id: UUID,
        initiator_id: UUID,
        session: AsyncSession,
) -> None:
    """
    Обновление аватарки профиля группы
    :param group_id: UUID группы
    :param initiator_id: UUID человека, который меняет аватарку
    :param session: Сессия
    """

    group = await get_group_with_members(group_id, session)

    if initiator_id != group.creator_id:
        if not group_member_has_permission(
                group_id,
                initiator_id,
                session,
                GroupPermission.FULL_ACCESS,
                GroupPermission.MANAGE_GROUP,
        ):
            raise NotEnoughPermissionsException()

    async with get_minio_client() as client:
        await client.delete_object(
            Bucket=AVATARS_BUCKET_NAME, Key=f"groups/{group_id}.webp",
        )

    group.has_avatar = False
    session.add(group)
    await session.commit()