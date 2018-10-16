import re
from typing import List

from core import Config
from core.mixins import Attribute
from core.users.models import User
from core.users.serializers import UserSerializer
from core.utils import cached_property
from forums.models import ForumPost, ForumThread
from core.permissions.models import UserPermission


old_is_valid_permission = UserPermission.is_valid_permission


@classmethod
def is_valid_permission(cls,
                        permission: str,
                        permissioned: bool = True) -> bool:
    if not old_is_valid_permission(permission, permissioned):
        return any(re.match(f'forumaccess_{t}_\d+$', permission) for t in ['forum', 'thread'])
    return True


@cached_property
def forum_post_count(self) -> int:
    return self.count(
        key=self.__cache_key_forum_post_count__.format(id=self.id),
        attribute=ForumPost.id,
        filter=ForumPost.poster_id == self.id)


@cached_property
def forum_thread_count(self) -> int:
    return self.count(
        key=self.__cache_key_forum_thread_count__.format(id=self.id),
        attribute=ForumThread.id,
        filter=ForumThread.poster_id == self.id)


@cached_property
def forum_permissions(self) -> List[str]:
    return {p for p in self.permissions if p.startswith('forumaccess')}


def modify_core():
    User.assign_attrs(
        __cache_key_forum_post_count__='users_{id}_forum_post_count',
        __cache_key_forum_thread_count__='users_{id}_forum_thread_count',
        forum_thread_count=forum_thread_count,
        forum_post_count=forum_post_count,
        forum_permissions=forum_permissions,
        )
    UserSerializer.assign_attrs(
        forum_permissions=Attribute(permission='moderate_users', nested=False),
        )
    UserPermission.assign_attrs(
        is_valid_permission=is_valid_permission,
        )

    Config.BASIC_PERMISSIONS += [
        'create_forum_posts',
        'create_forum_threads',
        ]

    from forums import PERMISSIONS
    UserPermission.all_permissions += PERMISSIONS
