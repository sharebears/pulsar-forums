from core.users.models import User
from core.utils import cached_property
from forums.models import ForumPost
from forums.models import ForumThread


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


def modify_user_model():
    User.assign_attrs(
        __cache_key_forum_post_count__='users_{id}_forum_post_count',
        __cache_key_forum_thread_count__='users_{id}_forum_thread_count',
        __cache_key_forum_permissions__='users_{id}_forums_permissions',
        forum_thread_count=forum_thread_count,
        forum_post_count=forum_post_count,
        )
