from typing import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_pydantic_mapper import ObjectMapper

from ...user.schemas import PublicUserSchema
from ..models import Group, GroupInvitation
from ..schemas import (
    GroupDetailSchema,
    GroupInvitationSchema,
    GroupMemberSchema,
    GroupSearchSchema,
    GroupSummarySchema,
)
from . import get_groups_member_count
from .group_service import (
    get_group_member_count,
    get_group_user_context,
    get_groups_user_context,
)

__all__ = [
    "map_to_group_detail_schema",
    "map_to_group_invitation_schemas",
    "map_to_group_detail_schemas",
    "map_to_group_search_schemas",
    "map_to_group_summary_schemas",
    "map_to_group_search_schema",
    "map_to_group_invitation_schema",
    "map_to_group_summary_schema",
]


@ObjectMapper.register(Group, GroupDetailSchema)
async def map_to_group_detail_schema(
    group: Group, user_id: UUID, session: AsyncSession
) -> GroupDetailSchema:
    return GroupDetailSchema(
        id=group.id,
        name=group.name,
        description=group.description,
        creator_id=group.creator_id,
        created_at=group.created_at,
        max_members_count=group.max_members,
        members=[
            GroupMemberSchema.model_validate(member, from_attributes=True)
            for member in group.members
        ],
        has_avatar=group.has_avatar,
        me=await get_group_user_context(group, user_id, session),
        members_count=await get_group_member_count(group, session),
    )


@ObjectMapper.register_bulk(Group, GroupDetailSchema)
async def map_to_group_detail_schemas(
    groups: Sequence[Group], user_id: UUID, session: AsyncSession
) -> list[GroupDetailSchema]:
    user_contexts = await get_groups_user_context(groups, user_id, session)
    group_members_count = await get_groups_member_count(groups, session)

    return [
        GroupDetailSchema(
            id=group.id,
            name=group.name,
            description=group.description,
            creator_id=group.creator_id,
            created_at=group.created_at,
            max_members_count=group.max_members,
            members=[
                GroupMemberSchema.model_validate(member, from_attributes=True)
                for member in group.members
            ],
            has_avatar=group.has_avatar,
            me=user_contexts[group.id],
            members_count=group_members_count[group.id],
        )
        for group in groups
    ]


@ObjectMapper.register(Group, GroupSummarySchema)
async def map_to_group_summary_schema(
    group: Group, user_id: UUID, session: AsyncSession
) -> GroupSummarySchema:
    return GroupSummarySchema(
        id=group.id,
        name=group.name,
        creator_id=group.creator_id,
        created_at=group.created_at,
        max_members_count=group.max_members,
        has_avatar=group.has_avatar,
        me=await get_group_user_context(group, user_id, session),
        members_count=await get_group_member_count(group, session),
    )


@ObjectMapper.register_bulk(Group, GroupSummarySchema)
async def map_to_group_summary_schemas(
    groups: Sequence[Group], user_id: UUID, session: AsyncSession
) -> list[GroupSummarySchema]:
    user_contexts = await get_groups_user_context(groups, user_id, session)
    group_members_count = await get_groups_member_count(groups, session)

    return [
        GroupSummarySchema(
            id=group.id,
            name=group.name,
            creator_id=group.creator_id,
            created_at=group.created_at,
            max_members_count=group.max_members,
            has_avatar=group.has_avatar,
            me=user_contexts[group.id],
            members_count=group_members_count[group.id],
        )
        for group in groups
    ]


@ObjectMapper.register(Group, GroupSearchSchema)
async def map_to_group_search_schema(
    group: Group, user_id: UUID, session: AsyncSession
) -> GroupSearchSchema:
    return GroupSearchSchema(
        id=group.id,
        name=group.name,
        max_members_count=group.max_members,
        has_avatar=group.has_avatar,
        me=await get_group_user_context(group, user_id, session),
        members_count=await get_group_member_count(group, session),
    )


@ObjectMapper.register_bulk(Group, GroupSearchSchema)
async def map_to_group_search_schemas(
    groups: Sequence[Group], user_id: UUID, session: AsyncSession
) -> list[GroupSearchSchema]:
    user_contexts = await get_groups_user_context(groups, user_id, session)
    group_members_count = await get_groups_member_count(groups, session)

    return [
        GroupSearchSchema(
            id=group.id,
            name=group.name,
            max_members_count=group.max_members,
            has_avatar=group.has_avatar,
            me=user_contexts[group.id],
            members_count=group_members_count[group.id],
        )
        for group in groups
    ]


@ObjectMapper.register(Group, GroupInvitationSchema)
async def map_to_group_invitation_schema(
    invitation: GroupInvitation, user_id: UUID, session: AsyncSession
) -> GroupInvitationSchema:
    return GroupInvitationSchema(
        id=invitation.id,
        status=invitation.status,
        updated_at=invitation.updated_at,
        created_at=invitation.created_at,
        inviter=PublicUserSchema.model_validate(
            invitation.inviter, from_attributes=True
        ),
        group=await map_to_group_summary_schema(invitation.group, user_id, session),
    )


@ObjectMapper.register_bulk(Group, GroupInvitationSchema)
async def map_to_group_invitation_schemas(
    invitations: Sequence[GroupInvitation], user_id: UUID, session: AsyncSession
) -> list[GroupInvitationSchema]:
    groups_summary_schemas = await map_to_group_summary_schemas(
        [invitation.group for invitation in invitations], user_id, session
    )
    return [
        GroupInvitationSchema(
            id=invitation.id,
            status=invitation.status,
            updated_at=invitation.updated_at,
            created_at=invitation.created_at,
            inviter=PublicUserSchema.model_validate(
                invitation.inviter, from_attributes=True
            ),
            group=group_summary_schema,
        )
        for invitation, group_summary_schema in zip(
            invitations, groups_summary_schemas, strict=False
        )
    ]
