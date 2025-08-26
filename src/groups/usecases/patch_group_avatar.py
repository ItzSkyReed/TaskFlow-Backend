from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ...minio import AVATARS_BUCKET_NAME, get_minio_client
from ...utils import validate_avatar_file
from ..exceptions import NotEnoughPermissionsException
from ..models import GroupPermission
from ..schemas import GroupDetailSchema
from ..services import (
    get_group_with_members,
    get_groups_member_count,
    get_groups_user_context,
    group_member_has_permission,
    map_to_group_detail_schema,
)


async def patch_group_avatar(
    file: UploadFile,
    group_id: UUID,
    initiator_id: UUID,
    session: AsyncSession,
) -> GroupDetailSchema:
    """
    Обновление аватарки профиля группы
    :param file: Содержит данные о самом аватаре группы
    :param group_id: UUID группы
    :param initiator_id: UUID человека, который меняет аватарку
    :param session: Сессия
    """
    await validate_avatar_file(file)

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
        await client.put_object(
            Bucket=AVATARS_BUCKET_NAME,
            Key=f"groups/{group_id}.webp",
            Body=await file.read(),
            ContentType=file.content_type,
        )

    group.has_avatar = True
    session.add(group)
    await session.commit()

    group_seq = [group]

    groups_user_context_map = await get_groups_user_context(
        group_seq, initiator_id, session
    )

    members_count = await get_groups_member_count(group_seq, session)

    return map_to_group_detail_schema(
        group, groups_user_context_map[group.id], members_count[group.id]
    )
