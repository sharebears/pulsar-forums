from collections import namedtuple

from core.notifications.models import Notification
from forums.models import ForumPost, ForumThread, ForumThreadSubscription
from forums.notifications import (
    check_post_contents_for_mentions,
    check_post_contents_for_quotes,
    send_subscription_notices,
)

ForumPostFake = namedtuple('ForumPost', ['contents', 'user_id'])


def test_subscribe_users_to_new_thread(app, authed_client):
    thread = ForumThread.new(
        topic='aa', forum_id=5, creator_id=1, post_contents='hello'
    )
    assert ForumThreadSubscription.user_ids_from_thread(thread.id) == [3, 4]


def test_dispatch_subscription_notices(app, client):
    send_subscription_notices(ForumPost.from_pk(7))
    assert (
        Notification.get_notification_counts(user_id=1)['forums_subscription']
        == 1
    )
    assert (
        Notification.get_notification_counts(user_id=2)['forums_subscription']
        == 0
    )


quote_c = (
    '[quote=user_two|121]hi[/quote]'
    '[quote=fake_user][quote=user_three]bye[/quote][/quote]'
    '[quote=user_four]hi'
)


def test_quoted_post(app, client):
    post = ForumPostFake(contents=quote_c, user_id=1)
    check_post_contents_for_quotes(post)
    assert len(Notification.from_type(user_id=2, type='forums_quoted')) == 1
    assert len(Notification.from_type(user_id=3, type='forums_quoted')) == 0
    assert len(Notification.from_type(user_id=4, type='forums_quoted')) == 1


quote_d = (
    '[quote=user_two|121]hi[/quote][quote=user_one]bye[/quote]'
    '[quote][quote=user_three]f[/quote][/quote]'
)


def test_quoted_post_by_self(app, client):
    post = ForumPostFake(contents=quote_d, user_id=1)
    check_post_contents_for_quotes(post)
    assert len(Notification.from_type(user_id=2, type='forums_quoted')) == 1
    assert len(Notification.from_type(user_id=1, type='forums_quoted')) == 0
    assert len(Notification.from_type(user_id=3, type='forums_quoted')) == 0


ment_c = (
    '[quote][user]user_two[/user][/quote]'
    '[user]user_three[/user]'
    '[user]user_one[/user]'
    '[user]fake_user[/user]'
)


def test_mentioned_post(app, client):
    post = ForumPostFake(contents=ment_c, user_id=1)
    check_post_contents_for_mentions(post)
    assert len(Notification.from_type(user_id=2, type='forums_mentioned')) == 0
    assert len(Notification.from_type(user_id=3, type='forums_mentioned')) == 1
    assert len(Notification.from_type(user_id=1, type='forums_mentioned')) == 0
