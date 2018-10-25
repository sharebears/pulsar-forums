from conftest import add_permissions, check_json_response
from core import cache, db
from forums.models import Forum, ForumSubscription, ForumThread, ForumThreadSubscription
from forums.permissions import ForumPermissions


def test_subscribe_to_forum(app, authed_client):
    add_permissions(app, 'forums_subscriptions_modify')
    response = authed_client.post('/subscriptions/forums/5')
    check_json_response(response, 'Successfully subscribed to forum 5.')
    assert ForumSubscription.from_attrs(user_id=1, forum_id=5)


def test_subscribe_to_forum_already_subscribed(app, authed_client):
    add_permissions(app, 'forums_subscriptions_modify')
    response = authed_client.post('/subscriptions/forums/2')
    check_json_response(response, 'You are already subscribed to forum 2.')


def test_unsubscribe_from_forum(app, authed_client):
    add_permissions(app, 'forums_subscriptions_modify')
    response = authed_client.delete('/subscriptions/forums/2')
    check_json_response(response, 'Successfully unsubscribed from forum 2.')
    assert not ForumSubscription.from_attrs(user_id=1, forum_id=2)


def test_unsubscribe_from_forum_not_subscribed(app, authed_client):
    add_permissions(app, 'forums_subscriptions_modify')
    response = authed_client.delete('/subscriptions/forums/5')
    check_json_response(response, 'You are not subscribed to forum 5.')


def test_subscribe_to_thread(app, authed_client):
    add_permissions(app, 'forums_subscriptions_modify')
    response = authed_client.post('/subscriptions/threads/5')
    check_json_response(response, 'Successfully subscribed to thread 5.')
    assert ForumThreadSubscription.from_attrs(user_id=1, thread_id=5)


def test_subscribe_to_thread_already_subscribed(app, authed_client):
    add_permissions(app, 'forums_subscriptions_modify')
    response = authed_client.post('/subscriptions/threads/3')
    check_json_response(response, 'You are already subscribed to thread 3.')


def test_unsubscribe_from_thread(app, authed_client):
    add_permissions(app, 'forums_subscriptions_modify')
    response = authed_client.delete('/subscriptions/threads/3')
    check_json_response(response, 'Successfully unsubscribed from thread 3.')
    assert not ForumThreadSubscription.from_attrs(user_id=1, thread_id=3)


def test_unsubscribe_from_thread_not_subscribed(app, authed_client):
    add_permissions(app, 'forums_subscriptions_modify')
    response = authed_client.delete('/subscriptions/threads/5')
    check_json_response(response, 'You are not subscribed to thread 5.')


def test_view_my_subscriptions(app, authed_client):
    add_permissions(app, 'forums_view_subscriptions')
    response = authed_client.get('/subscriptions/forums').get_json()['response']
    assert {1, 2, 4} == {s['id'] for s in response}


def test_view_thread_subscriptions(app, authed_client):
    add_permissions(app, 'forums_view_subscriptions')
    response = authed_client.get('/subscriptions/threads').get_json()['response']
    assert {1, 3, 4} == {s['id'] for s in response}


def test_view_forum_subscriptions_empty(app, authed_client):
    db.engine.execute("DELETE FROM forums_forums_subscriptions")
    add_permissions(app, 'forums_view_subscriptions')
    response = authed_client.get('/subscriptions/forums').get_json()['response']
    assert response == []


def test_view_thread_subscriptions_empty(app, authed_client):
    db.engine.execute("DELETE FROM users_permissions")
    add_permissions(app, 'forums_view_subscriptions')
    response = authed_client.get('/subscriptions/threads').get_json()['response']
    assert response == []


def test_view_forum_subscriptions_no_forum_perms(app, authed_client):
    db.engine.execute("DELETE FROM users_permissions")
    add_permissions(app, 'forums_view_subscriptions')
    response = authed_client.get('/subscriptions/forums').get_json()['response']
    assert response == []


def test_view_thread_subscriptions_no_forum_perms(app, authed_client):
    db.engine.execute("DELETE FROM users_permissions WHERE permission LIKE 'forumaccess%%'")
    add_permissions(app, 'forums_view_subscriptions')
    response = authed_client.get('/subscriptions/threads').get_json()['response']
    assert response == []


def test_subscribe_thread_deletes_cache_keys(app, authed_client):
    add_permissions(app, ForumPermissions.MODIFY_SUBSCRIPTIONS)
    ForumThread.from_subscribed_user(1)
    ForumThreadSubscription.user_ids_from_thread(5)
    response = authed_client.post('/subscriptions/threads/5')
    assert response.status_code == 200
    assert not cache.get(ForumThreadSubscription.__cache_key_users__.format(thread_id=5))
    assert not cache.get(ForumThreadSubscription.__cache_key_of_user__.format(user_id=1))
    assert ForumThreadSubscription.user_ids_from_thread(5) == [1]


def test_unsubscribe_thread_deletes_cache_keys(app, authed_client):
    add_permissions(app, ForumPermissions.MODIFY_SUBSCRIPTIONS)
    ForumThread.from_subscribed_user(1)
    ForumThreadSubscription.user_ids_from_thread(4)
    assert cache.get(ForumThreadSubscription.__cache_key_users__.format(thread_id=4))
    assert cache.get(ForumThreadSubscription.__cache_key_of_user__.format(user_id=1))
    response = authed_client.delete('/subscriptions/threads/4')
    assert response.status_code == 200
    assert not cache.get(ForumThreadSubscription.__cache_key_users__.format(thread_id=4))
    assert not cache.get(ForumThreadSubscription.__cache_key_of_user__.format(user_id=1))
    assert ForumThreadSubscription.user_ids_from_thread(4) == [2]


def test_subscribe_forum_deletes_cache_keys(app, authed_client):
    add_permissions(app, ForumPermissions.MODIFY_SUBSCRIPTIONS)
    Forum.from_subscribed_user(1)
    ForumSubscription.user_ids_from_forum(5)
    response = authed_client.post('/subscriptions/forums/5')
    assert response.status_code == 200
    assert not cache.get(ForumSubscription.__cache_key_users__.format(forum_id=5))
    assert not cache.get(ForumSubscription.__cache_key_of_user__.format(user_id=1))
    assert ForumSubscription.user_ids_from_forum(5) == [1]


def test_unsubscribe_forum_deletes_cache_keys(app, authed_client):
    add_permissions(app, ForumPermissions.MODIFY_SUBSCRIPTIONS)
    Forum.from_subscribed_user(1)
    ForumSubscription.user_ids_from_forum(4)
    assert cache.get(ForumSubscription.__cache_key_users__.format(forum_id=4))
    assert cache.get(ForumSubscription.__cache_key_of_user__.format(user_id=1))
    response = authed_client.delete('/subscriptions/forums/4')
    assert response.status_code == 200
    assert not cache.get(ForumSubscription.__cache_key_users__.format(forum_id=4))
    assert not cache.get(ForumSubscription.__cache_key_of_user__.format(user_id=1))
    assert ForumSubscription.user_ids_from_forum(4) == [2]
