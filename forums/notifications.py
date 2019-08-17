import re
from typing import TYPE_CHECKING, List

from core import db
from core.notifications.models import Notification
from core.users.models import User

if TYPE_CHECKING:
    from forums.models import ForumPost, ForumThread  # noqa


RE_QUOTE = re.compile(
    r'(\[quote(?:=([^|\]]*?)(?:\|.+?)?)?\]|\[\/quote\])', flags=re.IGNORECASE
)
RE_QUOTE_OPEN = re.compile(r'\[quote[^\]]*\]', flags=re.IGNORECASE)

RE_MENTION = re.compile(
    r'(\[user\](.+?)\[\/user\]|\[quote[^\]]*\]|\[\/quote\])',
    flags=re.IGNORECASE,
)


def subscribe_users_to_new_thread(thread: 'ForumThread') -> None:
    """
    Subscribes all users subscribed to the parent forum to the new forum thread.

    :param thread: The newly-created forum thread
    """
    from forums.models import ForumSubscription, ForumThreadSubscription

    user_ids = ForumSubscription.user_ids_from_forum(thread.forum_id)
    db.session.bulk_save_objects(
        [
            ForumThreadSubscription.new(user_id=uid, thread_id=thread.id)
            for uid in user_ids
        ]
    )
    ForumThreadSubscription.clear_cache_keys(user_ids=user_ids)


def send_subscription_notices(post: 'ForumPost') -> None:
    from forums.models import ForumThreadSubscription

    user_ids = ForumThreadSubscription.user_ids_from_thread(post.thread_id)
    if post.user_id in user_ids:
        user_ids.remove(post.user_id)
    _dispatch_notifications(
        post, type='forums_subscription', user_ids=user_ids
    )


def check_post_contents_for_quotes(post: 'ForumPost') -> None:
    cur_nest_level = 0
    quoted_user_ids: List[int] = []
    for match in RE_QUOTE.findall(post.contents):
        if match[0].lower() != '[/quote]':
            if (
                cur_nest_level == 0
                and isinstance(match, tuple)
                and len(match) == 2
            ):
                user = User.from_username(match[1])
                if user and user.id != post.user_id:
                    quoted_user_ids.append(user.id)
            cur_nest_level -= 1
        else:
            cur_nest_level += 1

    _dispatch_notifications(
        post, type='forums_quoted', user_ids=quoted_user_ids
    )


def check_post_contents_for_mentions(post: 'ForumPost') -> None:
    cur_nest_level = 0
    mentioned_user_ids: List[int] = []
    for match in RE_MENTION.findall(post.contents):
        if RE_QUOTE_OPEN.match(match[0]):
            cur_nest_level += 1
        elif match[0].lower() == '[/quote]':
            cur_nest_level -= 1
        elif (
            cur_nest_level == 0
            and isinstance(match, tuple)
            and len(match) == 2
        ):
            user = User.from_username(match[1])
            if user and user.id != post.user_id:
                mentioned_user_ids.append(user.id)

    _dispatch_notifications(
        post, type='forums_mentioned', user_ids=mentioned_user_ids
    )


def _dispatch_notifications(
    post: 'ForumPost', type: str, user_ids: List[int]
) -> None:
    for user_id in user_ids:
        Notification.new(
            user_id=user_id,
            type=type,
            contents={'thread_id': 1, 'post_id': 1, 'from': post.user_id},
        )
