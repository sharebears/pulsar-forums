import re
from typing import List
from core.notifications.models import Notification
from core.users.models import User
from forums.models import ForumPost


RE_QUOTE = re.compile(r'\[quote(?:=(.+)(?:\|.+)?)?\]|\[\/quote\]', flags=re.IGNORECASE)
RE_QUOTE_OPEN = re.compile(r'\[quote(?:=[^\]]+)?\]/', flags=re.IGNORECASE)

RE_MENTION = re.compile(r'\[user\]([^ ]+)\[\/user\]|\[quote(?:=[^\]]+)?\]|\[\/quote\]',
                        flags=re.IGNORECASE)


def check_post_contents_for_quotes(post: ForumPost) -> None:
    cur_nest_level = 0
    quoted_usernames: List[str] = []
    for match in RE_QUOTE.findall(post.contents):
        if match[0].lower() != '[/quote]':
            if cur_nest_level == 0 and match.last_index == 1:
                quoted_usernames += match[1]
            cur_nest_level -= 1
        else:
            cur_nest_level += 1

    _dispatch_notifications(post, type='forums_quoted', usernames=quoted_usernames)


def check_post_contents_for_mentions(post: ForumPost) -> None:
    cur_nest_level = 0
    mentioned_usernames: List[str] = []
    for match in RE_MENTION.findall(post.contents):
        if RE_QUOTE_OPEN.match(match[0]):
            cur_nest_level += 1
        elif match[0].lower() == '[/quote]':
            cur_nest_level -= 1
        elif cur_nest_level == 0 and match.last_index == 1:
            mentioned_usernames += match[1]

    _dispatch_notifications(post, type='forums_mentioned', usernames=mentioned_usernames)


def _dispatch_notifications(post: ForumPost,
                            type: str,
                            usernames: List[str]) -> None:
    for uname in usernames:
        user_id = User.from_username(uname)
        if user_id:
            Notification.new(
                user_id=user_id,
                type=type,
                contents={
                    'thread_id': 1,
                    'post_id': 1,
                    'from': post.user_id,
                    })
