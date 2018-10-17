import re
from typing import Set

from core import Config
from core.mixins import Attribute
from core.permissions import Permissions
from core.users.models import User
from core.users.serializers import UserSerializer
from core.utils import cached_property
from forums.models import ForumPost, ForumThread


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
def forum_permissions(self) -> Set[str]:
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
        forum_permissions=Attribute(permission='users_moderate', nested=False),
        )
    Permissions.permission_regexes['basic'] += [
        re.compile('forumaccess_forum_\d+$'),
        re.compile('forumaccess_thread_\d+$'),
        ]
    Config.BASIC_PERMISSIONS += [
        'forums_posts_create',
        'forums_threads_create',
        ]
